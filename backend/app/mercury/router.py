"""Public owner-scoped query API; no write-capable legacy loop is reachable."""
import asyncio
import json
import time
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session, sessionmaker
from sse_starlette import EventSourceResponse
from app.core.database import get_db
from app.core.identity import get_or_create_owner
from app.mercury.provider import QueryChatClient
from app.mercury.store import CaseStore
from app.mercury.orders import MercuryOrderService
from app.mercury.graph import run_query, log_query_failure
from app.mercury.aftersales import AfterSalesService
from app.mercury import aftersales_graph

router = APIRouter(prefix='/api/v1/mercury', tags=['mercury'])
_running = set()


def _owner(request: Request, response: Response, db: Session = Depends(get_db)) -> str:
    return get_or_create_owner(request, response, db)


def get_query_model():
    return QueryChatClient()


def get_case_store(db: Session = Depends(get_db)):
    return CaseStore(sessionmaker(bind=db.get_bind(), expire_on_commit=False, autoflush=False))


def get_order_service(db: Session = Depends(get_db)):
    return MercuryOrderService(sessionmaker(bind=db.get_bind(), expire_on_commit=False, autoflush=False))


class TurnRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    message: str = Field(min_length=1)
    request_id: str = Field(min_length=1)


class OrderSelection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    order_id: str
    selection_version: int = Field(ge=0)


def owned_case(store, owner_id, session_id):
    case = store.read_case(owner_id, session_id)
    if case is None:
        raise HTTPException(404, '未找到该售后会话')
    return case


@router.get('/orders')
def get_orders(owner_id: str = Depends(_owner), orders=Depends(get_order_service)):
    return {'orders': orders.list_orders(owner_id), 'simulated': True}


@router.post('/sessions')
def create_mercury_session(owner_id: str = Depends(_owner), store=Depends(get_case_store)):
    return store.create_case(owner_id)


@router.get('/sessions/{session_id}')
def get_mercury_session(session_id: str, owner_id: str = Depends(_owner), store=Depends(get_case_store)):
    return owned_case(store, owner_id, session_id)


@router.put('/sessions/{session_id}/order')
def choose_order(session_id: str, request: OrderSelection, owner_id: str = Depends(_owner), store=Depends(get_case_store)):
    owned_case(store, owner_id, session_id)
    result = store.select_order(owner_id, session_id, request.order_id, request.selection_version)
    if result == 'not_found':
        raise HTTPException(404, '未找到该订单')
    if result == 'conflict':
        raise HTTPException(409, '订单选择或会话责任已变化，或查询仍在进行，请刷新后重试')
    return owned_case(store, owner_id, session_id)


def _finished(task):
    _running.discard(task)
    if not task.cancelled() and task.exception() is not None:
        log_query_failure('query execution failed', task.exception())


@router.post('/sessions/{session_id}/turns/stream')
async def mercury_turn_stream(session_id: str, request: TurnRequest, owner_id: str = Depends(_owner),
                              store=Depends(get_case_store), orders=Depends(get_order_service),
                              model=Depends(get_query_model)):
    accepted_at = time.monotonic()
    owned_case(store, owner_id, session_id)
    run_id = store.reserve_query(owner_id, session_id)
    if run_id is None:
        raise HTTPException(409, '该售后会话正在查询或由人工负责，请稍后重试')
    case = owned_case(store, owner_id, session_id)
    task = asyncio.create_task(asyncio.to_thread(run_query, owner_id, case, request.message,
                                                model, accepted_at, run_id, store, orders))
    _running.add(task)
    task.add_done_callback(_finished)

    async def events():
        yield {'event': 'accepted', 'data': json.dumps({'request_id': request.request_id})}
        try:
            state = await asyncio.shield(task)
        except Exception:
            yield {'event': 'error', 'data': json.dumps({'message': '查询暂时失败，请刷新后重试；未提交任何申请。'}, ensure_ascii=False)}
            return
        yield {'event': 'answer.delta', 'data': json.dumps({'text': state['final_text']}, ensure_ascii=False)}
        yield {'event': 'turn.completed', 'data': json.dumps({'session_id': session_id,
               'final_text': state['final_text'], 'status': state['status'], 'action_results': state.get('action_results', [])}, ensure_ascii=False)}

    return EventSourceResponse(events())


class ProposalRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    kind: Literal['refund', 'return']
    item_id: str | None = None
    reason: str = Field(min_length=1, max_length=1000)
    selection_version: int = Field(ge=0)


class ConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    proposal_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=160)
    confirmed: Literal[True]


def get_aftersales_service(db: Session = Depends(get_db)):
    return AfterSalesService(sessionmaker(bind=db.get_bind(), expire_on_commit=False, autoflush=False))


@router.get('/sessions/{session_id}/aftersales')
def read_aftersales(session_id: str, owner_id: str = Depends(_owner), service=Depends(get_aftersales_service)):
    return service.read(owner_id, session_id)


@router.post('/sessions/{session_id}/proposals')
def propose_aftersales(session_id: str, request: ProposalRequest, owner_id: str = Depends(_owner), service=Depends(get_aftersales_service)):
    return aftersales_graph.propose(service, owner_id, session_id, request.model_dump())


@router.post('/sessions/{session_id}/confirm')
def confirm_aftersales(session_id: str, request: ConfirmationRequest, owner_id: str = Depends(_owner), service=Depends(get_aftersales_service)):
    return aftersales_graph.confirm(service, owner_id, session_id, request.proposal_id, request.idempotency_key)

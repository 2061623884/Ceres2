"""Public owner-scoped query API; no write-capable legacy loop is reachable."""
import asyncio
import hashlib
import json
import time
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from sqlalchemy.orm import Session, sessionmaker
from sse_starlette import EventSourceResponse
from app.core.database import get_db
from app.core.identity import get_or_create_owner
from app.core.errors import AppError
from app.models.guide import GuideCommandReceipt
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
    routing_request_id: str | None = None


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
                              model=Depends(get_query_model), db: Session = Depends(get_db)):
    accepted_at = time.monotonic()
    owned_case(store, owner_id, session_id)
    from app.services.navigation_service import authorize_text, canonical_for_owner, consume_handoff
    guide = canonical_for_owner(db, owner_id)
    case = owned_case(store, owner_id, session_id)
    body = {**request.model_dump(), '_role_session_id': session_id,
            '_selected_object': {'kind':'order', 'id':case['order_id']} if case['order_id'] else None}
    route = authorize_text(db, owner_id, guide.session_id, 'momo', body)
    selected = route.get('selected_object')
    if selected and selected['kind'] == 'order' and selected['id'] != case['order_id']:
        raise AppError(409, 'ORDER_SELECTION_CHANGED', '请先选择原请求中的订单，再继续查询')
    key = (guide.session_id, 'momo:' + request.request_id)
    digest = hashlib.sha256(json.dumps({'case':session_id, 'message':request.message}, sort_keys=True).encode()).hexdigest()
    prior = db.get(GuideCommandReceipt, key)
    if prior:
        if prior.digest != digest:
            raise AppError(409, 'IDEMPOTENCY_CONFLICT', '同一请求不能切换到其他售后会话或文字')
        result = json.loads(prior.result_json)
        if result['status'] == 'running' and time.time() - result['started_at'] >= 30:
            result = {'status':'failed', 'message':'原查询已中断，请重新说明需求；不会自动重做。'}
            prior.result_json = json.dumps(result, ensure_ascii=False)
            db.commit()
        if result['status'] == 'running':
            raise AppError(409, 'QUERY_PENDING', '原查询仍在处理，请稍后刷新；不会重复执行')
        async def replay():
            if result['status'] == 'failed':
                yield {'event':'error', 'data':json.dumps({'message':result['message']}, ensure_ascii=False)}
            else:
                yield {'event':'turn.completed', 'data':json.dumps(result['result'], ensure_ascii=False)}
        return EventSourceResponse(replay())
    db.rollback()
    run_id = store.reserve_query(owner_id, session_id)
    if run_id is None:
        raise HTTPException(409, '该售后会话正在查询或由人工负责，请稍后重试')
    try:
        # Case reservation is a separate canonical transaction. Recheck the
        # stored decision and exact order after that gap, without another Kev.
        route = authorize_text(db, owner_id, guide.session_id, 'momo', body)
        case = owned_case(store, owner_id, session_id)
        selected = route.get('selected_object')
        if selected and selected['kind'] == 'order' and selected['id'] != case['order_id']:
            raise AppError(409, 'ORDER_SELECTION_CHANGED', '原请求的订单已变化，请重新选择后继续')
        db.add(GuideCommandReceipt(session_id=key[0], request_id=key[1], digest=digest,
                                   result_json=json.dumps({'status':'running', 'started_at':time.time()})))
        db.commit()
        consume_handoff(db, owner_id, guide.session_id, request.request_id)
    except Exception:
        db.rollback()
        store.release_query(owner_id, session_id, run_id)
        raise
    factory = sessionmaker(bind=db.get_bind(), expire_on_commit=False)
    def execute_once():
        try:
            state = run_query(owner_id, case, request.message, model, accepted_at, run_id, store, orders)
            result = {'session_id':session_id, 'final_text':state['final_text'], 'status':state['status'], 'action_results':state.get('action_results', [])}
            saved = {'status':'completed', 'result':result}
        except Exception:
            with factory() as receipt_db:
                row = receipt_db.get(GuideCommandReceipt, key)
                row.result_json = json.dumps({'status':'failed', 'message':'原查询失败，请重新说明需求；未提交任何申请。'}, ensure_ascii=False)
                receipt_db.commit()
            raise
        with factory() as receipt_db:
            row = receipt_db.get(GuideCommandReceipt, key)
            row.result_json = json.dumps(saved, ensure_ascii=False)
            receipt_db.commit()
        return state
    task = asyncio.create_task(asyncio.to_thread(execute_once))
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
    kind: Literal['refund', 'return', 'quality', 'fulfillment']
    item_id: str | None = None
    reason: str = Field(min_length=1, max_length=1000)
    selection_version: int = Field(ge=0)
    problem_quantity: StrictInt | None = Field(default=None, ge=1)
    photo_ids: list[str] = Field(default_factory=list, max_length=3)


class PhotoUpload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    content_type: Literal['image/jpeg', 'image/png', 'image/webp']
    data_base64: str = Field(min_length=1, max_length=5592408)
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


@router.post('/sessions/{session_id}/photos')
def upload_photo(session_id: str, request: PhotoUpload, owner_id: str = Depends(_owner), service=Depends(get_aftersales_service)):
    return service.upload_photo(owner_id, session_id, request.model_dump())


@router.get('/sessions/{session_id}/photos/{photo_id}')
def read_photo(session_id: str, photo_id: str, owner_id: str = Depends(_owner), service=Depends(get_aftersales_service)):
    from fastapi.responses import Response
    content, content_type = service.read_photo(owner_id, session_id, photo_id)
    return Response(content, media_type=content_type, headers={'X-Content-Type-Options':'nosniff'})


@router.post('/sessions/{session_id}/proposals')
def propose_aftersales(session_id: str, request: ProposalRequest, owner_id: str = Depends(_owner), service=Depends(get_aftersales_service)):
    return aftersales_graph.propose(service, owner_id, session_id, request.model_dump())


@router.post('/sessions/{session_id}/confirm')
def confirm_aftersales(session_id: str, request: ConfirmationRequest, owner_id: str = Depends(_owner), service=Depends(get_aftersales_service)):
    return aftersales_graph.confirm(service, owner_id, session_id, request.proposal_id, request.idempotency_key)


class ReceiptIntroduction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_id: str = Field(min_length=1, max_length=150)


@router.post('/sessions/{session_id}/result-introductions', status_code=202)
def introduce_receipt(session_id: str, body: ReceiptIntroduction, owner_id: str = Depends(_owner), db: Session = Depends(get_db)):
    from app.mercury.aftersales_models import AfterSalesReceipt
    from app.services.navigation_service import canonical_for_owner
    from app.services.result_introduction_service import start_introduction
    receipt = db.get(AfterSalesReceipt, body.source_id)
    if receipt is None or receipt.owner_id != owner_id or receipt.case_id != session_id:
        raise AppError(404, 'RESULT_NOT_FOUND', '没有找到这个售后会话的申请回执')
    guide = canonical_for_owner(db, owner_id)
    return start_introduction(db, owner_id, guide.session_id, {'source_kind':'aftersales_receipt','source_id':body.source_id})

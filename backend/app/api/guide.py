"""Minimal guide HTTP/SSE adapter; Python owns identity, facts and receipts."""
from __future__ import annotations
import json
import time
from typing import Literal
from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker
from app.core.database import get_db
from app.core.errors import AppError
from app.core.identity import get_or_create_owner
from app.models.guide import GuideSession, GuideTask, GuideMessage, GuideTurnReceipt
from app.services.pi_product_turn_service import PiProductTurnService, owned_session, session_anchor
from app.services.guide_lifecycle_service import canonical_entry, task_projection, transition, require_canonical_session
from app.services.guide_run_service import admit, owned_run, run_events, run_projection, record_progress, append_event, start_worker, log_host_failure, run_cancelled, TERMINAL

router = APIRouter(prefix='/api/v1/guide', tags=['guide'])


class EntryContext(BaseModel):
    model_config = ConfigDict(extra='allow')
    page: str
    store_id: str
    delivery_zone_id: str


class CreateSession(BaseModel):
    entry_context: EntryContext


class DisplayedPlan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    task_id: str
    plan_id: str
    plan_version: int = Field(ge=1)
    state_version: int = Field(ge=0)
    session_version: int = Field(ge=0)


class TurnRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=8000)
    expected_task_id: str | None = None
    expected_state_version: int = Field(default=0, ge=0)
    expected_session_version: int = Field(default=0, ge=0)
    view_context: dict | None = None
    displayed_plan: DisplayedPlan | None = None
    displayed_candidate_refs: list[str] = Field(default_factory=list)


class StopRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=100)


class SupplyRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=100)
    store_id: str
    delivery_zone_id: str
    expected_session_version: int = Field(ge=0)


def messages(db, session_id, owner_id, after_sequence=0, limit=None):
    rows = db.scalars(select(GuideMessage).where(GuideMessage.session_id == session_id, GuideMessage.owner_id == owner_id, GuideMessage.sequence > after_sequence).order_by(GuideMessage.sequence).limit(limit)).all()
    return [{key: getattr(row, key) for key in ('message_id', 'session_id', 'task_id', 'sequence', 'role', 'kind', 'content', 'request_id')} for row in rows]


def projection(db, session, include_messages=False, view_context=None):
    anchor = session_anchor(db, session)
    task = db.get(GuideTask, anchor[1]) if anchor[1] else None
    result = {'session_id': session.session_id, 'task_id': anchor[1], 'state_version': anchor[2], 'session_version': anchor[0], 'entry_context': json.loads(session.entry_context_json), 'current_step': task.current_step if task else 'understanding', 'task_status': task.status if task else None, 'plan': json.loads(task.plan_json) if task and task.plan_json else None, 'product_cards': [], 'available_actions': ['send_message'], 'pending_clarifications': []}
    from app.services.pi_product_turn_service import bounded_dialogue_context
    pending = bounded_dialogue_context(db, session.owner_id, session.session_id, anchor)['pending_clarification']
    result['pending_clarifications'] = [pending] if pending else []
    result.update(task_projection(db, session))
    from app.services.comparison_service import ComparisonService
    result['product_cards'] = ComparisonService(db, session.owner_id).current(session.session_id, view_context)
    if result['plan']:
        from app.services.purchase_service import plan_actions
        result['available_actions'] = plan_actions(result['plan'])
        result['confirmation_result'] = result['plan'].get('confirmation_result')
    if include_messages:
        result['messages'] = messages(db, session.session_id, session.owner_id)
    return result


@router.post('/sessions')
def create_session(body: CreateSession, request: Request, response: Response, db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    context = body.entry_context.model_dump()
    session = canonical_entry(db, owner_id, context)
    return projection(db, session, True, context)


@router.get('/sessions/{session_id}')
def read_session(session_id: str, request: Request, response: Response, include_messages: bool = False, db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    return projection(db, owned_session(db, owner_id, session_id), include_messages)


@router.get('/sessions/{session_id}/messages')
def read_messages(session_id: str, request: Request, response: Response, after_sequence: int = Query(default=0, ge=0), limit: int = Query(default=200, ge=1, le=200), db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    owned_session(db, owner_id, session_id)
    return {'messages': messages(db, session_id, owner_id, after_sequence, limit)}


@router.post('/sessions/{session_id}/supply-context')
def change_supply(session_id: str, body: SupplyRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    session = owned_session(db, owner_id, session_id)
    require_canonical_session(db, owner_id, session_id)
    context = json.loads(session.entry_context_json)
    context.update(store_id=body.store_id, delivery_zone_id=body.delivery_zone_id)
    changed = db.execute(update(GuideSession).where(GuideSession.session_id == session_id, GuideSession.owner_id == owner_id, GuideSession.session_version == body.expected_session_version).values(session_version=GuideSession.session_version + 1, supply_store_id=body.store_id, delivery_zone_id=body.delivery_zone_id, entry_context_json=json.dumps(context)))
    if changed.rowcount != 1:
        db.rollback()
        raise AppError(409, 'STALE_STATE', '会话版本已变化')
    db.commit()
    db.expire_all()
    return projection(db, db.get(GuideSession, session_id))


@router.post('/sessions/{session_id}/turns/stop')
def stop_turn(session_id: str, body: StopRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    owned_session(db, owner_id, session_id)
    stopped = db.execute(update(GuideTurnReceipt).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.owner_id == owner_id, GuideTurnReceipt.request_id == body.request_id, GuideTurnReceipt.status == 'running').values(status='stop_requested'))
    db.commit()
    db.expire_all()
    receipt = db.scalar(select(GuideTurnReceipt).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.owner_id == owner_id, GuideTurnReceipt.request_id == body.request_id))
    return {'request_id': body.request_id, 'cancelled': stopped.rowcount == 1, 'status': receipt.status if receipt else None, 'result': json.loads(receipt.result_json) if receipt and receipt.result_json else None}


@router.get('/sessions/{session_id}/turns/{request_id}')
def read_receipt(session_id: str, request_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    owned_session(db, owner_id, session_id)
    receipt = db.scalar(select(GuideTurnReceipt).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.owner_id == owner_id, GuideTurnReceipt.request_id == request_id))
    if receipt is None:
        raise AppError(404, 'TURN_NOT_FOUND', '请求不存在')
    return {'run_id': receipt.run_id, 'status': receipt.status, 'result': json.loads(receipt.result_json) if receipt.result_json else None}


def launch_run(factory, owner_id, session_id, body, run_id, deadline):
    def work():
        with factory() as worker_db:
            try:
                PiProductTurnService(worker_db, owner_id).process(session_id, body, run_id=run_id, deadline=deadline, progress=lambda phase: record_progress(worker_db, run_id, phase))
            except Exception as exc:
                worker_db.rollback()
                if run_cancelled(run_id):
                    return
                receipt = worker_db.get(GuideTurnReceipt, run_id)
                if receipt.status not in TERMINAL:
                    if not isinstance(exc, AppError):
                        log_host_failure(run_id, exc)
                    error = exc.detail['error'] if isinstance(exc, AppError) else {'code': 'PI_QUERY_FAILED', 'message': 'Pi 查询失败', 'retryable': False}
                    receipt.status = 'failed'
                    receipt.result_json = json.dumps(error)
                    append_event(worker_db, receipt, 'error', error)
                    worker_db.commit()
    start_worker(factory.kw['bind'], run_id, deadline, work)


def event_stream(factory, owner_id, session_id, run_id, after_sequence=0):
    def stream():
        sequence = after_sequence
        while True:
            with factory() as db:
                receipt = owned_run(db, owner_id, session_id, run_id)
                events = run_events(db, receipt, sequence)
                terminal = receipt.status in TERMINAL
            for event in events:
                sequence = event['sequence']
                yield 'data: ' + json.dumps(event, ensure_ascii=False) + '\n\n'
            if terminal:
                return
            time.sleep(0.03)
    return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


def accept_run(db, owner_id, session_id, body, deadline):
    factory = sessionmaker(bind=db.get_bind(), autoflush=False, expire_on_commit=False)
    receipt, is_new = admit(db, owner_id, session_id, body)
    run_id = receipt.run_id
    db.rollback()
    if is_new:
        launch_run(factory, owner_id, session_id, body, run_id, deadline)
    return run_id, factory


@router.post('/sessions/{session_id}/runs', status_code=202)
def start_run(session_id: str, body: TurnRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    deadline = time.monotonic() + 30.0
    owner_id = get_or_create_owner(request, response, db)
    run_id, _factory = accept_run(db, owner_id, session_id, body.model_dump(), deadline)
    return {'run_id': run_id, 'request_id': body.request_id}


@router.post('/sessions/{session_id}/turns/stream')
def stream_turn(session_id: str, body: TurnRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    deadline = time.monotonic() + 30.0
    owner_id = get_or_create_owner(request, response, db)
    owned_session(db, owner_id, session_id)
    try:
        run_id, factory = accept_run(db, owner_id, session_id, body.model_dump(), deadline)
    except AppError as exc:
        # Existing P01 clients receive admission conflicts in their SSE contract.
        event = {'protocol_version': 1, 'run_id': None, 'sequence': 1, 'type': 'error', 'session_id': session_id, 'target_task_id': body.expected_task_id, 'payload': exc.detail['error']}
        return StreamingResponse(iter(['data: ' + json.dumps(event, ensure_ascii=False) + '\n\n']), media_type='text/event-stream')
    return event_stream(factory, owner_id, session_id, run_id)


@router.get('/sessions/{session_id}/runs/{run_id}/events')
def read_events(session_id: str, run_id: str, request: Request, response: Response, after_sequence: int = Query(default=0, ge=0), db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    receipt = owned_run(db, owner_id, session_id, run_id)
    return {'events': run_events(db, receipt, after_sequence), 'status': receipt.status}


@router.get('/sessions/{session_id}/runs/{run_id}/stream')
def reconnect_run(session_id: str, run_id: str, request: Request, response: Response, after_sequence: int = Query(default=0, ge=0), db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    owned_run(db, owner_id, session_id, run_id)
    factory = sessionmaker(bind=db.get_bind(), autoflush=False, expire_on_commit=False)
    db.rollback()
    return event_stream(factory, owner_id, session_id, run_id, after_sequence)


@router.get('/sessions/{session_id}/status')
def read_status(session_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    session = owned_session(db, owner_id, session_id)
    runs = db.scalars(select(GuideTurnReceipt).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.owner_id == owner_id).order_by(GuideTurnReceipt.started_at.desc())).all()
    return {**projection(db, session), 'runs': [run_projection(row) for row in runs]}


class TaskCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(min_length=1, max_length=100)
    kind: Literal['new_goal', 'amend', 'continue', 'abandon']
    goal: str | None = Field(default=None, max_length=8000)
    conditions: dict | None = None
    expected_task_id: str | None = None
    expected_state_version: int = Field(ge=0)
    expected_session_version: int = Field(ge=0)


@router.post('/sessions/{session_id}/tasks/current')
def change_task(session_id: str, body: TaskCommand, request: Request, response: Response, db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    return transition(db, owner_id, session_id, body.model_dump())


@router.get('/sessions/{session_id}/tasks')
def list_tasks(session_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    owner_id = get_or_create_owner(request, response, db)
    owned_session(db, owner_id, session_id)
    rows = db.scalars(select(GuideTask).where(GuideTask.session_id == session_id, GuideTask.owner_id == owner_id).order_by(GuideTask.task_id)).all()
    return {'tasks': [{'task_id': row.task_id, 'status': row.status, 'state_version': row.state_version, 'goal': row.goal, 'conditions': json.loads(row.conditions_json)} for row in rows]}


class ConfirmItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sku_id: str
    quantity: int = Field(gt=0, strict=True)


class ConfirmPlan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    plan_id: str
    plan_version: int = Field(ge=1)
    expected_state_version: int = Field(ge=0)
    expected_session_version: int = Field(ge=0)
    selected_items: list[ConfirmItem] = Field(min_length=1)


@router.post('/tasks/{task_id}/confirm')
def confirm_plan(task_id: str, body: ConfirmPlan, request: Request, response: Response, idempotency_key: str = Header(min_length=1, max_length=150), db: Session = Depends(get_db)):
    from app.services.purchase_service import PurchaseService
    owner_id = get_or_create_owner(request, response, db)
    try:
        result = PurchaseService(db, owner_id).confirm(task_id, body.model_dump(), idempotency_key)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


class RevisionItem(ConfirmItem):
    selected: bool


class RevisePlan(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(min_length=1, max_length=100)
    base_plan_id: str
    base_plan_version: int = Field(ge=1)
    expected_state_version: int = Field(ge=0)
    expected_session_version: int = Field(ge=0)
    coverage_intent: Literal['selection_only', 'dish_update', 'group_update', 'group_remove', 'choose_partial', 'choose_alternative', 'accept_quote']
    items: list[RevisionItem]
    people: int | None = Field(default=None, gt=0, strict=True)
    selections: dict[str, str] = Field(default_factory=dict)
    group_id: str | None = None
    gap_id: str | None = None
    alternative_index: int | None = Field(default=None, ge=0, strict=True)


@router.post('/tasks/{task_id}/plan-revisions')
def revise_plan(task_id: str, body: RevisePlan, request: Request, response: Response, db: Session = Depends(get_db)):
    from app.services.purchase_service import PurchaseService
    owner_id = get_or_create_owner(request, response, db)
    try:
        result = PurchaseService(db, owner_id).revise(task_id, body.model_dump())
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise



@router.post('/tasks/{task_id}/items/{sku_id}/add')
def add_plan_item(task_id: str, sku_id: str, body: ConfirmPlan, request: Request, response: Response, idempotency_key: str = Header(min_length=1, max_length=150), db: Session = Depends(get_db)):
    from app.services.purchase_service import PurchaseService
    owner_id = get_or_create_owner(request, response, db)
    try:
        result = PurchaseService(db, owner_id).confirm(task_id, body.model_dump(), idempotency_key, row_sku=sku_id)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


class RepurchaseRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(min_length=1, max_length=100)
    source_task_id: str
    expected_task_id: str | None = None
    expected_state_version: int = Field(ge=0)
    expected_session_version: int = Field(ge=0)


@router.get('/sessions/{session_id}/history')
def historical_sources(session_id: str, request: Request, response: Response, db: Session = Depends(get_db)):
    from app.services.history_service import HistoryService
    owner_id = get_or_create_owner(request, response, db)
    return {'sources':HistoryService(db, owner_id).sources(session_id)}


@router.post('/sessions/{session_id}/history/repurchase')
def repurchase_history(session_id: str, body: RepurchaseRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    from app.services.history_service import HistoryService
    owner_id = get_or_create_owner(request, response, db)
    try:
        result = HistoryService(db, owner_id).select(session_id, body.model_dump())
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


class ReminderDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    task_id: str
    decision: Literal['ignore', 'decline']


@router.post('/sessions/{session_id}/history/reminder')
def dismiss_history_reminder(session_id: str, body: ReminderDecision, request: Request, response: Response, db: Session = Depends(get_db)):
    from app.services.history_service import HistoryService
    owner_id = get_or_create_owner(request, response, db)
    HistoryService(db, owner_id).dismiss_reminder(session_id, body.task_id, body.decision)
    db.commit()
    return projection(db, owned_session(db, owner_id, session_id))

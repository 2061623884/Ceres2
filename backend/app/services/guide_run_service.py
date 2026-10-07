"""Durable bounded run admission and event journal, independent of SSE transport."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import time
import threading
import logging
import traceback
from uuid import uuid4
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.core.errors import AppError
from app.models.guide import GuideSession, GuideTurnReceipt, GuideRunEvent
from app.services.pi_product_turn_service import owned_session, session_anchor

# This deployment is one Linux host using its local SQLite store. A process
# incarnation includes the kernel boot and process start tick, not just a PID.
BOOT_ID = Path('/proc/sys/kernel/random/boot_id').read_text().strip()

def process_incarnation(pid):
    stat = Path(f'/proc/{pid}/stat').read_text()
    return f'{BOOT_ID}:{pid}:{stat[stat.rindex(")") + 2:].split()[19]}'

EXECUTION_ID = process_incarnation(os.getpid())
TERMINAL = {'completed', 'waiting_clarification', 'waiting_confirmation', 'protected', 'stopped', 'failed', 'interrupted'}


_RUNNERS = {}
_CLOSING = set()
_PENDING_INTERRUPTION = {}
_RUNNER_LOCK = threading.Lock()


def open_run_lifecycle(bind):
    with _RUNNER_LOCK:
        pending = tuple(_PENDING_INTERRUPTION.get(bind, ()))
    # On same-process app reopening, persist shutdown cancellation that a
    # contending SQLite writer prevented. Actual process restart uses the
    # process-incarnation recovery below. Neither path reruns the model.
    if pending:
        with Session(bind) as db:
            for run_id in pending:
                interrupt_run(db, run_id)
            db.commit()
    with _RUNNER_LOCK:
        _PENDING_INTERRUPTION.pop(bind, None)
        _CLOSING.discard(bind)


def run_cancelled(run_id):
    with _RUNNER_LOCK:
        runner = _RUNNERS.get(run_id)
        return runner is not None and runner[3].is_set()


def start_worker(bind, run_id, deadline, work):
    def execute():
        try:
            work()
        finally:
            with _RUNNER_LOCK:
                _RUNNERS.pop(run_id, None)
    with _RUNNER_LOCK:
        closing = bind in _CLOSING
        if not closing:
            thread = threading.Thread(target=execute, name=f'guide-{run_id}', daemon=False)
            _RUNNERS[run_id] = (bind, thread, deadline, threading.Event())
            thread.start()
    if closing:
        # No SQL or waiting while holding the runner registry lock.
        persist_interruption(bind, [run_id], deadline)
        raise AppError(503, 'GUIDE_SHUTTING_DOWN', '服务正在关闭，请稍后继续')


def interrupt_run(db, run_id):
    changed = db.execute(update(GuideTurnReceipt).where(GuideTurnReceipt.run_id == run_id, GuideTurnReceipt.execution_id == EXECUTION_ID, GuideTurnReceipt.status.in_(['running', 'stop_requested'])).values(status='interrupted'))
    if changed.rowcount:
        receipt = db.get(GuideTurnReceipt, run_id)
        error = {'code': 'RUN_INTERRUPTED', 'message': '服务关闭，这次处理未完成，已有结果仍保留。请决定是否继续。', 'http_status': 409}
        receipt.result_json = json.dumps(error, ensure_ascii=False)
        append_event(db, receipt, 'error', error)


def persist_interruption(bind, run_ids, deadline):
    with _RUNNER_LOCK:
        _PENDING_INTERRUPTION.setdefault(bind, set()).update(run_ids)
    # Only this local cleanup connection changes busy_timeout. It stays checked
    # out until its original setting is restored, so the pool cannot leak it.
    with bind.connect() as connection:
        previous_timeout = connection.exec_driver_sql('PRAGMA busy_timeout').scalar_one()
        connection.commit()
        timeout_ms = min(250, max(0, int((deadline - time.monotonic()) * 1000)))
        connection.exec_driver_sql(f'PRAGMA busy_timeout={timeout_ms}')
        connection.commit()
        try:
            with Session(bind=connection) as db:
                for run_id in run_ids:
                    interrupt_run(db, run_id)
                db.commit()
        except OperationalError as exc:
            if getattr(exc.orig, 'sqlite_errorname', '') not in ('SQLITE_BUSY', 'SQLITE_LOCKED'):
                raise
            logging.getLogger(__name__).warning('Guide shutdown persistence deferred: SQLite writer busy; recovery required')
            return
        finally:
            connection.rollback()
            connection.exec_driver_sql(f'PRAGMA busy_timeout={previous_timeout}')
            connection.commit()
    with _RUNNER_LOCK:
        _PENDING_INTERRUPTION[bind].difference_update(run_ids)


def shutdown_runs(bind):
    with _RUNNER_LOCK:
        _CLOSING.add(bind)
        owned = [(run_id, thread, deadline) for run_id, (engine, thread, deadline, cancelled) in _RUNNERS.items() if engine is bind]
        for run_id, _thread, _deadline in owned:
            _RUNNERS[run_id][3].set()
    if not owned:
        return
    try:
        persist_interruption(bind, [run_id for run_id, _thread, _deadline in owned], max(deadline for _run_id, _thread, deadline in owned))
    finally:
        # Cancellation never waits for SQL. A DB call already blocked can
        # outlive this bounded join, remains tracked, and is fenced again before
        # publication. No claim that arbitrary SQLite shutdown finishes in 15s.
        for _run_id, thread, deadline in owned:
            thread.join(timeout=max(0, deadline - time.monotonic()) + 0.25)


def digest_body(body):
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def append_event(db, receipt, kind, payload):
    # Callers either hold the session/receipt write lock or own this sole runner.
    sequence = (db.scalar(select(func.max(GuideRunEvent.sequence)).where(GuideRunEvent.run_id == receipt.run_id)) or 0) + 1
    db.add(GuideRunEvent(run_id=receipt.run_id, sequence=sequence, type=kind,
        payload_json=json.dumps(payload, ensure_ascii=False), recorded_at_ms=time.time()*1000))
    db.flush()


def event_projection(receipt, row):
    elapsed_ms = row.recorded_at_ms-receipt.started_at*1000 if row.recorded_at_ms is not None and receipt.started_at is not None else None
    return {'protocol_version': 1, 'run_id': receipt.run_id, 'sequence': row.sequence, 'type': row.type,
        'recorded_at_ms':row.recorded_at_ms, 'elapsed_ms':elapsed_ms, 'session_id': receipt.session_id,
        'target_task_id': json.loads(receipt.anchor_json).get('task_id'), 'payload': json.loads(row.payload_json)}


def run_projection(receipt):
    return {'run_id': receipt.run_id, 'request_id': receipt.request_id, 'status': receipt.status, 'input': json.loads(receipt.input_json), 'anchor': json.loads(receipt.anchor_json), 'result': json.loads(receipt.result_json) if receipt.result_json else None}


def owned_run(db, owner_id, session_id, run_id):
    owned_session(db, owner_id, session_id)
    receipt = db.get(GuideTurnReceipt, run_id)
    if receipt is None or receipt.owner_id != owner_id or receipt.session_id != session_id:
        raise AppError(404, 'RUN_NOT_FOUND', '运行不存在')
    return receipt


def run_events(db, receipt, after_sequence=0):
    rows = db.scalars(select(GuideRunEvent).where(GuideRunEvent.run_id == receipt.run_id, GuideRunEvent.sequence > after_sequence).order_by(GuideRunEvent.sequence)).all()
    return [event_projection(receipt, row) for row in rows]


def admit(db, owner_id, session_id, body):
    with _RUNNER_LOCK:
        if db.get_bind() in _CLOSING:
            raise AppError(503, 'GUIDE_SHUTTING_DOWN', '服务正在关闭，请稍后继续')
    owned_session(db, owner_id, session_id)
    from app.services.guide_lifecycle_service import require_canonical_session
    require_canonical_session(db, owner_id, session_id)
    digest = digest_body(body)
    # Receipt registration precedes worker launch, so accepted/stop cannot race
    # an absent reservation. The same lock protects body replay and task anchor.
    db.execute(update(GuideSession).where(GuideSession.session_id == session_id, GuideSession.owner_id == owner_id).values(session_version=GuideSession.session_version))
    db.expire_all()
    receipt = db.scalar(select(GuideTurnReceipt).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.request_id == body['request_id']))
    if receipt:
        if receipt.owner_id != owner_id or receipt.digest != digest:
            db.rollback()
            raise AppError(409, 'IDEMPOTENCY_CONFLICT', '同一请求标识对应不同内容')
        db.commit()
        return receipt, False
    session = owned_session(db, owner_id, session_id)
    anchor = session_anchor(db, session)
    if anchor != (body['expected_session_version'], body['expected_task_id'], body['expected_state_version']):
        db.rollback()
        raise AppError(409, 'STALE_STATE', '会话或任务版本已变化')
    from app.services.history_service import HistoryService
    HistoryService(db, owner_id).dismiss_reminder(session_id, anchor[1], 'ignored')
    receipt = GuideTurnReceipt(run_id=f'run-{uuid4().hex}', owner_id=owner_id, session_id=session_id, request_id=body['request_id'], digest=digest, input_json=json.dumps(body, ensure_ascii=False), anchor_json=json.dumps({'session_version': anchor[0], 'task_id': anchor[1], 'state_version': anchor[2]}), execution_id=EXECUTION_ID, started_at=time.time())
    db.add(receipt)
    db.flush()
    append_event(db, receipt, 'accepted', {'request_id': body['request_id']})
    db.commit()
    return receipt, True


def record_progress(db, run_id, phase):
    if run_cancelled(run_id):
        return
    receipt = db.get(GuideTurnReceipt, run_id)
    if receipt.status not in TERMINAL:
        append_event(db, receipt, 'progress', {'phase': phase})
        db.commit()


def publish_result(db, receipt, result):
    append_event(db, receipt, 'progress', {'phase': 'speaking'})
    for message in result['messages']:
        text = message['content']
        # Only validated, committed-safe text is exposed; no raw SDK tokens.
        for offset in range(0, len(text), 24):
            append_event(db, receipt, 'answer.delta', {'delta': text[offset:offset + 24], 'replace': offset == 0, 'final': offset + 24 >= len(text), 'message_id': message['message_id'], 'answer_kind': result['answer_kind']})
    append_event(db, receipt, 'turn.stopped' if result['runtime_status'] == 'stopped' else 'turn.completed', result)


def recover_interrupted_runs(bind):
    with Session(bind) as db:
        receipts = db.scalars(select(GuideTurnReceipt).where(GuideTurnReceipt.status.in_(['running', 'stop_requested']))).all()
        for receipt in receipts:
            incarnation = receipt.execution_id
            if incarnation:
                parts = incarnation.split(':')
                if len(parts) != 3:
                    continue  # Unknown provenance cannot prove a former process.
                if parts[0] == BOOT_ID:
                    try:
                        if process_incarnation(int(parts[1])) == incarnation:
                            continue
                    except FileNotFoundError:
                        pass  # Known local process no longer exists.
            # Legacy runs have no executor to resume; terminal receipts above
            # are never rewritten. Recovery is an honest failure, not a retry.
            changed = db.execute(update(GuideTurnReceipt).where(GuideTurnReceipt.run_id == receipt.run_id, GuideTurnReceipt.status.in_(['running', 'stop_requested'])).values(status='interrupted'))
            if changed.rowcount:
                error = {'code': 'RUN_INTERRUPTED', 'message': '服务重启中断了这次处理，已有结果仍保留。请决定是否继续。', 'http_status': 409}
                receipt.result_json = json.dumps(error, ensure_ascii=False)
                append_event(db, receipt, 'error', error)
        db.commit()

def safe_failure_diagnostic(error):
    chain = []
    current = error
    while current is not None:
        kind = type(current).__name__ if type(current).__name__ in ('RuntimeError', 'TypeError', 'ValueError', 'OSError', 'IntegrityError', 'OperationalError') else 'Error'
        chain.append({'kind': kind, 'fingerprint': hashlib.sha256(str(current).encode()).hexdigest(), 'frames': [{'file': Path(frame.filename).name, 'line': frame.lineno, 'function': frame.name} for frame in traceback.extract_tb(current.__traceback__)]})
        current = current.__cause__ if current.__cause__ is not None else current.__context__
    return chain



def log_host_failure(run_id, error):
    logging.getLogger(__name__).error('Pi host failure run_id=%s causes=%s', run_id, safe_failure_diagnostic(error))

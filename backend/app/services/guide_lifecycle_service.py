"""Small, owner-scoped task transitions. No cart or order mutation lives here."""
from __future__ import annotations
import hashlib
import json
from uuid import uuid4
from sqlalchemy import select, update
from app.core.errors import AppError
from app.models.identity import Owner
from app.models.guide import GuideEntry, GuideSession, GuideTask, GuideCommandReceipt
from app.services.pi_product_turn_service import owned_session, session_anchor


def canonical_entry(db, owner_id, context):
    # Serializes entry admission across tabs/processes without altering identity.
    db.execute(update(Owner).where(Owner.id == owner_id).values(id=Owner.id))
    entry = db.get(GuideEntry, owner_id)
    if entry:
        session = owned_session(db, owner_id, entry.session_id)
    else:
        session = db.scalar(select(GuideSession).where(GuideSession.owner_id == owner_id).order_by(GuideSession.session_id).limit(1))
        if session is None:
            session = GuideSession(session_id=f'session-{uuid4().hex}', owner_id=owner_id, entry_context_json=json.dumps(context), supply_store_id=context['store_id'], delivery_zone_id=context['delivery_zone_id'])
            db.add(session)
            db.flush()
        db.add(GuideEntry(owner_id=owner_id, session_id=session.session_id))
    db.commit()
    return session


def require_canonical_session(db, owner_id, session_id):
    entry = db.get(GuideEntry, owner_id)
    canonical = entry.session_id if entry else db.scalar(select(GuideSession.session_id).where(GuideSession.owner_id == owner_id).order_by(GuideSession.session_id).limit(1))
    if canonical != session_id:
        raise AppError(409, 'LEGACY_SESSION_READ_ONLY', '历史会话仅供查看，请回到当前导购入口继续')


def task_projection(db, session):
    anchor = session_anchor(db, session)
    task = db.get(GuideTask, anchor[1]) if anchor[1] else None
    conditions = json.loads(task.conditions_json) if task else {}
    reminder = conditions.get('history_reminder')
    return {'history_reminder':reminder if reminder and reminder['decision'] == 'offered' else None, 'session_id': session.session_id, 'task_id': anchor[1], 'state_version': anchor[2], 'session_version': anchor[0], 'task_status': task.status if task else None, 'goal': task.goal if task else None, 'conditions': json.loads(task.conditions_json) if task else {}}


def transition(db, owner_id, session_id, body, *, commit=True):
    owned_session(db, owner_id, session_id)
    require_canonical_session(db, owner_id, session_id)
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    # The session row is the single-task and command-receipt serialization seam.
    db.execute(update(GuideSession).where(GuideSession.session_id == session_id, GuideSession.owner_id == owner_id).values(session_version=GuideSession.session_version))
    prior = db.get(GuideCommandReceipt, (session_id, body['request_id']))
    if prior:
        if prior.digest != digest:
            if commit:
                db.rollback()
            raise AppError(409, 'IDEMPOTENCY_CONFLICT', '同一请求标识对应不同内容')
        result = json.loads(prior.result_json)
        if commit:
            db.rollback()
        return result
    db.expire_all()
    session = owned_session(db, owner_id, session_id)
    anchor = session_anchor(db, session)
    if anchor != (body['expected_session_version'], body['expected_task_id'], body['expected_state_version']):
        if commit:
            db.rollback()
        raise AppError(409, 'STALE_STATE', '会话或任务版本已变化')
    task = db.get(GuideTask, anchor[1]) if anchor[1] else None
    kind = body['kind']
    if set(body.get('conditions') or {}) & {'activity_id', 'dish_groups', 'dish_selection', 'history_source', 'history_memory', 'history_memory_defaults', 'history_reminder'}:
        raise AppError(422, 'RESERVED_TASK_CONDITION', '活动范围与菜品分组只能通过对应的明确入口更新')
    if kind == 'new_goal':
        if not body['goal'] or not body['goal'].strip():
            if commit:
                db.rollback()
            raise AppError(422, 'GOAL_REQUIRED', '请说明新的购买目标')
        if task:
            task.status = 'superseded'
            task.state_version += 1
        task = GuideTask(task_id=f'task-{uuid4().hex}', session_id=session_id, owner_id=owner_id, goal=body['goal'], conditions_json=json.dumps(body['conditions'] or {}, ensure_ascii=False), state_version=0, current_step='understanding', status='active')
        db.add(task)
        session.current_task_id = task.task_id
        session.session_version += 1
    elif kind in ('amend', 'abandon'):
        if task is None:
            if commit:
                db.rollback()
            raise AppError(409, 'NO_ACTIVE_TASK', '当前没有活动购买任务')
        task.state_version += 1
        if kind == 'abandon':
            task.status = 'abandoned'
            session.current_task_id = None
            session.session_version += 1
        else:
            if not body['conditions']:
                if commit:
                    db.rollback()
                raise AppError(422, 'CONDITIONS_REQUIRED', '请说明要修改的条件')
            conditions = json.loads(task.conditions_json)
            for key in body['conditions']:
                conditions.get('history_memory_defaults', {}).pop(key, None)
            if 'people' in body['conditions']:
                for group in conditions.get('dish_groups', []):
                    group['people'] = body['conditions']['people']
                    group['people_origin'] = 'explicit'
                if conditions.get('dish_selection'):
                    conditions['dish_selection']['people'] = body['conditions']['people']
                    conditions['dish_selection']['people_origin'] = 'explicit'
            task.conditions_json = json.dumps({**conditions, **body['conditions']}, ensure_ascii=False)
            task.plan_json = None
            task.current_step = 'understanding'
    db.flush()
    if kind == 'new_goal':
        from app.services.history_service import HistoryService
        HistoryService(db, owner_id).offer_reminder(session, task)
        db.flush()
    result = task_projection(db, session)
    result['available_actions'] = ['send_message']
    result['plan'] = json.loads(task.plan_json) if task and task.plan_json else None
    result['message'] = {'new_goal': '好的，开始这个购买任务 🙂', 'amend': '条件已更新，我会按新条件继续核对。', 'abandon': '已放弃这个购买任务，购物车里的商品仍保留。', 'continue': '继续当前购买任务。'}[kind]
    db.add(GuideCommandReceipt(session_id=session_id, request_id=body['request_id'], digest=digest, result_json=json.dumps(result, ensure_ascii=False)))
    if commit:
        db.commit()
    return result

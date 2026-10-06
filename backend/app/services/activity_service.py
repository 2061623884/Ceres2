"""One existing homepage activity, using ordinary task and purchase authorities."""
import json
from uuid import uuid4
from sqlalchemy import func, select, update
from app.core.errors import AppError
from app.models.guide import GuideCommandReceipt, GuideMessage, GuideSession, GuideTask
from app.services.pi_product_turn_service import owned_session


def activity_mismatch(product, conditions):
    activity_id = conditions.get('activity_id')
    metadata = product['metadata']
    return bool(activity_id and (activity_id not in metadata.get('activity_ids', []) or metadata.get('finished_product') is not True))


def enter_light_meal(db, owner_id, session_id, body):
    from app.api.guide import projection
    from app.services.guide_lifecycle_service import require_canonical_session, transition
    from app.services.product_question_service import ProductQuestionService, supply_fingerprint
    owned_session(db, owner_id, session_id)
    require_canonical_session(db, owner_id, session_id)
    digest = supply_fingerprint({'activity_id':'light-meal', **body})
    db.execute(update(GuideSession).where(GuideSession.session_id == session_id, GuideSession.owner_id == owner_id).values(session_version=GuideSession.session_version))
    receipt = db.get(GuideCommandReceipt, (session_id, body['request_id']))
    if receipt:
        if receipt.digest != digest:
            raise AppError(409, 'IDEMPOTENCY_CONFLICT', '同一请求对应不同活动入口')
        return json.loads(receipt.result_json)
    db.expire_all()
    session = owned_session(db, owner_id, session_id)
    task = db.get(GuideTask, session.current_task_id) if session.current_task_id else None
    conditions = json.loads(task.conditions_json) if task else {}
    for key in ('activity_id', 'query', 'category_id', 'product_type', 'dish_groups', 'dish_selection', 'history_source', 'history_memory', 'history_memory_defaults', 'history_reminder'):
        conditions.pop(key, None)
    transition(db, owner_id, session_id, {**body, 'kind':'new_goal', 'goal':'选购首页活动成品', 'conditions':conditions}, commit=False)
    session = owned_session(db, owner_id, session_id)
    task = db.get(GuideTask, session.current_task_id)
    conditions = json.loads(task.conditions_json)
    conditions['activity_id'] = 'light-meal'
    task.conditions_json = json.dumps(conditions, ensure_ascii=False)
    db.flush()
    questions = ProductQuestionService(db, owner_id)
    message_id = f'msg-{uuid4().hex}'
    question = questions.publish(session_id, questions.explore(session_id, {}), message_id)
    sequence = db.scalar(select(func.max(GuideMessage.sequence)).where(GuideMessage.session_id == session_id)) or 0
    db.add(GuideMessage(message_id=message_id, session_id=session_id, owner_id=owner_id, task_id=session.current_task_id, sequence=sequence+1, role='assistant', kind='question', content=json.dumps(question, ensure_ascii=False), request_id=body['request_id']))
    db.flush()
    result = projection(db, session, include_messages=True)
    receipt = db.get(GuideCommandReceipt, (session_id, body['request_id']))
    receipt.digest = digest
    receipt.result_json = json.dumps(result, ensure_ascii=False)
    db.commit()
    return result

"""Role navigation metadata on the existing canonical session and command receipts.

No business write is authorized here. Destination roles re-read their own facts.
"""
import hashlib
import json
import logging
import time
from uuid import uuid4
from sqlalchemy import select, update
from app.core.errors import AppError
from app.models.guide import GuideSession, GuideCommandReceipt, GuideMessage, GuideEntry
from app.services.pi_product_turn_service import owned_session, session_anchor
from app.services.guide_lifecycle_service import require_canonical_session, canonical_entry
from app.services.kev_provider import judge, KevUnavailable, CRITERIA_VERSION

KEY = 'role_navigation'


def lock_session(db, owner_id, session_id):
    owned_session(db, owner_id, session_id)
    require_canonical_session(db, owner_id, session_id)
    db.execute(update(GuideSession).where(GuideSession.session_id == session_id, GuideSession.owner_id == owner_id).values(session_version=GuideSession.session_version))
    db.expire_all()
    return owned_session(db, owner_id, session_id)


def metadata(session):
    return json.loads(session.entry_context_json).get(KEY)


def save(session, opening):
    context = json.loads(session.entry_context_json)
    context[KEY] = opening
    session.entry_context_json = json.dumps(context, ensure_ascii=False)


def current(session, opening_id=None):
    opening = metadata(session)
    if not opening or opening['closed'] or (opening_id and opening['opening_id'] != opening_id):
        raise AppError(409, 'OPENING_CLOSED', '聊天已关闭，请重新打开')
    return opening


def open_chat(db, owner_id, session_id, role):
    session = lock_session(db, owner_id, session_id)
    opening = metadata(session)
    if not opening or opening['closed']:
        opening = {'opening_id': 'opening-' + uuid4().hex, 'role': role, 'prompt_displayed': False, 'closed': False, 'pending_request_id': None, 'latest_request_id': None, 'accepted_request_id': None}
        save(session, opening)
    db.commit()
    return read_opening(db, owner_id, session_id)


def read_opening(db, owner_id, session_id):
    opening = current(owned_session(db, owner_id, session_id))
    result = {**opening, 'handoff': None}
    if opening.get('accepted_request_id'):
        route = json.loads(receipt(db, session_id, opening['accepted_request_id']).result_json)
        if route.get('criteria_version') == CRITERIA_VERSION and route['authorized_role'] == opening['role']:
            result['handoff'] = {key: route[key] for key in ('routing_request_id', 'original_message', 'selected_object')}
    return result


def close_chat(db, owner_id, session_id, opening_id):
    session = lock_session(db, owner_id, session_id)
    opening = current(session, opening_id)
    opening.update(closed=True, pending_request_id=None, accepted_request_id=None)
    save(session, opening)
    db.commit()
    return opening


def receipt(db, session_id, request_id):
    return db.get(GuideCommandReceipt, (session_id, 'route:' + request_id))


def completed_execution(db, session_id, request_id, role):
    """Only a durable terminal result can survive a legacy navigation contract."""
    if role == 'keke':
        from app.models.guide import GuideTurnReceipt
        from app.services.guide_run_service import TERMINAL
        row = db.scalar(select(GuideTurnReceipt).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.request_id == request_id))
        return row is not None and row.status in TERMINAL and row.result_json is not None
    if role == 'momo':
        row = db.get(GuideCommandReceipt, (session_id, 'momo:' + request_id))
        return row is not None and json.loads(row.result_json)['status'] in ('completed', 'failed')
    return False


def decide_route(db, owner_id, session_id, body):
    session = lock_session(db, owner_id, session_id)
    digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    prior = receipt(db, session_id, body['request_id'])
    if prior:
        if prior.digest != digest:
            db.rollback()
            raise AppError(409, 'IDEMPOTENCY_CONFLICT', '同一文字请求标识对应不同内容')
        result = json.loads(prior.result_json)
        if result.get('criteria_version') != CRITERIA_VERSION:
            if not completed_execution(db, session_id, body['request_id'], result['authorized_role']):
                db.rollback()
                raise AppError(409, 'STALE_NAVIGATION', '旧版导航请求已失效，请重新说明需求')
            # Preserve the stored original metadata for the business digest,
            # while projecting no old page-changing or continuation instruction.
            result = {**result, 'status': 'ready', 'show_prompt': False,
                      'continue_original': False, 'capability': None, 'legacy_replay': True}
        db.rollback()
        return result
    opening = current(session, body['opening_id'])
    if opening['role'] != body['role']:
        raise AppError(409, 'ROLE_CHANGED', '当前角色已变化，请刷新后继续')
    recent = db.scalars(select(GuideMessage).where(GuideMessage.session_id == session_id).order_by(GuideMessage.sequence.desc()).limit(6)).all()
    dialogue = [{'role': row.role, 'content': row.content} for row in reversed(recent)]
    if body['role'] == 'momo':
        dialogue = []
        if body.get('role_session_id'):
            from app.mercury.models import MercuryCase
            case = db.get(MercuryCase, body['role_session_id'])
            if case is None or case.owner_id != owner_id:
                raise AppError(403, 'CASE_FORBIDDEN', '无法读取该售后会话')
            dialogue = json.loads(case.messages_json)[-6:]
    state = {'current_role': body['role'], 'message': body['message'], 'selected_object': body.get('selected_object'),
             'recent_dialogue': dialogue}
    result = {'routing_request_id': body['request_id'], 'opening_id': opening['opening_id'], 'original_message': body['message'],
              'source_role': body['role'], 'target_role': body['role'], 'selected_object': body.get('selected_object'),
              'capability': None, 'authorized_role': None, 'show_prompt': False, 'continue_original': False, 'criteria_version': CRITERIA_VERSION, 'anchor': list(session_anchor(db, session))}
    if body['role'] == 'momo':
        result.update(status='ready', authorized_role='momo', entry_judgment={'outcome': 'not_attempted', 'elapsed_ms': None, 'reason': 'momo_direct'})
    else:
        started_at = time.monotonic()
        try:
            choice, raw = judge(state)
            result['provider_output'] = raw
            result['entry_judgment'] = {'outcome': choice, 'elapsed_ms': (time.monotonic() - started_at) * 1000, 'reason': None}
            if choice == 'yes':
                result.update(status='switch', target_role='momo', show_prompt=not opening['prompt_displayed'],
                              message='这件事可以交给墨墨。要切换吗？')
            else:
                result.update(status='ready', authorized_role='keke')
        except KevUnavailable as exc:
            from app.services.guide_run_service import safe_failure_diagnostic
            logging.getLogger(__name__).warning(
                'Kev entry fallback session_id=%s request_id=%s causes=%s',
                session_id, body['request_id'], safe_failure_diagnostic(exc),
            )
            result.update(status='ready', authorized_role='keke', provider_error=exc.reason,
                          entry_judgment={'outcome': exc.outcome, 'elapsed_ms': (time.monotonic() - started_at) * 1000, 'reason': exc.reason})
    opening['accepted_request_id'] = body['request_id'] if result['continue_original'] else None
    opening['latest_request_id'] = body['request_id']
    opening['pending_request_id'] = body['request_id'] if result['status'] == 'switch' else None
    save(session, opening)
    db.add(GuideCommandReceipt(session_id=session_id, request_id='route:' + body['request_id'], digest=digest, result_json=json.dumps(result, ensure_ascii=False)))
    db.commit()
    return result


def displayed(db, owner_id, session_id, opening_id, routing_request_id):
    session = lock_session(db, owner_id, session_id)
    opening = current(session, opening_id)
    row = receipt(db, session_id, routing_request_id)
    route = json.loads(row.result_json) if row else None
    # ACK can arrive after acceptance/decline or a newer text. The actual
    # displayed offer, not its continued pending status, consumes this quota.
    if not route or route['opening_id'] != opening_id or route['status'] != 'switch' or not route['show_prompt']:
        raise AppError(409, 'STALE_NAVIGATION', '这条提示不属于当前聊天中的切换建议')
    opening['prompt_displayed'] = True
    save(session, opening)
    db.commit()
    return opening


def switch_role(db, owner_id, session_id, body):
    session = lock_session(db, owner_id, session_id)
    opening = current(session, body['opening_id'])
    # A button without a route ID chooses a page only. Never recover old text
    # implicitly from either pending or already accepted handoff metadata.
    request_id = body.get('routing_request_id')
    handoff = None
    if request_id:
        if request_id != (opening['pending_request_id'] or opening.get('accepted_request_id')) or request_id != opening['latest_request_id']:
            raise AppError(409, 'STALE_NAVIGATION', '原请求已经失效，请重新说明需求')
        row = receipt(db, session_id, request_id)
        route = json.loads(row.result_json)
        if route.get('criteria_version') != CRITERIA_VERSION:
            raise AppError(409, 'STALE_NAVIGATION', '旧版导航请求已失效，请重新说明需求')
        if route['anchor'] != list(session_anchor(db, session)):
            opening['pending_request_id'] = None
            save(session, opening)
            db.commit()
            raise AppError(409, 'STALE_NAVIGATION', '购物状态已变化，请重新说明需求')
        if body['accept'] and (route['target_role'] == body['target_role'] or route['status'] == 'unavailable'):
            route['authorized_role'] = body['target_role']
            opening['accepted_request_id'] = request_id
            row.result_json = json.dumps(route, ensure_ascii=False)
            handoff = {key: route[key] for key in ('routing_request_id', 'original_message', 'selected_object')}
    if not body['accept'] or request_id is None:
        opening['accepted_request_id'] = None
    if body['accept']:
        opening['role'] = body['target_role']
    opening['pending_request_id'] = None
    save(session, opening)
    db.commit()
    return {**opening, 'handoff': handoff}


def canonical_for_owner(db, owner_id):
    entry = db.get(GuideEntry, owner_id)
    if entry:
        return owned_session(db, owner_id, entry.session_id)
    return canonical_entry(db, owner_id, {'page': 'orders', 'store_id': None, 'delivery_zone_id': None})


def authorize_text(db, owner_id, session_id, role, body):
    """Called by public role ingress, never by tool loops/recovery/structured actions."""
    session = owned_session(db, owner_id, session_id)
    route_id = body.get('routing_request_id') or body['request_id']
    row = receipt(db, session_id, route_id)
    if body['request_id'] != route_id:
        raise AppError(409, 'ROUTE_REQUEST_MISMATCH', '续接必须沿用原请求标识')
    if row:
        result = json.loads(row.result_json)
        if result['original_message'] != body['message']:
            raise AppError(409, 'IDEMPOTENCY_CONFLICT', '原始文字与路由请求不一致')
    elif body.get('routing_request_id'):
        raise AppError(409, 'ROUTE_NOT_FOUND', '原请求已失效，请重新发送')
    else:
        opening = open_chat(db, owner_id, session_id, role)
        result = decide_route(db, owner_id, session_id, {'request_id': route_id, 'message': body['message'], 'role': role, 'opening_id': opening['opening_id'], 'selected_object': body.get('_selected_object'), 'role_session_id': body.get('_role_session_id')})
    # Keep the existing session write lock through the caller's run admission.
    # The provider receipt is already durable; this short transaction contains
    # only freshness validation and admission, never model execution.
    session = lock_session(db, owner_id, session_id)
    # A previously completed run can still replay its receipt after close; an
    # accepted but never admitted handoff must not start in a different opening.
    from app.models.guide import GuideTurnReceipt
    admitted = db.scalar(select(GuideTurnReceipt).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.request_id == route_id)) if role == 'keke' else db.get(GuideCommandReceipt, (session_id, 'momo:' + route_id))
    if result.get('criteria_version') != CRITERIA_VERSION and not completed_execution(db, session_id, route_id, role):
        raise AppError(409, 'STALE_NAVIGATION', '旧版导航请求已失效，请重新说明需求')
    if admitted is None:
        opening = current(session)
        if opening['opening_id'] != result['opening_id'] or opening['role'] != role:
            raise AppError(409, 'STALE_NAVIGATION', '原聊天或角色已变化，请重新说明需求')
        if result['source_role'] != role or result['status'] == 'unavailable':
            if opening.get('accepted_request_id') != route_id or result['anchor'] != list(session_anchor(db, session)):
                raise AppError(409, 'STALE_NAVIGATION', '原请求或购物状态已变化，请重新说明需求')
    if result['authorized_role'] != role:
        raise AppError(409, 'ROLE_NAVIGATION_REQUIRED', result.get('message', '请先选择角色'), navigation=result)
    return result


def consume_handoff(db, owner_id, session_id, request_id):
    session = lock_session(db, owner_id, session_id)
    opening = metadata(session)
    if opening and opening.get('accepted_request_id') == request_id:
        opening['accepted_request_id'] = None
        save(session, opening)
    db.commit()

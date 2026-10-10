"""Ticket transitions and canonical responsibility fences share one transaction."""
from datetime import datetime, timezone
import json
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select, update
from app.human.models import HumanTicket, HumanHandoffState
from app.mercury.models import MercuryCase, SimulatedOrder

ACTIVE = ('open', 'waiting_user')


def owned_case(db, owner_id, case_id):
    case = db.scalar(select(MercuryCase).where(MercuryCase.case_id == case_id, MercuryCase.owner_id == owner_id))
    if case is None:
        raise HTTPException(404, '未找到该售后会话')
    return case


def open_ticket(db, case_id):
    return db.scalar(select(HumanTicket).where(HumanTicket.case_id == case_id, HumanTicket.status.in_(ACTIVE)))


def latest_ticket(db, case_id):
    return db.scalar(select(HumanTicket).where(HumanTicket.case_id == case_id).order_by(HumanTicket.created_at.desc()).limit(1))


def ticket_view(db, ticket):
    if ticket is None:
        return None
    case = db.get(MercuryCase, ticket.case_id)
    order = db.scalar(select(SimulatedOrder).where(SimulatedOrder.order_id == ticket.order_id,
                                                  SimulatedOrder.owner_id == case.owner_id))
    summary = None if order is None else {'order_id': order.order_id, 'status': order.status,
        'total_fen': order.total_fen, 'items': [{'name': item['name'], 'quantity': item['quantity']}
                                              for item in json.loads(order.snapshot_json)['items']]}
    applications, photos = ticket_evidence(db, ticket, case.owner_id)
    return {'ticket_id': ticket.ticket_id, 'case_id': case.case_id, 'owner_id': case.owner_id,
        'order_id': ticket.order_id, 'order_summary': summary, 'reason': ticket.reason,
        'summary': ticket.summary, 'status': ticket.status, 'generation': ticket.generation,
        'version': ticket.version, 'history': json.loads(ticket.history_json),
        'messages': json.loads(ticket.messages_json),
        'photos': [{'photo_id':photo.photo_id, 'content_type':photo.content_type} for photo in photos],
        'applications': [json.loads(row.result_json) for row in applications]}


def ticket_evidence(db, ticket, owner_id):
    """Only explicitly linked confirmed applications and their immutable photos."""
    from app.mercury.aftersales_models import AfterSalesPhoto, AfterSalesReceipt, AfterSalesApplication, AfterSalesProposal
    applications = db.scalars(select(AfterSalesReceipt).join(AfterSalesApplication,
        AfterSalesApplication.application_id == AfterSalesReceipt.application_id).join(AfterSalesProposal,
        AfterSalesProposal.proposal_id == AfterSalesApplication.proposal_id).where(
        AfterSalesReceipt.case_id == ticket.case_id, AfterSalesReceipt.owner_id == owner_id,
        AfterSalesApplication.case_id == ticket.case_id, AfterSalesApplication.owner_id == owner_id,
        AfterSalesApplication.order_id == ticket.order_id,
        AfterSalesApplication.human_ticket_id == ticket.ticket_id,
        AfterSalesProposal.responsibility_generation == ticket.generation - 1)).all()
    # Refund/return receipts created before photo support do not contain photo_ids.
    photo_ids = {photo_id for receipt in applications
                 for photo_id in json.loads(receipt.result_json).get('photo_ids', [])}
    photos = db.scalars(select(AfterSalesPhoto).where(
        AfterSalesPhoto.photo_id.in_(photo_ids), AfterSalesPhoto.owner_id == owner_id,
        AfterSalesPhoto.case_id == ticket.case_id, AfterSalesPhoto.order_id == ticket.order_id)).all()
    return applications, photos


def create_ticket(db, case, summary, reason):
    existing = open_ticket(db, case.case_id)
    if existing is not None:
        return existing
    generation = case.responsibility_generation
    changed = db.execute(update(MercuryCase).where(MercuryCase.case_id == case.case_id,
        MercuryCase.owner_id == case.owner_id, MercuryCase.responsibility == 'agent',
        MercuryCase.responsibility_generation == generation).values(responsibility='human',
        responsibility_generation=generation + 1, active_run_id=None, active_until=None)).rowcount
    if changed != 1:
        # A concurrent handoff may already own this same issue. Read after its write.
        db.expire_all()
        existing = open_ticket(db, case.case_id)
        if existing is not None:
            return existing
        raise HTTPException(409, '事项责任已变化，请刷新后重试')
    ticket = HumanTicket(ticket_id=f'ht_{uuid4().hex}', case_id=case.case_id,
        order_id=case.order_id, reason=reason, summary=summary, status='open', generation=generation + 1,
        version=1, history_json=case.messages_json, messages_json='[]',
        created_at=datetime.now(timezone.utc).isoformat())
    db.add(ticket)
    db.flush()
    return ticket


def record_query_outcome(db, case_id, state):
    """Called only after fenced query publication, before its owning commit."""
    case = db.get(MercuryCase, case_id)
    streak = db.get(HumanHandoffState, case_id)
    signal = state.get('human_signal')
    if streak is None:
        streak = HumanHandoffState(case_id=case_id, selection_version=case.selection_version, service_failures=0)
        db.add(streak)
    if streak.selection_version != case.selection_version:
        streak.selection_version = case.selection_version
        streak.service_failures = 0
    streak.service_failures = streak.service_failures + 1 if signal == 'service_failure' else 0
    if signal == 'policy_indeterminate':
        create_ticket(db, case, '现有政策无法确定此问题，需要人工核实。', 'policy_indeterminate')
    elif streak.service_failures >= 2:
        create_ticket(db, case, '售后查询服务连续失败，需要人工跟进。', 'persistent_service_failure')


def append_message(db, ticket, version, author, action, content):
    if ticket.status not in ACTIVE or ticket.version != version:
        raise HTTPException(409, '工单已更新或结束，请刷新后重试')
    status = {'reply': 'open', 'ask': 'waiting_user', 'resolve': 'resolved', 'close': 'closed'}[action]
    messages = json.loads(ticket.messages_json)
    messages.append({'message_id': f'hm_{uuid4().hex}', 'author': author, 'kind': action,
                     'content': content, 'created_at': datetime.now(timezone.utc).isoformat()})
    changed = db.execute(update(HumanTicket).where(HumanTicket.ticket_id == ticket.ticket_id,
        HumanTicket.version == version, HumanTicket.status.in_(ACTIVE)).values(
        version=version + 1, status=status, messages_json=json.dumps(messages, ensure_ascii=False))).rowcount
    if changed != 1:
        raise HTTPException(409, '工单已更新，请刷新后重试')
    # Reply is only correspondence. It never grants a proposal or financial authority.
    if status in ('resolved', 'closed'):
        changed = db.execute(update(MercuryCase).where(MercuryCase.case_id == ticket.case_id,
            MercuryCase.responsibility == 'human',
            MercuryCase.responsibility_generation == ticket.generation).values(
            responsibility='agent', responsibility_generation=MercuryCase.responsibility_generation + 1)).rowcount
        if changed != 1:
            raise HTTPException(409, '事项责任已变化，请刷新后重试')
        streak = db.get(HumanHandoffState, ticket.case_id)
        if streak is not None:
            streak.service_failures = 0
    db.flush()
    db.refresh(ticket)
    return ticket

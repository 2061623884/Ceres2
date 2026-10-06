"""Owner-bound canonical cases; checkpoints never authorize case access."""
from datetime import datetime, timezone
import json
import time
import uuid
from sqlalchemy import or_, update
from app.mercury.models import MercuryCase, SimulatedOrder
from app.human.service import record_query_outcome


class CaseStore:
    def __init__(self, sessions):
        self.sessions = sessions

    def create_case(self, owner_id):
        with self.sessions() as db:
            case = MercuryCase(case_id=f'ms_{uuid.uuid4().hex}', owner_id=owner_id,
                               created_at=datetime.now(timezone.utc))
            db.add(case)
            db.commit()
            return {'session_id': case.case_id, 'created_at': case.created_at.isoformat()}

    def read_case(self, owner_id, case_id):
        with self.sessions() as db:
            row = db.query(MercuryCase).filter_by(case_id=case_id, owner_id=owner_id).first()
            if row is None:
                return None
            return {'session_id': row.case_id, 'created_at': row.created_at.isoformat(),
                    'order_id': row.order_id, 'selection_version': row.selection_version,
                    'responsibility': row.responsibility,
                    'responsibility_generation': row.responsibility_generation,
                    'messages': json.loads(row.messages_json), 'status': row.query_status,
                    'tool_rounds': row.tool_rounds}

    def select_order(self, owner_id, case_id, order_id, selection_version):
        with self.sessions() as db:
            if not db.query(SimulatedOrder).filter_by(order_id=order_id, owner_id=owner_id).first():
                return 'not_found'
            changed = db.execute(update(MercuryCase).where(
                MercuryCase.case_id == case_id, MercuryCase.owner_id == owner_id,
                MercuryCase.selection_version == selection_version,
                MercuryCase.responsibility == 'agent',
                or_(MercuryCase.active_run_id.is_(None), MercuryCase.active_until <= time.time()),
            ).values(order_id=order_id, selection_version=MercuryCase.selection_version + 1,
                     responsibility_generation=MercuryCase.responsibility_generation + 1,
                     query_status='ready', tool_rounds=0)).rowcount
            db.commit()
            return 'selected' if changed else 'conflict'

    def reserve_query(self, owner_id, case_id):
        run_id = uuid.uuid4().hex
        now = time.time()
        with self.sessions() as db:
            changed = db.execute(update(MercuryCase).where(
                MercuryCase.case_id == case_id, MercuryCase.owner_id == owner_id,
                MercuryCase.responsibility == 'agent',
                or_(MercuryCase.active_run_id.is_(None), MercuryCase.active_until <= now),
            ).values(active_run_id=run_id, active_until=now + 30)).rowcount
            db.commit()
        return run_id if changed else None

    def publish_result(self, owner_id, case, run_id, state, *, memory_turn=None):
        messages = [{'role': message['role'], 'content': message['content'],
                     **({'memory_management': True} if message.get('memory_management') else {}),
                     **({'memory_list_refs': message['memory_list_refs']} if 'memory_list_refs' in message else {})}
                    for message in state['messages']
                    if message['role'] in ('user', 'assistant') and message.get('content')
                    and not message.get('tool_calls')]
        with self.sessions() as db:
            changed = db.execute(update(MercuryCase).where(
                MercuryCase.case_id == case['session_id'], MercuryCase.owner_id == owner_id,
                MercuryCase.active_run_id == run_id,
                MercuryCase.selection_version == case['selection_version'],
                MercuryCase.responsibility == 'agent',
                MercuryCase.responsibility_generation == case['responsibility_generation'],
            ).values(messages_json=json.dumps(messages, ensure_ascii=False),
                     query_status=state['status'], tool_rounds=state.get('rounds', 0))).rowcount
            if changed == 1:
                if state['status'] == 'completed' and state.get('action_results'):
                    result = memory_turn.commit(db)
                    state['action_results'] = [result]
                    state['final_text'] = result['message']
                    messages[-1]['content'] = result['message']
                    if result['action'] == 'list':
                        from app.services.memory_service import memory_list_references
                        messages[-1]['memory_list_refs'] = memory_list_references(result['records'], run_id)
                    db.execute(update(MercuryCase).where(MercuryCase.case_id == case['session_id']).values(
                        messages_json=json.dumps(messages, ensure_ascii=False)))
                if state['status'] == 'completed' and not state.get('action_results'):
                    from app.services.memory_background import enqueue_extraction
                    user_text = next(message['content'] for message in reversed(messages) if message['role'] == 'user')
                    enqueue_extraction(db, owner_id=owner_id, role='momo', source_id=run_id, source_text=user_text)
                record_query_outcome(db, case['session_id'], state)
            db.commit()
        return changed == 1

    def release_query(self, owner_id, case_id, run_id):
        with self.sessions() as db:
            db.execute(update(MercuryCase).where(
                MercuryCase.case_id == case_id, MercuryCase.owner_id == owner_id,
                MercuryCase.active_run_id == run_id,
            ).values(active_run_id=None, active_until=None))
            db.commit()

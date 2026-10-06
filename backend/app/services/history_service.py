"""Historical plans are references; every selection creates fresh purchase facts."""
from __future__ import annotations
import hashlib
import json
from uuid import uuid4
from math import ceil
from sqlalchemy import func, select, update
from app.core.errors import AppError
from app.models.guide import GuideSession, GuideTask, GuideMessage, GuideCommandReceipt
from app.services.guide_lifecycle_service import require_canonical_session, task_projection
from app.services.pi_product_turn_service import owned_session, session_anchor
from app.services.purchase_service import PurchaseService, plan_actions, render_plan

PROTECTED = {'dish_groups', 'dish_selection', 'history_source', 'history_memory', 'history_memory_defaults', 'history_reminder'}


def current_conditions(task):
    conditions = json.loads(task.conditions_json) if task else {}
    remembered = conditions.get('history_memory_defaults', {})
    return {key:value for key,value in conditions.items() if key not in PROTECTED and key not in remembered}


class HistoryService:
    def __init__(self, db, owner_id):
        self.db, self.owner_id = db, owner_id

    def sources(self, session_id):
        session = owned_session(self.db, self.owner_id, session_id)
        rows = self.db.scalars(select(GuideTask).where(GuideTask.owner_id == self.owner_id, GuideTask.plan_json.is_not(None), GuideTask.status != 'active').order_by(GuideTask.task_id)).all()
        return [{'task_id':row.task_id, 'goal':row.goal, 'status':row.status, 'plan':json.loads(row.plan_json)} for row in rows]

    def offer_reminder(self, session, task):
        """Called once inside new-goal admission, after checking actual cart facts."""
        from app.models.cart import Cart, CartItem
        from app.services.memory_service import _terms
        store_id = session.supply_store_id or json.loads(session.entry_context_json)['store_id']
        quantities = dict(self.db.execute(select(CartItem.sku_id, CartItem.quantity).join(Cart).where(Cart.owner_id == self.owner_id, Cart.store_id == store_id)).all())
        terms = _terms(task.goal or '')
        for source in self.sources(session.session_id):
            if source['status'] == 'abandoned':
                continue
            plan = source['plan']
            related = _terms(source['goal'] or '') | _terms(' '.join(group['name'] for group in plan.get('groups', [])))
            outstanding = [row for row in plan['items'] if row['selected'] and row['quantity'] > max(row['added_quantity'], quantities.get(row['sku_id'], 0))]
            known_rows = {row['sku_id']:row for row in plan['items']}
            active_groups = {group['group_id'] for group in plan.get('groups', [])}
            unresolved = []
            for gap in plan.get('gaps', []):
                if gap['group_ids'] and not active_groups.intersection(gap['group_ids']):
                    continue
                row = known_rows.get(gap['sku_id'])
                if row is None:
                    unresolved.append(gap)
                    continue
                required_packs = ceil(row['coverage_quantity'] / row['spec_quantity']) if row.get('coverage_quantity') is not None else max(row['quantity'], gap['requested_packs'] or 0)
                if required_packs > max(row['added_quantity'], quantities.get(row['sku_id'], 0)):
                    unresolved.append(gap)
            key = 'history-reminder:' + source['task_id']
            if not terms & related or not (outstanding or unresolved) or self.db.get(GuideCommandReceipt, (session.session_id, key)):
                continue
            reminder = {'source_task_id':source['task_id'], 'goal':source['goal'], 'decision':'offered', 'message':'之前的“' + (source['goal'] or '采购清单') + '”还有未完成项，要按当前条件重新准备吗？'}
            conditions = json.loads(task.conditions_json)
            conditions['history_reminder'] = reminder
            task.conditions_json = json.dumps(conditions, ensure_ascii=False)
            self.db.add(GuideCommandReceipt(session_id=session.session_id, request_id=key, digest=hashlib.sha256(source['task_id'].encode()).hexdigest(), result_json=json.dumps(reminder, ensure_ascii=False)))
            return reminder
        return None

    def dismiss_reminder(self, session_id, task_id, decision):
        session = owned_session(self.db, self.owner_id, session_id)
        require_canonical_session(self.db, self.owner_id, session_id)
        self.db.execute(update(GuideSession).where(GuideSession.session_id == session_id, GuideSession.owner_id == self.owner_id).values(session_version=GuideSession.session_version))
        self.db.expire_all()
        session = owned_session(self.db, self.owner_id, session_id)
        if session.current_task_id != task_id:
            raise AppError(409, 'STALE_STATE', '当前购买任务已变化')
        task = self.db.get(GuideTask, task_id) if task_id else None
        if task:
            conditions = json.loads(task.conditions_json)
            reminder = conditions.get('history_reminder')
            if reminder and reminder['decision'] == 'offered':
                reminder['decision'] = decision
                task.conditions_json = json.dumps(conditions, ensure_ascii=False)
                record = self.db.get(GuideCommandReceipt, (session_id, 'history-reminder:' + reminder['source_task_id']))
                record.result_json = json.dumps(reminder, ensure_ascii=False)
        self.db.flush()

    def memory_context(self, session_id, source):
        from app.services.memory_service import MemoryService
        session = owned_session(self.db, self.owner_id, session_id)
        task = self.db.get(GuideTask, session.current_task_id) if session.current_task_id else None
        conditions = current_conditions(task)
        return MemoryService(self.db, self.owner_id).recall(role='keke', query=source['goal'] or '', current_conditions=conditions)

    def select(self, session_id, body, *, memory_defaults=None, memory_refs=None, displayed_message_id=None):
        db = self.db
        owned_session(db, self.owner_id, session_id)
        require_canonical_session(db, self.owner_id, session_id)
        db.execute(update(GuideSession).where(GuideSession.session_id == session_id, GuideSession.owner_id == self.owner_id).values(session_version=GuideSession.session_version))
        key = 'history:' + body['request_id']
        digest = hashlib.sha256(json.dumps({**body, 'memory_defaults':memory_defaults, 'memory_refs':memory_refs}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        prior = db.get(GuideCommandReceipt, (session_id, key))
        if prior:
            if prior.digest != digest:
                raise AppError(409, 'IDEMPOTENCY_CONFLICT', '同一历史选择标识对应不同内容')
            return json.loads(prior.result_json)
        db.expire_all()
        session = owned_session(db, self.owner_id, session_id)
        if session_anchor(db, session) != (body['expected_session_version'], body['expected_task_id'], body['expected_state_version']):
            raise AppError(409, 'STALE_STATE', '当前购买任务已变化')
        source = db.get(GuideTask, body['source_task_id'])
        if source is None or source.owner_id != self.owner_id:
            raise AppError(403, 'HISTORY_FORBIDDEN', '历史方案不可访问')
        if source.status == 'active' or not source.plan_json:
            raise AppError(409, 'HISTORY_SOURCE_INVALID', '请选择已留存的历史方案')
        old = json.loads(source.plan_json)
        current = db.get(GuideTask, session.current_task_id) if session.current_task_id else None
        conditions = current_conditions(current)
        memory = self.memory_context(session_id, {'goal':source.goal})['records']
        eligible = [row for row in memory if row['domain'] == 'shopping' and row['category'] != 'reference']
        current_refs = {(row['memory_id'], row['revision']) for row in eligible}
        submitted_refs = {(row['memory_id'], row['revision']) for row in memory_refs or []}
        if eligible and memory_refs is None:
            raise AppError(409, 'HISTORY_MEMORY_REVIEW_REQUIRED', '请在聊天中选定来源，先核对当前有效偏好再准备清单')
        if submitted_refs != current_refs:
            raise AppError(409, 'HISTORY_MEMORY_CHANGED', '有效偏好已变化，请重新核对历史采购条件')
        from app.schemas.history import HistoryDefaults
        defaults = HistoryDefaults.model_validate(memory_defaults or {}).model_dump(exclude_none=True)
        if defaults and not eligible:
            raise AppError(422, 'HISTORY_MEMORY_UNGROUNDED', '记忆条件需要当前有效的购物偏好来源')
        if eligible and not defaults:
            raise AppError(409, 'HISTORY_MEMORY_CLARIFICATION', '这些有效偏好需要先澄清如何用于本次采购')
        applied_defaults = {key:value for key,value in defaults.items() if key not in conditions}
        conditions = {**defaults, **conditions}
        conditions['history_memory_defaults'] = applied_defaults
        conditions['history_memory'] = memory
        provenance = {'task_id':source.task_id, 'plan_id':old['plan_id'], 'plan_version':old['plan_version'], 'goal':source.goal}
        conditions['history_source'] = provenance
        groups = json.loads(source.conditions_json).get('dish_groups', [])
        current_group_conditions = json.loads(current.conditions_json) if current else {}
        current_groups = current_group_conditions.get('dish_groups', [])
        same_source = current_group_conditions.get('history_source', {}).get('task_id') == source.task_id
        group_people = []
        for group in groups:
            candidates = [item for item in current_groups if item.get('source_group_id') == group['group_id']] if same_source else []
            if not candidates:
                candidates = [item for item in current_groups if item['dish_id'] == group['dish_id'] and item['people'] is not None]
                if candidates and (len(candidates) != 1 or sum(item['dish_id'] == group['dish_id'] for item in groups) != 1):
                    raise AppError(409, 'HISTORY_PEOPLE_CLARIFICATION', '多个同菜目标的人数不同或来源不明确，请先明确本次各组人数')
            explicit = candidates[0] if candidates and candidates[0]['people'] is not None and candidates[0].get('people_origin', 'explicit') != 'memory' else None
            group_people.append((explicit['people'], 'explicit') if explicit else (conditions.get('people'), 'memory' if 'people' in applied_defaults else 'explicit'))
        task = GuideTask(task_id=f'task-{uuid4().hex}', session_id=session_id, owner_id=self.owner_id, goal=source.goal, conditions_json=json.dumps(conditions, ensure_ascii=False), state_version=0, current_step='understanding', status='active')
        if current:
            current.status = 'superseded'
            current.state_version += 1
        db.add(task)
        session.current_task_id = task.task_id
        session.session_version += 1
        db.flush()
        purchase = PurchaseService(db, self.owner_id)
        message_id = displayed_message_id or f'msg-{uuid4().hex}'
        if groups:
            for group, (people, origin) in zip(groups, group_people):
                plan = purchase.prepare_dish(task.task_id, {'dish_id':group['dish_id'], 'operation':'append', 'people':people, 'people_origin':origin, 'source_group_id':group['group_id'], 'selections':group['selections'], 'pack_allocations':group.get('pack_allocations', {})}, message_id)
        else:
            if len(old['items']) != 1:
                raise AppError(409, 'HISTORY_SOURCE_INVALID', '请明确本次要购买的商品与数量')
            item = old['items'][0]
            plan = purchase.prepare(task.task_id, item['sku_id'], item['quantity'], message_id, supply_preview=True)
        plan['history_source'] = provenance
        plan['history_memory'] = memory
        plan['history_changes'] = self.changes(old, plan)
        task.plan_json = json.dumps(plan, ensure_ascii=False)
        sequence = db.scalar(select(func.max(GuideMessage.sequence)).where(GuideMessage.session_id == session_id)) or 0
        if displayed_message_id is None:
            db.add(GuideMessage(message_id=message_id, session_id=session_id, owner_id=self.owner_id, task_id=task.task_id, sequence=sequence+1, role='assistant', kind='plan', content=render_plan(plan), request_id=key))
        result = {**task_projection(db, session), 'plan':plan, 'available_actions':plan_actions(plan), 'message':render_plan(plan)}
        db.add(GuideCommandReceipt(session_id=session_id, request_id=key, digest=digest, result_json=json.dumps(result, ensure_ascii=False)))
        db.flush()
        return result

    def annotate(self, task, plan):
        conditions = json.loads(task.conditions_json)
        source = conditions.get('history_source')
        if source:
            original = self.db.get(GuideTask, source['task_id'])
            plan['history_source'] = source
            plan['history_memory'] = conditions['history_memory']
            plan['history_changes'] = self.changes(json.loads(original.plan_json), plan)

    @staticmethod
    def changes(old, new):
        changes = ['已按当前条件和模拟供给生成新清单；历史加购与批准不沿用。']
        old_rows = {row['sku_id']:row for row in old['items']}
        for row in new['items']:
            previous = old_rows.get(row['sku_id'])
            if previous is None:
                changes.append(f"新增当前商品：{row['name']}。")
            elif any(previous.get(field) != row.get(field) for field in ('quantity','unit_price_fen','available_qty','sellable')):
                changes.append(f"{row['name']}：原 {previous['quantity']} 件 / ¥{previous['unit_price_fen']/100:.2f}，本次 {row['quantity']} 件 / ¥{row['unit_price_fen']/100:.2f}；当前库存 {row['available_qty']}。")
        old_groups = {group['group_id']:group for group in old.get('groups', [])}
        retained = set()
        for after in new.get('groups', []):
            before = old_groups.get(after.get('source_group_id'))
            if before:
                retained.add(before['group_id'])
                if before['people'] != after['people']:
                    changes.append(f"{after['name']}：人数 {before['people']} → {after['people']}。")
            else:
                changes.append(f"新增目标：{after['name']}。")
        for group_id, before in old_groups.items():
            if group_id not in retained:
                changes.append(f"已移除历史目标：{before['name']}（{before['people']} 人）。")
        return changes


class HistoryTurn:
    """The model may interpret prose preferences, but cannot pick ambiguous history."""
    def __init__(self, db, owner_id, session_id, source_text):
        self.db, self.owner_id, self.session_id, self.source_text = db, owner_id, session_id, source_text
        self.results = {}

    def prepare(self, arguments):
        from app.schemas.history import HistoryCommand
        command = HistoryCommand.model_validate(arguments)
        service = HistoryService(self.db, self.owner_id)
        sources = service.sources(self.session_id)
        ref = f'history-{uuid4().hex}'
        if command.action == 'list':
            public = [{'task_id':source['task_id'], 'goal':source['goal'], 'plan_id':source['plan']['plan_id'], 'plan_version':source['plan']['plan_version'], 'memory':service.memory_context(self.session_id, source)} for source in sources]
            result = {'history_ref':ref, 'sources':public, 'message':'请选择历史来源，再按当前条件重新准备。' if public else '目前没有可重新采购的历史方案。'}
        else:
            source = next((source for source in sources if source['task_id'] == command.source_task_id), None)
            matches = [item for item in sources if item['goal'] and item['goal'] in self.source_text]
            explicit = source and (source['task_id'] in self.source_text or (len(matches) == 1 and matches[0]['task_id'] == source['task_id']))
            if not explicit:
                raise AppError(409, 'HISTORY_SELECTION_REQUIRED', '“上次”可能对应多个历史方案，请先明确选择来源')
            result = {'history_ref':ref, 'selection':{'source_task_id':source['task_id'], 'memory_defaults':command.memory_defaults.model_dump(exclude_none=True), 'memory_refs':[row.model_dump() for row in command.memory_refs]}, 'message':'来源已选定，将重新核对当前条件与供给；仍需单独确认加购。'}
        self.results[ref] = result
        return result

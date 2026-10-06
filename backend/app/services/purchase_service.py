"""Plan preparation and one caller-owned confirmation transaction."""
from __future__ import annotations
import hashlib
import json
from uuid import uuid4
from sqlalchemy import func, select, update
from app.core.errors import AppError
from app.models.guide import GuideSession, GuideTask, GuideMessage, GuideTurnReceipt, GuideCommandReceipt
from app.models.purchase import PurchaseConfirmation, PurchaseLedger
from app.models.catalog import CatalogProduct
from app.models.store import Offer, Store
from app.services.cart_service import CartService


def plan_actions(plan):
    return ['send_message', 'modify'] + (['confirm'] if plan['can_confirm'] else [])


def render_plan(plan):
    title = '供给预览（尚未选择采购）' if plan.get('plan_kind') == 'supply_preview' else '部分采购清单（未配齐全部食材）' if plan.get('plan_kind') == 'partial_purchase' else '采购清单'
    lines = [title + '（商品、价格和配送均为模拟数据）：']
    if plan.get('history_source'):
        lines.append('历史来源：' + (plan['history_source']['goal'] or plan['history_source']['task_id']))
        lines.extend(plan['history_changes'])
    for dish in plan.get('groups', [plan['dish']] if plan.get('dish') else []):
        lines.append(f"{dish['name']}：" + (f"菜谱默认基准 {dish['base_people']} 人用量，非用户指定人数。" if dish['people_source'] == 'default' else f"用户指定 {dish['people']} 人；菜谱基准 {dish['base_people']} 人。"))
    for row in plan['items']:
        requirement = row.get('requirement')
        if requirement is not None:
            if requirement['quantity'] is None:
                lines.append('基础调料用量未知；默认不选不代表家中已有，选购一包不代表菜谱用量。')
            else:
                difference = row['leftover_quantity']
                lines.append(f"需求 {requirement['quantity']:g}{requirement['unit']}，{'包装余量' if difference >= 0 else '尚未覆盖'} {abs(difference):g}{requirement['unit']}。")
        selection = '已选' if row['selected'] else '未选'
        lines.append(f"{selection} {row['name']}：{row['quantity']} 件销售包装，单价 ¥{row['unit_price_fen'] / 100:.2f}；已加购 {row['added_quantity']} 件，剩余 {row['remaining_quantity']} 件。")
    total = sum(row['remaining_quantity'] * row['unit_price_fen'] for row in plan['items'] if row['selected'])
    lines.extend(gap['message'] for gap in plan.get('gaps', []))
    if plan.get('plan_kind') == 'supply_preview':
        lines.append(f'所选规格需求合计 ¥{total / 100:.2f}，含当前不可售部分。请先选择替代或可售部分；选择后仍需独立确认加购。')
    else:
        lines.append(f'本次待加购合计 ¥{total / 100:.2f}。' + ('请先处理下方预算报价。' if plan.get('budget_quote') else '请核对后确认加购。'))
    if plan.get('budget_quote'):
        quote = plan['budget_quote']
        lines.append(f"当前预算 ¥{quote['budget_fen'] / 100:.2f}，本方案报价 ¥{quote['total_fen'] / 100:.2f}，超出预算。可修改方案，或明确接受报价后更新预算；接受报价不代表确认加购。")
    return '\n'.join(lines)


class PurchaseService:
    def __init__(self, db, owner_id):
        self.db, self.owner_id = db, owner_id

    def task(self, task_id):
        task = self.db.get(GuideTask, task_id)
        if task is None or task.owner_id != self.owner_id:
            raise AppError(403, 'TASK_FORBIDDEN', '购买任务不可访问')
        session = self.db.get(GuideSession, task.session_id)
        from app.services.guide_lifecycle_service import require_canonical_session
        require_canonical_session(self.db, self.owner_id, session.session_id)
        if session.current_task_id != task_id or task.status != 'active':
            raise AppError(409, 'STALE_STATE', '购买任务已变化')
        return task, session

    def facts(self, task, session, items, *, supply_preview=False, allow_quote=False):
        context = json.loads(session.entry_context_json)
        store_id = session.supply_store_id or context['store_id']
        zone = session.delivery_zone_id or context['delivery_zone_id']
        store = self.db.get(Store, store_id)
        if store is None or store.delivery_zone_id != zone or store.delivery_reachable is not True:
            raise AppError(409, 'DELIVERY_UNAVAILABLE', '当前配送区域不可配送或尚未核实')
        conditions = json.loads(task.conditions_json)
        exclusions = conditions.get('exclusions', [])
        from app.models.cart import Cart, CartItem
        cart_quantities = dict(self.db.execute(select(CartItem.sku_id, CartItem.quantity).join(Cart).where(Cart.owner_id == self.owner_id, Cart.store_id == store_id)).all())
        rows = []
        for item in items:
            sku_id, quantity = item['sku_id'], item['quantity']
            product = self.db.get(CatalogProduct, sku_id)
            offer = self.db.scalar(select(Offer).where(Offer.store_id == store_id, Offer.sku_id == sku_id))
            if not product or product.review_status != 'approved' or not offer or (not supply_preview and item.get('selected', True) and (not offer.sellable or offer.available_qty < quantity)):
                raise AppError(409, 'CHECKOUT_UNAVAILABLE', '商品供给不足或不可售')
            identities = [sku_id, product.name, product.name_zh, product.brand, *json.loads(product.ingredient_ids), *json.loads(product.usage_tags)]
            if item.get('selected', True) and any(exclusion in identities for exclusion in exclusions):
                raise AppError(409, 'EXCLUSION_CONFLICT', '商品不符合当前排除条件')
            ledger = self.db.get(PurchaseLedger, (task.task_id, sku_id))
            added = ledger.added_quantity if ledger else 0
            rows.append({'sku_id':sku_id, 'name':product.name_zh or product.name, 'image_path':product.image_path,
                         'quantity':quantity, 'unit_price_fen':offer.price_fen, 'line_total_fen':quantity * offer.price_fen,
                         'selected':item.get('selected', True), 'role':'required', 'added_quantity':added,
                         'remaining_quantity':max(0, quantity - added), 'offer_version':offer.offer_version,
                         'spec_quantity':product.spec_quantity, 'spec_unit':product.spec_unit,
                         'available_qty':offer.available_qty, 'available_to_add':max(0, offer.available_qty - cart_quantities.get(sku_id, 0)), 'sellable':offer.sellable})
        total = sum(row['line_total_fen'] for row in rows if row['selected'])
        if not allow_quote and conditions.get('budget_fen') is not None and total > conditions['budget_fen']:
            raise AppError(409, 'BUDGET_EXCEEDED', '清单金额超过当前预算')
        return rows, store, zone, total

    @staticmethod
    def project_budget(task, plan):
        budget = json.loads(task.conditions_json).get('budget_fen')
        total = plan['selected_total_fen']
        plan.pop('budget_quote', None)
        if budget is not None and total > budget:
            plan['budget_quote'] = {'budget_fen':budget, 'total_fen':total}
            plan['can_confirm'] = False

    def prepare(self, task_id, sku_id, quantity, displayed_message_id, *, supply_preview=False):
        task, session = self.task(task_id)
        rows, store, zone, total = self.facts(task, session, [{'sku_id':sku_id,'quantity':quantity}], supply_preview=supply_preview, allow_quote=True)
        prior = json.loads(task.plan_json) if task.plan_json else None
        plan = {'plan_id':prior['plan_id'] if prior else f'plan-{uuid4().hex}', 'plan_version':prior['plan_version'] + 1 if prior else 1,
                'mode':'bundle', 'items':rows, 'total_price_fen':total, 'selected_total_fen':total,
                'expires_at':None, 'validation_status':'valid', 'can_confirm':any(row['remaining_quantity'] for row in rows),
                'store_id':store.store_id, 'delivery_zone_id':zone, 'delivery_version':store.delivery_version,
                'displayed_message_id':displayed_message_id}
        if supply_preview:
            row = rows[0]
            available = row['available_to_add'] if row['sellable'] else 0
            gap = available < row['remaining_quantity']
            plan['plan_kind'] = 'supply_preview' if gap else 'full_plan'
            plan['gaps'] = [{'gap_id':f'supply:{sku_id}', 'ingredient_id':None, 'sku_id':sku_id, 'group_ids':[],
                             'kind':'unavailable' if available == 0 else 'shortage', 'requirement':{'quantity':quantity, 'unit':'sale_pack'},
                             'requested_packs':quantity, 'available_packs':available, 'shortfall_packs':quantity-available,
                             'alternatives':[], 'message':f"{row['name']}需要 {quantity} 件，当前可售 {available} 件；请决定是否仅采购可售部分。"}] if gap else []
            if gap:
                plan['can_confirm'] = False
        task.state_version += 1
        task.current_step = 'awaiting_confirmation'
        from app.services.history_service import HistoryService
        HistoryService(self.db, self.owner_id).annotate(task, plan)
        self.project_budget(task, plan)
        task.plan_json = json.dumps(plan, ensure_ascii=False)
        self.db.flush()
        return plan

    def group_purchase_ledger(self, task_id):
        receipts = self.db.scalars(select(PurchaseConfirmation).where(PurchaseConfirmation.task_id == task_id, PurchaseConfirmation.owner_id == self.owner_id).order_by(PurchaseConfirmation.request_key)).all()
        return [record for receipt in receipts for record in json.loads(receipt.result_json).get('group_purchases', [])]

    def prepare_dish(self, task_id, proposal, displayed_message_id):
        from app.services.dish_service import DishService, recipes, merge_group_requirements
        from app.services.catalog_service import CatalogService
        task, session = self.task(task_id)
        conditions = json.loads(task.conditions_json)
        groups = conditions.get('dish_groups', [])
        if not groups and conditions.get('dish_selection'):
            groups = [{'group_id':f'group-{uuid4().hex}', **conditions['dish_selection']}]
        if proposal.get('group_id') and not any(group['group_id'] == proposal['group_id'] for group in groups):
            raise AppError(422, 'DISH_GROUP_UNKNOWN', '菜品分组不存在，不能修改已移除的目标')
        if proposal.get('operation') == 'remove':
            groups = [group for group in groups if group['group_id'] != proposal['group_id']]
            target = None
        elif proposal.get('operation') == 'append' or not groups:
            target = {'group_id':f'group-{uuid4().hex}', 'dish_id':proposal['dish_id'], 'people':None, 'selections':{}, 'selected':{}}
            if proposal.get('source_group_id'):
                target['source_group_id'] = proposal['source_group_id']
            groups.append(target)
        else:
            matches = [group for group in groups if group['group_id'] == proposal['group_id']] if proposal.get('group_id') else [group for group in groups if group['dish_id'] == proposal['dish_id']]
            if len(matches) != 1:
                raise AppError(422, 'DISH_GROUP_AMBIGUOUS', '请明确要修改的菜品分组；新菜需要明确追加')
            target = matches[0]
        if target is not None:
            if target['dish_id'] != proposal['dish_id']:
                raise AppError(422, 'DISH_GROUP_MISMATCH', '菜谱与目标分组不一致')
            if proposal.get('people') is not None:
                target['people'] = proposal['people']
                target['people_origin'] = proposal.get('people_origin', 'explicit')
            target['selections'].update(proposal['selections'])
            for ingredient in proposal['selections']:
                target.get('pack_allocations', {}).pop(ingredient, None)
            if proposal.get('pack_allocations'):
                target['pack_allocations'] = proposal['pack_allocations']
        context = json.loads(session.entry_context_json)
        service = DishService(CatalogService(self.db, session.supply_store_id or context['store_id']))
        group_rows, public_groups = [], []
        for group in groups:
            recipe = next((dish for dish in recipes() if dish['dish_id'] == group['dish_id']), None)
            if recipe is None:
                raise AppError(422, 'DISH_UNKNOWN', '菜谱不存在')
            dish, requirements = service.requirements(recipe, group['people'] or recipe['base_people'], group['selections'], group.get('pack_allocations', {}))
            for requirement in requirements:
                ingredient = requirement['ingredient_id']
                if ingredient in group['selected']:
                    requirement['selected'] = group['selected'][ingredient]
                if requirement['sku_id'] is not None:
                    group['selections'][ingredient] = requirement['sku_id']
                group['selected'][ingredient] = requirement['selected']
            group_rows.append((group, requirements))
            public_groups.append({'group_id':group['group_id'], 'dish_id':dish['dish_id'], 'name':dish['name'], 'base_people':dish['base_people'], 'people':group['people'] or dish['base_people'], 'people_source':'explicit' if group['people'] is not None else 'default'})
            if group.get('source_group_id'):
                public_groups[-1]['source_group_id'] = group['source_group_id']
        requirements = merge_group_requirements(group_rows)
        from app.services.supply_service import supply_gaps, unresolved_gap
        unresolved, resolved = [], []
        for requirement in requirements:
            issue = requirement.get('supply_issue')
            if not issue and service.catalog.get_product(requirement['sku_id'])['offer_version'] is None:
                issue = 'availability_unknown'
            if issue:
                if requirement['selected']:
                    unresolved.append(unresolved_gap(requirement, issue))
            else:
                resolved.append(requirement)
        requirements = resolved
        rows, store, zone, total = self.facts(task, session, requirements, supply_preview=True, allow_quote=True)
        for row, requirement in zip(rows, requirements):
            row.update({key:value for key,value in requirement.items() if key not in ('quantity', 'selected', 'sku_id')})
            if row['coverage_quantity'] is not None:
                row['leftover_quantity'] = max(row['quantity'], row['added_quantity']) * row['spec_quantity'] - row['coverage_quantity']
        prior = json.loads(task.plan_json) if task.plan_json else None
        plan = {'plan_id':prior['plan_id'] if prior else f'plan-{uuid4().hex}', 'plan_version':prior['plan_version'] + 1 if prior else 1,
                'mode':'bundle', 'items':rows, 'total_price_fen':total, 'selected_total_fen':total,
                'expires_at':None, 'validation_status':'valid', 'can_confirm':any(row['selected'] and row['remaining_quantity'] for row in rows),
                'store_id':store.store_id, 'delivery_zone_id':zone, 'delivery_version':store.delivery_version,
                'displayed_message_id':displayed_message_id,
                'purchase_ledger':self.group_purchase_ledger(task_id),
                'groups':public_groups, 'targets':[{'group_id':group['group_id'], 'name':group['name']} for group in public_groups]}
        plan['gaps'] = unresolved + supply_gaps(rows, service.catalog, conditions, self.owner_id, task_id)
        plan['plan_kind'] = 'supply_preview' if plan['gaps'] else 'full_plan'
        if plan['gaps']:
            plan['can_confirm'] = False
        if len(public_groups) == 1:
            plan['dish'] = {key:value for key,value in public_groups[0].items() if key != 'group_id'}
            conditions['dish_selection'] = {key:value for key,value in groups[0].items() if key != 'group_id'}
        else:
            conditions.pop('dish_selection', None)
        conditions['dish_groups'] = groups
        task.conditions_json = json.dumps(conditions, ensure_ascii=False)
        task.state_version += 1
        task.current_step = 'awaiting_confirmation'
        from app.services.history_service import HistoryService
        HistoryService(self.db, self.owner_id).annotate(task, plan)
        self.project_budget(task, plan)
        task.plan_json = json.dumps(plan, ensure_ascii=False)
        self.db.flush()
        return plan

    def confirm(self, task_id, body, key, *, run_id=None, row_sku=None):
        """Never commit here: host commits cart + ledger + receipt + run together."""
        db = self.db
        cart = CartService(db, self.owner_id)
        cart.fence()
        digest = hashlib.sha256(json.dumps({'task_id':task_id, 'row_sku':row_sku, **body}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        prior = db.get(PurchaseConfirmation, (self.owner_id, key))
        if prior:
            if prior.digest != digest:
                raise AppError(409, 'IDEMPOTENCY_CONFLICT', '同一确认标识对应不同内容')
            return json.loads(prior.result_json)
        from app.core.business_mode import require_shopping_writes
        require_shopping_writes()
        db.expire_all()
        task, session = self.task(task_id)
        if (task.state_version, session.session_version) != (body['expected_state_version'], body['expected_session_version']):
            raise AppError(409, 'STALE_STATE', '清单或会话版本已变化')
        plan = json.loads(task.plan_json) if task.plan_json else None
        if not plan or (plan['plan_id'], plan['plan_version']) != (body['plan_id'], body['plan_version']):
            raise AppError(409, 'STALE_STATE', '清单版本已变化')
        if plan.get('budget_quote'):
            raise AppError(409, 'BUDGET_ACCEPTANCE_REQUIRED', '请先明确接受当前报价或修改方案，接受报价后仍需独立确认加购')
        if plan.get('plan_kind') == 'supply_preview':
            raise AppError(409, 'SUPPLY_SELECTION_REQUIRED', '请先明确选择替代或部分采购，再独立确认加购')
        displayed = db.get(GuideMessage, plan['displayed_message_id'])
        if not displayed or displayed.owner_id != self.owner_id or displayed.task_id != task_id:
            raise AppError(409, 'PLAN_NOT_DISPLAYED', '当前清单尚未展示')
        if run_id is not None:
            claimed = db.execute(update(GuideTurnReceipt).where(GuideTurnReceipt.run_id == run_id, GuideTurnReceipt.owner_id == self.owner_id, GuideTurnReceipt.session_id == session.session_id, GuideTurnReceipt.status == 'running').values(status='running'))
            if claimed.rowcount != 1:
                raise AppError(409, 'RUN_STOPPED', '确认处理已停止')
        expected = [{'sku_id':row['sku_id'], 'quantity':row['remaining_quantity']} for row in plan['items'] if row['selected'] and row['remaining_quantity'] > 0]
        if row_sku is not None:
            requested = body['selected_items']
            remaining = next((row['quantity'] for row in expected if row['sku_id'] == row_sku), 0)
            if len(requested) != 1 or requested[0]['sku_id'] != row_sku or not 0 < requested[0]['quantity'] <= remaining:
                raise AppError(409, 'CONFIRMATION_MISMATCH', '逐行加购数量超过当前选中行的剩余数量')
            expected = requested
        if not expected or sorted(body['selected_items'], key=lambda row:row['sku_id']) != sorted(expected, key=lambda row:row['sku_id']):
            raise AppError(409, 'CONFIRMATION_MISMATCH', '确认商品或剩余数量与展示清单不同')
        fresh, store, zone, total = self.facts(task, session, plan['items'])
        if (store.store_id, zone, store.delivery_version) != (plan['store_id'], plan['delivery_zone_id'], plan['delivery_version']):
            raise AppError(409, 'STALE_STATE', '配送条件已变化，请重新展示清单')
        if any((a['unit_price_fen'], a['offer_version'], a['remaining_quantity'], a['available_qty']) != (b['unit_price_fen'], b['offer_version'], b['remaining_quantity'], b['available_qty']) for a,b in zip(fresh, plan['items']) if b['selected']):
            raise AppError(409, 'STALE_STATE', '供给或已购数量已变化，请重新展示清单')
        version = cart.add_in_transaction(store.store_id, expected)
        increments = {row['sku_id']:row['quantity'] for row in expected}
        for row in plan['items']:
            if row['sku_id'] in increments:
                ledger = db.get(PurchaseLedger, (task_id, row['sku_id']))
                if ledger is None:
                    ledger = PurchaseLedger(task_id=task_id, sku_id=row['sku_id'], owner_id=self.owner_id, added_quantity=0)
                    db.add(ledger)
                ledger.added_quantity += increments[row['sku_id']]
                row['added_quantity'] = ledger.added_quantity
                row['remaining_quantity'] = max(0, row['quantity'] - ledger.added_quantity)
        task.state_version += 1
        task.current_step = 'awaiting_confirmation' if any(row['selected'] and row['remaining_quantity'] > 0 for row in plan['items']) else 'confirmed'
        result = {'operation_id':f'operation-{uuid4().hex}', 'confirmation_id':f'confirmation-{uuid4().hex}', 'status':'success',
                  'cart_version':version, 'items_added':expected, 'errors':[], 'task_id':task_id,
                  'state_version':task.state_version, 'session_version':session.session_version}
        if plan.get('groups'):
            result['group_purchases'] = []
            for row in plan['items']:
                if row['sku_id'] not in increments:
                    continue
                contributions = [item for item in row['contributions'] if item['selected']]
                group_ids = {item['group_id'] for item in contributions}
                result['group_purchases'].append({'operation_id':result['operation_id'], 'sku_id':row['sku_id'], 'name':row['name'], 'added_quantity':increments[row['sku_id']],
                                                 'groups':[group for group in plan['groups'] if group['group_id'] in group_ids], 'contributions':contributions})
        plan['can_confirm'] = any(row['selected'] and row['remaining_quantity'] > 0 for row in plan['items'])
        plan['confirmation_result'] = result
        task.plan_json = json.dumps(plan, ensure_ascii=False)
        db.add(PurchaseConfirmation(owner_id=self.owner_id, request_key=key, digest=digest, task_id=task_id, plan_id=plan['plan_id'], plan_version=plan['plan_version'], result_json=json.dumps(result, ensure_ascii=False)))
        db.flush()
        if plan.get('groups'):
            plan['purchase_ledger'] = self.group_purchase_ledger(task_id)
            task.plan_json = json.dumps(plan, ensure_ascii=False)
            db.flush()
        return result


    def revise(self, task_id, body):
        db = self.db
        CartService(db, self.owner_id).fence()
        task, session = self.task(task_id)
        key = 'revision:' + body['request_id']
        digest = hashlib.sha256(json.dumps({'task_id':task_id, **body}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        receipt = db.get(GuideCommandReceipt, (session.session_id, key))
        if receipt:
            if receipt.digest != digest:
                raise AppError(409, 'IDEMPOTENCY_CONFLICT', '同一修订标识对应不同内容')
            return json.loads(receipt.result_json)
        if (task.state_version, session.session_version) != (body['expected_state_version'], body['expected_session_version']):
            raise AppError(409, 'STALE_STATE', '清单或会话版本已变化')
        plan = json.loads(task.plan_json) if task.plan_json else None
        if not plan or (plan['plan_id'], plan['plan_version']) != (body['base_plan_id'], body['base_plan_version']):
            raise AppError(409, 'STALE_STATE', '清单版本已变化')
        message_id = f'msg-{uuid4().hex}'
        if body['coverage_intent'] == 'accept_quote':
            if not plan.get('budget_quote') or body['items'] or body['people'] is not None or body['selections'] or body.get('group_id') or body.get('gap_id') or body['alternative_index'] is not None:
                raise AppError(422, 'QUOTE_ACCEPTANCE_INVALID', '请明确接受当前展示的完整报价，不同时修改采购内容')
            rows, store, zone, total = self.facts(task, session, plan['items'], supply_preview=True, allow_quote=True)
            if (total != plan['budget_quote']['total_fen']
                or (store.store_id, zone, store.delivery_version) != (plan['store_id'], plan['delivery_zone_id'], plan['delivery_version'])
                or any((a['unit_price_fen'], a['offer_version'], a['available_qty'], a['available_to_add'], a['sellable'], a['remaining_quantity']) != (b['unit_price_fen'], b['offer_version'], b['available_qty'], b['available_to_add'], b['sellable'], b['remaining_quantity']) for a,b in zip(rows, plan['items']) if b['selected'])):
                raise AppError(409, 'STALE_STATE', '报价或供给已变化，请重新展示后接受')
            conditions = json.loads(task.conditions_json)
            conditions['budget_fen'] = total
            conditions.get('history_memory_defaults', {}).pop('budget_fen', None)
            task.conditions_json = json.dumps(conditions, ensure_ascii=False)
            plan.update(plan_version=plan['plan_version'] + 1, displayed_message_id=message_id,
                        can_confirm=plan.get('plan_kind') != 'supply_preview' and any(row['selected'] and row['remaining_quantity'] > 0 for row in rows))
            task.state_version += 1
            task.current_step = 'awaiting_confirmation'
        elif body['coverage_intent'] == 'choose_alternative':
            from app.services.supply_service import project_alternative
            from app.services.catalog_service import CatalogService
            gap = next((gap for gap in plan.get('gaps', []) if gap['gap_id'] == body['gap_id']), None)
            index = body['alternative_index']
            if plan.get('plan_kind') != 'supply_preview' or gap is None or index is None or index >= len(gap['alternatives']) or body['items'] or body['people'] is not None or body['selections'] or body.get('group_id'):
                raise AppError(422, 'SUPPLY_SELECTION_INVALID', '请选择当前预览中明确展示的兼容规格组合')
            source = next(row for row in plan['items'] if row['sku_id'] == gap['sku_id'])
            requested = project_alternative(plan['items'], source, gap['alternatives'][index], CatalogService(db, plan['store_id']))
            conditions = json.loads(task.conditions_json)
            for group in conditions['dish_groups']:
                if group['group_id'] not in gap['group_ids']:
                    continue
                ingredient = gap['ingredient_id']
                portions = [{'sku_id':row['sku_id'], 'quantity':sum(item['requirement']['quantity'] for item in row['contributions'] if item['group_id'] == group['group_id'] and item['selected'])} for row in requested if row['ingredient_id'] == ingredient]
                portions = [portion for portion in portions if portion['quantity'] > 0]
                group['selections'][ingredient] = portions[0]['sku_id']
                if len(portions) == 1:
                    group.get('pack_allocations', {}).pop(ingredient, None)
                else:
                    total_amount = sum(portion['quantity'] for portion in portions)
                    group.setdefault('pack_allocations', {})[ingredient] = [{'sku_id':portion['sku_id'],'fraction':portion['quantity']/total_amount} for portion in portions]
            if plan.get('dish'):
                conditions['dish_selection'] = {key:value for key,value in conditions['dish_groups'][0].items() if key != 'group_id'}
            task.conditions_json = json.dumps(conditions, ensure_ascii=False)
            rows, store, zone, total = self.facts(task, session, requested, supply_preview=True, allow_quote=True)
            for row, original in zip(rows, requested):
                for field in ('ingredient_id', 'role', 'requirement', 'coverage_quantity', 'available_specs', 'contributions', 'leftover_quantity'):
                    if field in original:
                        row[field] = original[field]
            from app.services.supply_service import supply_gaps
            remaining_gaps = [g for g in plan['gaps'] if g['sku_id'] not in {row['sku_id'] for row in plan['items']}]
            remaining_gaps += supply_gaps(rows, CatalogService(db, plan['store_id']), conditions, self.owner_id, task_id)
            plan.update(items=rows, gaps=remaining_gaps, plan_kind='supply_preview' if remaining_gaps else 'full_plan',
                        plan_version=plan['plan_version'] + 1, total_price_fen=total, selected_total_fen=total,
                        can_confirm=not remaining_gaps and any(row['selected'] and row['remaining_quantity'] > 0 for row in rows),
                        store_id=store.store_id, delivery_zone_id=zone, delivery_version=store.delivery_version, displayed_message_id=message_id)
            task.state_version += 1
            task.current_step = 'awaiting_confirmation'
        elif body['coverage_intent'] == 'choose_partial':
            if plan.get('plan_kind') != 'supply_preview' or body['items'] or body['people'] is not None or body['selections'] or body.get('group_id'):
                raise AppError(422, 'SUPPLY_SELECTION_INVALID', '请明确选择当前供给预览中的可售部分')
            requested = []
            for row in plan['items']:
                available = row['available_to_add'] if row['sellable'] else 0
                quantity = row['added_quantity'] + min(row['remaining_quantity'], available)
                requested.append({**row, 'quantity':quantity if quantity else row['quantity'], 'selected':row['selected'] and quantity > row['added_quantity']})
            rows, store, zone, total = self.facts(task, session, requested, allow_quote=True)
            for row, source in zip(rows, requested):
                for field in ('ingredient_id', 'role', 'requirement', 'coverage_quantity', 'available_specs', 'contributions', 'leftover_quantity'):
                    if field in source:
                        row[field] = source[field]
            for row in rows:
                if row.get('coverage_quantity') is not None:
                    row['leftover_quantity'] = max(row['added_quantity'], row['quantity'] if row['selected'] else 0) * row['spec_quantity'] - row['coverage_quantity']
            plan.update(items=rows, plan_kind='partial_purchase', plan_version=plan['plan_version'] + 1,
                        total_price_fen=total, selected_total_fen=total,
                        can_confirm=any(row['selected'] and row['remaining_quantity'] > 0 for row in rows),
                        store_id=store.store_id, delivery_zone_id=zone, delivery_version=store.delivery_version,
                        displayed_message_id=message_id)
            task.state_version += 1
            task.current_step = 'awaiting_confirmation'
        elif body['coverage_intent'] in ('dish_update', 'group_update', 'group_remove'):
            groups = plan.get('groups', [])
            if body['coverage_intent'] == 'dish_update':
                if not plan.get('dish') or body.get('group_id'):
                    raise AppError(422, 'DISH_REVISION_INVALID', '请明确当前菜品分组')
                group = groups[0] if groups else plan['dish']
            else:
                group = next((item for item in groups if item['group_id'] == body.get('group_id')), None)
                if group is None:
                    raise AppError(422, 'DISH_GROUP_UNKNOWN', '菜品分组不存在')
            removing = body['coverage_intent'] == 'group_remove'
            if body['items'] or (removing and (body['people'] is not None or body['selections'])) or (not removing and body['people'] is None and not body['selections']):
                raise AppError(422, 'DISH_REVISION_INVALID', '请指定分组的新人数、规格或移除操作')
            plan = self.prepare_dish(task_id, {'dish_id':group['dish_id'], 'group_id':group.get('group_id'), 'operation':'remove' if removing else 'update', 'people':body['people'], 'selections':body['selections']}, message_id)
        else:
            if plan.get('plan_kind') == 'supply_preview':
                raise AppError(409, 'SUPPLY_SELECTION_REQUIRED', '请先明确选择替代或部分采购')
            if body['people'] is not None or body['selections'] or body.get('group_id'):
                raise AppError(422, 'PLAN_SELECTION_INVALID', '人数或规格修改需要菜谱修订')
            if len(body['items']) != len(plan['items']) or {row['sku_id'] for row in body['items']} != {row['sku_id'] for row in plan['items']}:
                raise AppError(422, 'PLAN_SELECTION_INVALID', '改选只能修改当前清单商品；新商品需要先明确选定')
            prior_rows = {row['sku_id']:row for row in plan['items']}
            requested = []
            for item in body['items']:
                prior = prior_rows[item['sku_id']]
                source = {**prior, **item}
                if prior.get('contributions'):
                    source['contributions'] = [dict(contribution) for contribution in prior['contributions']]
                    if item['selected'] != prior['selected']:
                        from app.services.dish_service import recalculate_contribution_demand
                        previous_demand = dict(prior)
                        recalculate_contribution_demand(previous_demand)
                        for contribution in source['contributions']:
                            contribution['selected'] = item['selected']
                        recalculate_contribution_demand(source)
                        # Preserve a separately chosen package count. Otherwise
                        # a deliberate shared-row toggle uses its new full demand.
                        if item['quantity'] != prior['quantity'] or prior['quantity'] != previous_demand['quantity']:
                            source['quantity'] = item['quantity']
                requested.append(source)
            rows, store, zone, total = self.facts(task, session, requested, allow_quote=True)
            for row, source in zip(rows, requested):
                for field in ('ingredient_id', 'role', 'requirement', 'coverage_quantity', 'available_specs', 'contributions'):
                    if field in source:
                        row[field] = source[field]
                if 'coverage_quantity' in source:
                    row['leftover_quantity'] = max(row['quantity'], row['added_quantity']) * row['spec_quantity'] - source['coverage_quantity'] if source['coverage_quantity'] is not None else None
            plan.update(items=rows, plan_version=plan['plan_version'] + 1, total_price_fen=total, selected_total_fen=total,
                        can_confirm=any(row['selected'] and row['remaining_quantity'] > 0 for row in rows),
                        store_id=store.store_id, delivery_zone_id=zone, delivery_version=store.delivery_version,
                        displayed_message_id=message_id)
            if plan.get('groups'):
                conditions = json.loads(task.conditions_json)
                groups = {group['group_id']:group for group in conditions['dish_groups']}
                for row in rows:
                    for contribution in row['contributions']:
                        groups[contribution['group_id']]['selected'][contribution['ingredient_id']] = contribution['selected']
                if plan.get('dish'):
                    conditions['dish_selection'] = {key:value for key,value in conditions['dish_groups'][0].items() if key != 'group_id'}
                task.conditions_json = json.dumps(conditions, ensure_ascii=False)
            elif plan.get('dish'):
                conditions = json.loads(task.conditions_json)
                conditions['dish_selection']['selected'] = {row['ingredient_id']:row['selected'] for row in rows}
                task.conditions_json = json.dumps(conditions, ensure_ascii=False)
            task.state_version += 1
            task.current_step = 'awaiting_confirmation'
        self.project_budget(task, plan)
        plan.pop('confirmation_result', None)
        from app.services.history_service import HistoryService
        HistoryService(self.db, self.owner_id).annotate(task, plan)
        task.plan_json = json.dumps(plan, ensure_ascii=False)
        sequence = db.scalar(select(func.max(GuideMessage.sequence)).where(GuideMessage.session_id == session.session_id)) or 0
        db.add(GuideMessage(message_id=message_id, session_id=session.session_id, owner_id=self.owner_id, task_id=task_id,
                            sequence=sequence + 1, role='assistant', kind='plan', content=render_plan(plan), request_id=key))
        result = {**plan, 'state_version':task.state_version, 'session_version':session.session_version}
        db.add(GuideCommandReceipt(session_id=session.session_id, request_id=key, digest=digest, result_json=json.dumps(result, ensure_ascii=False)))
        db.flush()
        return result

"""Supply-derived choices stored in their original guide message, not a workflow store."""
import hashlib
import json
from uuid import uuid4
from sqlalchemy import select
from app.core.errors import AppError
from app.models.guide import GuideMessage, GuideTask
from app.services.catalog_service import CatalogService
from app.services.product_constraints import drink_filter_values, drink_filter_mismatch
from app.services.pi_product_turn_service import owned_session, session_anchor


def supply_fingerprint(products):
    return hashlib.sha256(json.dumps(products, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ProductQuestionService:
    def __init__(self, db, owner_id):
        self.db, self.owner_id = db, owner_id

    def explore(self, session_id, arguments):
        session = owned_session(self.db, self.owner_id, session_id)
        anchor = session_anchor(self.db, session)
        if not anchor[1]:
            raise AppError(409, 'NO_ACTIVE_TASK', '请先明确购买目标')
        answered_question_id = arguments.get('answer_question_id')
        answered_option_ids = []
        if answered_question_id:
            current = self.projection(session_id)['active_question']
            if not current or current['question_id'] != answered_question_id or current['kind'] != 'category':
                raise AppError(409, 'QUESTION_STALE', '文字回答所指的问题已失效')
            answered_option_ids = [o['option_id'] for o in current['options'] if o['value'] == arguments.get('product_type')]
            if len(answered_option_ids) != 1:
                raise AppError(422, 'QUESTION_OPTION_INVALID', '文字回答必须对应当前已展示的类型')
        arguments = {key:value for key,value in arguments.items() if key != 'answer_question_id'}
        task = self.db.get(GuideTask, anchor[1])
        conditions = json.loads(task.conditions_json)
        store_id = session.supply_store_id or json.loads(session.entry_context_json)['store_id']
        catalog = CatalogService(self.db, store_id)
        products, page, safety_reasons = [], 1, set()
        while True:
            rows, total = catalog.search_products(category_id=arguments.get('category_id') if conditions.get('activity_id') else arguments['category_id'], q=conditions.get('query') or arguments.get('query'), page=page, page_size=100)
            for product in rows:
                from app.services.activity_service import activity_mismatch
                if activity_mismatch(product, conditions):
                    continue
                from app.services.product_constraints import safety_mismatch
                safety_reason = safety_mismatch(product, conditions)
                if safety_reason:
                    safety_reasons.add(safety_reason)
                    continue
                if drink_filter_mismatch(product, conditions):
                    continue
                if not product['sellable'] or product['available_qty'] < conditions.get('quantity', 1):
                    continue
                if conditions.get('budget_fen') is not None and product['price_fen'] * conditions.get('quantity', 1) > conditions['budget_fen']:
                    continue
                if (conditions.get('product_type') or arguments.get('product_type')) and product['product_type'] != (conditions.get('product_type') or arguments.get('product_type')):
                    continue
                if conditions.get('brand') and product['brand'] != conditions['brand']:
                    continue
                if conditions.get('packaging') and product['metadata'].get('packaging') != conditions['packaging']:
                    continue
                packs = product['metadata'].get('pack_count')
                if conditions.get('pack_count_mode') == 'single' and packs != 1:
                    continue
                if conditions.get('pack_count_mode') == 'multi' and (packs is None or packs <= 1):
                    continue
                identities = [product['sku_id'], product['name'], product['name_zh'], product['brand'], *product['ingredient_ids'], *product['usage_tags']]
                if any(excluded in identities for excluded in conditions.get('exclusions', [])):
                    continue
                products.append(product)
            if page * 100 >= total:
                break
            page += 1
        types = {p['product_type']:p['metadata'].get('type_label') for p in products if p['product_type'] and p['metadata'].get('type_label')}
        kind = 'category' if not conditions.get('activity_id') and not arguments.get('product_type') and len(types) > 1 else 'products'
        options = [{'option_id':f'option-{uuid4().hex}', 'label':label, 'value':value} for value, label in sorted(types.items())] if kind == 'category' else [{'option_id':f'option-{uuid4().hex}', 'label':p['name_zh'] or p['name'], 'value':p['sku_id'], 'product':p} for p in products]
        question = ('想看哪类饮品？' if arguments.get('category_id') == 'beverage' else '想看哪类零食？') if kind == 'category' else '请选择商品和销售包装数量，选定后再核对清单。'
        if not products:
            question = '当前条件下没有可售的匹配商品。' + ''.join(sorted(safety_reasons)) + '原条件已保留；你可以告诉我是否调整预算或其他可调整条件。'
        filters = []
        if arguments.get('category_id') == 'beverage' and kind == 'products':
            labels = {'brand':'品牌', 'flavor':'口味', 'packaging':'包装', 'spec':'规格'}
            for attribute, label in labels.items():
                values = []
                for product in products:
                    value = drink_filter_values(product)[attribute]
                    if value is not None and value not in values:
                        values.append(value)
                for value in values:
                    if value == conditions.get(attribute):
                        continue
                    display = f"{value['quantity']:g}{value['unit']}" if attribute == 'spec' else {'can':'罐装','bottle':'瓶装'}.get(value, value)
                    filters.append({'option_id':f'filter-{uuid4().hex}', 'label':f'{label}：{display}', 'attribute':attribute, 'value':value})
                if conditions.get(attribute) is not None:
                    filters.append({'option_id':f'filter-{uuid4().hex}', 'label':f'取消{label}筛选', 'attribute':attribute, 'value':None})
        return {**({'known_total_quantity':conditions['quantity']} if conditions.get('quantity') is not None else {}), 'filter_options':filters, 'kind':kind, 'question':question, 'options':options, 'products':products, 'arguments':arguments, 'supply_fingerprint':supply_fingerprint(products), 'answered_question_id':answered_question_id, 'answered_option_ids':answered_option_ids}

    def publish(self, session_id, exploration, message_id):
        session = owned_session(self.db, self.owner_id, session_id)
        anchor = session_anchor(self.db, session)
        current = self.projection(session_id)['active_question']
        if current:
            old = self.db.get(GuideMessage, current['question_id'])
            saved = json.loads(old.content)
            is_answer = exploration.get('answered_question_id') == current['question_id']
            saved['status'] = 'answered' if is_answer else 'stale'
            saved['selected_option_ids'] = exploration.get('answered_option_ids', []) if is_answer else []
            old.content = json.dumps(saved, ensure_ascii=False)
        exploration = {key:value for key,value in exploration.items() if key not in ('answered_question_id', 'answered_option_ids')}
        return {**exploration, 'question_id':message_id, 'session_id':session_id, 'task_id':anchor[1], 'session_version':anchor[0], 'state_version':anchor[2], 'status':'active', 'selected_option_ids':[]}

    def projection(self, session_id):
        session = owned_session(self.db, self.owner_id, session_id)
        anchor = session_anchor(self.db, session)
        rows = self.db.scalars(select(GuideMessage).where(GuideMessage.session_id == session_id, GuideMessage.owner_id == self.owner_id, GuideMessage.kind == 'question').order_by(GuideMessage.sequence)).all()
        history = []
        for row in rows:
            saved = json.loads(row.content)
            question = {key:value for key,value in saved.items() if key not in ('products', 'arguments', 'supply_fingerprint')}
            if question['status'] == 'active' and (question['session_version'], question['task_id'], question['state_version']) != anchor:
                question['status'] = 'stale'
            if question['status'] == 'active':
                fresh = self.explore(session_id, saved['arguments'])
                if fresh['supply_fingerprint'] != saved['supply_fingerprint']:
                    question['status'] = 'stale'
            history.append(question)
        active = next((q for q in reversed(history) if q['status'] == 'active'), None)
        return {'active_question':active, 'question_history':history}

    def answer(self, session_id, question_id, body):
        from sqlalchemy import func, update
        from app.models.guide import GuideSession, GuideCommandReceipt
        from app.services.guide_lifecycle_service import require_canonical_session
        from app.services.purchase_service import PurchaseService, render_plan
        owned_session(self.db, self.owner_id, session_id)
        require_canonical_session(self.db, self.owner_id, session_id)
        digest = supply_fingerprint({'question_id':question_id, **body})
        self.db.execute(update(GuideSession).where(GuideSession.session_id == session_id, GuideSession.owner_id == self.owner_id).values(session_version=GuideSession.session_version))
        receipt = self.db.get(GuideCommandReceipt, (session_id, body['request_id']))
        if receipt:
            if receipt.digest != digest:
                raise AppError(409, 'IDEMPOTENCY_CONFLICT', '同一请求对应不同选择')
            return json.loads(receipt.result_json)
        self.db.expire_all()
        session = owned_session(self.db, self.owner_id, session_id)
        anchor = session_anchor(self.db, session)
        if anchor != (body['expected_session_version'], body['expected_task_id'], body['expected_state_version']):
            raise AppError(409, 'STALE_STATE', '购买任务或条件已变化，请查看当前问题')
        row = self.db.get(GuideMessage, question_id)
        current = self.projection(session_id)['active_question']
        if row is None or row.owner_id != self.owner_id or row.session_id != session_id or row.kind != 'question' or not current or current['question_id'] != question_id:
            raise AppError(409, 'QUESTION_STALE', '这个问题已回答或失效，请查看当前问题')
        saved = json.loads(row.content)
        fresh = self.explore(session_id, saved['arguments'])
        if fresh['supply_fingerprint'] != saved['supply_fingerprint']:
            raise AppError(409, 'QUESTION_SUPPLY_CHANGED', '商品报价或库存已变化，请重新查询后选择')
        options = {option['option_id']:option for option in saved['options']}
        filter_options = {option['option_id']:option for option in saved.get('filter_options', [])}
        selected = body['option_ids']
        if not selected or len(selected) != len(set(selected)) or any(oid not in options and oid not in filter_options for oid in selected):
            raise AppError(422, 'QUESTION_OPTION_INVALID', '请选择这个问题中实际展示的选项')
        is_filter = any(oid in filter_options for oid in selected)
        if is_filter and (saved['kind'] != 'products' or len(selected) != 1 or body['quantities']):
            raise AppError(422, 'QUESTION_OPTION_INVALID', '筛选只能选择一个已展示属性，不能同时选品或加购')
        if saved['kind'] == 'category' and (len(selected) != 1 or body['quantities']):
            raise AppError(422, 'QUESTION_OPTION_INVALID', '分类问题只能选一个类型，不代表选品或加购')
        task = self.db.get(GuideTask, anchor[1])
        assistant_id = f'msg-{uuid4().hex}'
        sequence = self.db.scalar(select(func.max(GuideMessage.sequence)).where(GuideMessage.session_id == session_id)) or 0
        if is_filter or saved['kind'] == 'category':
            conditions = json.loads(task.conditions_json)
            if is_filter:
                chosen = filter_options[selected[0]]
                conditions[chosen['attribute']] = chosen['value']
            else:
                conditions['product_type'] = options[selected[0]]['value']
            task.conditions_json = json.dumps(conditions, ensure_ascii=False)
            task.state_version += 1
            task.plan_json = None
            task.current_step = 'understanding'
            self.db.flush()
            arguments = {**saved['arguments']}
            if conditions.get('product_type'):
                arguments['product_type'] = conditions['product_type']
            next_question = self.publish(session_id, self.explore(session_id, arguments), assistant_id)
            content, kind = json.dumps(next_question, ensure_ascii=False), 'question'
        else:
            if set(body['quantities']) != set(selected):
                raise AppError(422, 'QUANTITY_REQUIRED', '请为每个选定商品填写销售包装数量')
            items = [{'sku_id':options[oid]['value'], 'quantity':body['quantities'][oid]} for oid in selected]
            plan = PurchaseService(self.db, self.owner_id).prepare_selected(task.task_id, items, assistant_id)
            content, kind = render_plan(plan), 'text'
        saved['status'], saved['selected_option_ids'] = 'answered', selected
        saved['answered_quantities'] = body['quantities']
        row.content = json.dumps(saved, ensure_ascii=False)
        self.db.add(GuideMessage(message_id=f'msg-{uuid4().hex}', session_id=session_id, owner_id=self.owner_id, task_id=task.task_id, sequence=sequence+1, role='user', kind='selection', content='、'.join((filter_options if is_filter else options)[oid]['label'] for oid in selected), request_id=body['request_id']))
        self.db.add(GuideMessage(message_id=assistant_id, session_id=session_id, owner_id=self.owner_id, task_id=task.task_id, sequence=sequence+2, role='assistant', kind=kind, content=content, request_id=body['request_id']))
        self.db.flush()
        from app.api.guide import projection
        result = projection(self.db, session, include_messages=True)
        self.db.add(GuideCommandReceipt(session_id=session_id, request_id=body['request_id'], digest=digest, result_json=json.dumps(result, ensure_ascii=False)))
        return result

    def select_products(self, session_id, arguments):
        """Interpret only choices bound to the currently displayed product question."""
        current = self.projection(session_id)['active_question']
        if not current or current['question_id'] != arguments['question_id'] or current['kind'] not in ('products', 'quantity'):
            raise AppError(409, 'QUESTION_STALE', '选品问题已变化，请查看当前候选')
        saved = json.loads(self.db.get(GuideMessage, current['question_id']).content)
        options = {option['option_id']:option for option in saved['options']}
        selections = arguments['selections']
        ids = [item['option_id'] for item in selections]
        if not ids or len(ids) != len(set(ids)) or any(oid not in options for oid in ids):
            raise AppError(422, 'QUESTION_OPTION_INVALID', '选品必须来自这个问题中已展示的候选')
        conditions = json.loads(self.db.get(GuideTask, current['task_id']).conditions_json)
        quantities = {item['option_id']:item.get('quantity', saved.get('known_quantities', {}).get(item['option_id'], conditions.get('quantity') if len(ids) == 1 else None)) for item in selections}
        if any(quantity is not None and (type(quantity) is not int or quantity <= 0) for quantity in quantities.values()):
            raise AppError(422, 'QUANTITY_REQUIRED', '销售包装数量必须为正整数')
        if any(quantity is None for quantity in quantities.values()):
            new_options, known = [], {}
            for oid in ids:
                new_id = f'option-{uuid4().hex}'
                new_options.append({**options[oid], 'option_id':new_id})
                if quantities[oid] is not None:
                    known[new_id] = quantities[oid]
            return {'exploration':{**saved, 'kind':'quantity', 'question':'选定的商品各要几件销售包装？', 'options':new_options, 'known_quantities':known, 'answered_question_id':current['question_id'], 'answered_option_ids':ids}}
        return {'items':[{'sku_id':options[oid]['value'], 'quantity':quantities[oid]} for oid in ids], 'question_id':current['question_id'], 'option_ids':ids, 'quantities':quantities}

    def record_selection(self, selection):
        row = self.db.get(GuideMessage, selection['question_id'])
        saved = json.loads(row.content)
        saved['status'], saved['selected_option_ids'] = 'answered', selection['option_ids']
        saved['answered_quantities'] = selection['quantities']
        row.content = json.dumps(saved, ensure_ascii=False)

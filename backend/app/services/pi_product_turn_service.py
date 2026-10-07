"""Read-only Pi query with one authoritative final history/receipt transaction."""
from __future__ import annotations
import json
from uuid import uuid4
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from app.core.errors import AppError
from app.models.guide import GuideSession, GuideTask, GuideMessage, GuideTurnReceipt
from app.services.catalog_service import CatalogService
from app.services.pi_product_runtime import PiProductRuntime


def owned_session(db, owner_id, session_id):
    session = db.get(GuideSession, session_id)
    if session is None or session.owner_id != owner_id:
        raise AppError(403, 'SESSION_FORBIDDEN', '会话不可访问')
    return session


def session_anchor(db, session):
    task = db.get(GuideTask, session.current_task_id) if session.current_task_id else None
    if session.current_task_id and (task is None or task.owner_id != session.owner_id or task.session_id != session.session_id):
        raise AppError(403, 'SESSION_FORBIDDEN', '购买任务不可访问')
    return session.session_version, session.current_task_id, task.state_version if task else 0


def bounded_dialogue_context(db, owner_id, session_id, anchor, exclude_run_id=None):
    """Only the latest anchored host projection, never raw dialogue or memory text."""
    query = select(GuideTurnReceipt).join(GuideMessage, (GuideMessage.session_id == GuideTurnReceipt.session_id) & (GuideMessage.request_id == GuideTurnReceipt.request_id)).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.owner_id == owner_id, GuideMessage.owner_id == owner_id, GuideMessage.role == 'assistant', GuideMessage.kind != 'introduction')
    if exclude_run_id is not None:
        query = query.where(GuideTurnReceipt.run_id != exclude_run_id)
    prior = db.scalar(query.order_by(GuideMessage.sequence.desc()).limit(1))
    empty = {'pending_clarification': None, 'dish_candidates': []}
    if prior is None or prior.status not in ('completed', 'waiting_clarification', 'waiting_confirmation') or not prior.result_json:
        return empty
    result = json.loads(prior.result_json)
    if (result['session_version'], result['task_id'], result['state_version']) != anchor:
        return empty
    pending = result.get('pending_clarifications', [])
    return {'pending_clarification': pending[0] if pending else None, 'dish_candidates': result.get('dish_candidates', [])[:5]}


class PiProductTurnService:
    def __init__(self, db, owner_id):
        self.db, self.owner_id = db, owner_id

    def process(self, session_id, body, *, run_id, deadline, progress):
        db = self.db
        session = owned_session(db, self.owner_id, session_id)
        from app.services.guide_run_service import digest_body, append_event, publish_result, log_host_failure, run_cancelled
        digest = digest_body(body)
        receipt = db.get(GuideTurnReceipt, run_id)
        if receipt is None or receipt.owner_id != self.owner_id or receipt.session_id != session_id or receipt.digest != digest:
            raise AppError(409, 'IDEMPOTENCY_CONFLICT', '运行登记与输入不一致')
        original = json.loads(receipt.anchor_json)
        anchor = (original['session_version'], original['task_id'], original['state_version'])
        store_id = session.supply_store_id or json.loads(session.entry_context_json)['store_id']
        db.rollback()

        def assert_current(final=False):
            db.expire_all()
            current = owned_session(db, self.owner_id, session_id)
            current_anchor = session_anchor(db, current)
            if current_anchor[:2] != anchor[:2] or (final and current_anchor != anchor):
                db.rollback()
                raise AppError(409, 'STALE_STATE', '查询期间会话或购买任务已变化')
            db.rollback()

        def should_stop():
            if run_cancelled(run_id):
                return True
            db.expire_all()
            stopped = db.get(GuideTurnReceipt, run_id).status != 'running'
            db.rollback()
            return stopped

        def route_request(arguments):
            nonlocal anchor
            from app.services.guide_lifecycle_service import transition, task_projection
            kind = arguments['kind']
            if kind not in ('question', 'progress', 'new_goal', 'amend', 'continue', 'stop', 'abandon'):
                raise AppError(422, 'PI_ROUTE_INVALID', '消息相关性类型不受支持')
            if kind in ('new_goal', 'amend', 'continue', 'abandon'):
                result = transition(db, self.owner_id, session_id, {
                    'request_id': f'route-{run_id}', 'kind': kind,
                    'goal': arguments.get('goal'), 'conditions': arguments.get('conditions'),
                    'expected_session_version': anchor[0], 'expected_task_id': anchor[1], 'expected_state_version': anchor[2],
                })
                # This run caused an explicit semantic command; its *original*
                # admission anchor stays immutable on the durable receipt.
                anchor = (result['session_version'], result['task_id'], result['state_version'])
                progress('conditions_updated' if kind == 'amend' else 'understanding')
            elif kind == 'stop':
                db.execute(update(GuideTurnReceipt).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.owner_id == self.owner_id, GuideTurnReceipt.run_id != run_id, GuideTurnReceipt.status == 'running').values(status='stop_requested'))
                db.commit()
                result = {'message': '已停止当前处理，购买任务和已有方案仍保留。'}
            elif kind == 'progress':
                rows = db.scalars(select(GuideTurnReceipt).where(GuideTurnReceipt.session_id == session_id, GuideTurnReceipt.owner_id == self.owner_id, GuideTurnReceipt.run_id != run_id).order_by(GuideTurnReceipt.started_at.desc())).all()
                active = [row for row in rows if row.status in ('running', 'stop_requested')]
                result = {'message': '还在处理，已取得的结果会保留。' if active else '当前没有正在进行的处理。', 'runs': [{'run_id': row.run_id, 'status': row.status} for row in rows[:10]]}
                db.rollback()
            else:
                result = task_projection(db, owned_session(db, self.owner_id, session_id))
                db.rollback()
            if kind in ('continue', 'new_goal', 'amend'):
                result['categories'] = CatalogService(db, store_id).get_categories()
                db.rollback()
            if kind == 'question':
                result = {}  # General channel gets no merchant task or facts.
            return {**result, 'guide_request': True, 'kind': kind}

        history = db.scalars(select(GuideMessage).where(GuideMessage.session_id == session_id, GuideMessage.owner_id == self.owner_id, GuideMessage.role == 'assistant', GuideMessage.kind == 'general').order_by(GuideMessage.sequence.desc()).limit(20)).all()
        task = db.get(GuideTask, anchor[1]) if anchor[1] else None
        from app.services.memory_service import MemoryTurn, MemoryService, previous_guide_memory_refs
        memory_turn = MemoryTurn(db, self.owner_id, role='keke', source_id=run_id, source_text=body['message'])
        memory_context = MemoryService(db, self.owner_id).recall(role='keke', query=body['message'] + ' ' + (task.goal or '' if task else ''), current_conditions=json.loads(task.conditions_json) if task else {})
        from app.services.product_question_service import ProductQuestionService
        question_context = ProductQuestionService(db, self.owner_id).projection(session_id)['active_question']
        dialogue_context = bounded_dialogue_context(db, self.owner_id, session_id, anchor, run_id)
        context = {**dialogue_context, 'capability':body.get('_route_capability'), 'active_question':question_context, 'memory_list_refs':previous_guide_memory_refs(db, self.owner_id, session_id), 'memory':memory_context, 'has_active_task': task is not None, 'general_history': [row.content for row in reversed(history)]}
        db.rollback()
        from app.services.comparison_service import ComparisonService
        comparison_snapshot_refs = [card['ref'] for card in ComparisonService(db, self.owner_id).current(session_id)]
        context['comparison_candidates'] = [card for card in ComparisonService(db, self.owner_id).current(session_id, body.get('view_context')) if card['ref'] in body.get('displayed_candidate_refs', [])]
        db.rollback()
        from app.services.history_service import HistoryService, HistoryTurn
        from app.services.guide_lifecycle_service import task_projection
        history_turn = HistoryTurn(db, self.owner_id, session_id, body['message'])
        from app.services.product_question_service import ProductQuestionService
        questions = ProductQuestionService(db, self.owner_id)
        def activity_active():
            current = owned_session(db, self.owner_id, session_id)
            task = db.get(GuideTask, current.current_task_id) if current.current_task_id else None
            return bool(task and json.loads(task.conditions_json).get('activity_id'))

        def publish_interim(identity, text):
            assert_current(final=True)
            # A separate short transaction publishes history only. It cannot
            # commit pending shopping or memory changes in the runtime Session.
            with Session(db.get_bind()) as publication:
                fenced = publication.execute(update(GuideSession).where(
                    GuideSession.session_id == session_id, GuideSession.owner_id == self.owner_id,
                    GuideSession.session_version == anchor[0], GuideSession.current_task_id == anchor[1],
                ).values(session_version=GuideSession.session_version))
                if fenced.rowcount != 1:
                    raise AppError(409, 'STALE_STATE', '发布中途回复时会话已变化')
                if anchor[1] is not None:
                    task_fence = publication.execute(update(GuideTask).where(
                        GuideTask.task_id == anchor[1], GuideTask.owner_id == self.owner_id,
                        GuideTask.state_version == anchor[2],
                    ).values(state_version=GuideTask.state_version))
                    if task_fence.rowcount != 1:
                        raise AppError(409, 'STALE_STATE', '发布中途回复时购买条件已变化')
                receipt = publication.get(GuideTurnReceipt, run_id)
                if receipt.status != 'running' or run_cancelled(run_id):
                    return
                sequence = publication.scalar(select(func.max(GuideMessage.sequence)).where(GuideMessage.session_id == session_id)) or 0
                user = publication.scalar(select(GuideMessage).where(GuideMessage.session_id == session_id,
                    GuideMessage.owner_id == self.owner_id, GuideMessage.request_id == body['request_id'], GuideMessage.role == 'user'))
                if user is None:
                    sequence += 1
                    publication.add(GuideMessage(message_id=f'msg-{uuid4().hex}', session_id=session_id,
                        owner_id=self.owner_id, task_id=anchor[1], sequence=sequence, role='user',
                        kind='text', content=body['message'], request_id=body['request_id']))
                publication.add(GuideMessage(message_id=identity, session_id=session_id, owner_id=self.owner_id,
                    task_id=anchor[1], sequence=sequence+1, role='assistant', kind='interim', content=text, request_id=body['request_id']))
                append_event(publication, receipt, 'message.interim', {'message_id':identity, 'content':text})
                if run_cancelled(run_id):
                    return
                publication.commit()

        runtime = PiProductRuntime(CatalogService(db, store_id), assert_current, run_id=run_id, route_request=route_request, context=context, memory_command=memory_turn.prepare, product_search=lambda arguments: ComparisonService(db, self.owner_id).search(session_id, arguments, scope_to_page=False), comparison_search=lambda arguments: ComparisonService(db, self.owner_id).search(session_id, arguments, body.get('view_context')), candidate_resolve=lambda ref: ComparisonService(db, self.owner_id).resolve(session_id, ref, body.get('displayed_candidate_refs', []), body.get('view_context')), history_command=history_turn.prepare, explore_products=lambda arguments: questions.explore(session_id, arguments), select_question_products=lambda arguments: questions.select_products(session_id, arguments), activity_active=activity_active, publish_interim=publish_interim)
        try:
            progress('understanding')
            explicit_confirm = body['message'].strip().rstrip('。！!') in ('就按这个加购', '确认加购', '确认把当前清单加入购物车')
            if explicit_confirm:
                outcome = {'status':'completed', 'message':'已按确认清单加入购物车（模拟业务）。', 'products':[]}
            elif body['message'].strip().rstrip('。！!') in ('好的', '可以'):
                outcome = {'status':'waiting', 'message':'你是要确认当前清单加购，还是继续修改？确认时请说“就按这个加购”。', 'products':[]}
            else:
                outcome = runtime.run(body['message'], should_stop=should_stop, on_phase=progress, deadline=deadline)
            if run_cancelled(run_id):
                raise AppError(409, 'RUN_INTERRUPTED', '这次处理已中断')
            assert_current(final=True)
            # This UPDATE locks the original session anchor in the SAME
            # transaction that inserts public history and final receipt.
            fenced = db.execute(update(GuideSession).where(
                GuideSession.session_id == session_id, GuideSession.owner_id == self.owner_id,
                GuideSession.session_version == anchor[0], GuideSession.current_task_id == anchor[1],
            ).values(session_version=GuideSession.session_version))
            if fenced.rowcount != 1:
                raise AppError(409, 'STALE_STATE', '提交回复时会话版本已变化')
            if anchor[1] is not None:
                fenced = db.execute(update(GuideTask).where(
                    GuideTask.task_id == anchor[1], GuideTask.owner_id == self.owner_id,
                    GuideTask.session_id == session_id, GuideTask.state_version == anchor[2],
                ).values(state_version=GuideTask.state_version))
                if fenced.rowcount != 1:
                    raise AppError(409, 'STALE_STATE', '提交回复时任务版本已变化')
            db.expire_all()
            receipt = db.get(GuideTurnReceipt, run_id)
            if run_cancelled(run_id) or receipt.status == 'interrupted':
                raise AppError(409, 'RUN_INTERRUPTED', '这次处理已中断')
            if receipt.status == 'stop_requested':
                outcome = runtime._close('stopped')
            status = outcome['status']
            memory_result = memory_turn.commit() if status == 'completed' and outcome.get('memory_result') else None
            if memory_result:
                outcome['message'] = memory_result['message']
                outcome['messages'] = [memory_result['message']]
            confirmation = None
            if explicit_confirm and status == 'completed':
                from app.services.purchase_service import PurchaseService
                task = db.get(GuideTask, anchor[1]) if anchor[1] else None
                plan = json.loads(task.plan_json) if task and task.plan_json else None
                if plan is None:
                    raise AppError(409, 'NO_CURRENT_PLAN', '当前没有可确认的已展示清单')
                displayed = body.get('displayed_plan')
                current_display = {'task_id':anchor[1], 'plan_id':plan['plan_id'], 'plan_version':plan['plan_version'], 'state_version':anchor[2], 'session_version':anchor[0]}
                if displayed != current_display:
                    raise AppError(409, 'DISPLAYED_PLAN_STALE', '你看到的清单已变化或尚未展示，请重新查看清单后确认')
                confirm_body = {'plan_id':plan['plan_id'], 'plan_version':plan['plan_version'], 'expected_state_version':anchor[2], 'expected_session_version':anchor[0],
                                'selected_items':[{'sku_id':row['sku_id'], 'quantity':row['remaining_quantity']} for row in plan['items'] if row['selected'] and row['remaining_quantity'] > 0]}
                confirmation = PurchaseService(db, self.owner_id).confirm(anchor[1], confirm_body, f'text:{run_id}', run_id=run_id)
                anchor = (anchor[0], anchor[1], confirmation['state_version'])
            assistant_id = f'msg-{uuid4().hex}'
            history_result = outcome.get('history_result') if status == 'completed' else None
            history_selection = history_result.get('selection') if history_result else None
            if history_selection:
                rebuilt = HistoryService(db, self.owner_id).select(session_id, {
                    'request_id':run_id, 'source_task_id':history_selection['source_task_id'],
                    'expected_task_id':anchor[1], 'expected_state_version':anchor[2], 'expected_session_version':anchor[0]},
                    memory_defaults=history_selection['memory_defaults'], memory_refs=history_selection['memory_refs'], displayed_message_id=assistant_id)
                anchor = (rebuilt['session_version'], rebuilt['task_id'], rebuilt['state_version'])
                outcome['message'] = rebuilt['message']
            elif history_result:
                outcome['message'] += '\n' + '\n'.join(f"{index+1}. {source['goal']}（{source['task_id']}）" for index, source in enumerate(history_result['sources']))
            sequence = db.scalar(select(func.max(GuideMessage.sequence)).where(GuideMessage.session_id == session_id)) or 0
            from app.services.purchase_service import PurchaseService, plan_actions, render_plan
            purchase = outcome.get('purchase_proposal') if status == 'completed' else None
            if purchase:
                if anchor[1] is None:
                    raise AppError(409, 'NO_ACTIVE_TASK', '请先明确购买任务')
                if purchase.get('comparison_ref'):
                    selected = ComparisonService(db, self.owner_id).resolve(session_id, purchase['comparison_ref'], body.get('displayed_candidate_refs', []), body.get('view_context'))
                    if selected['sku_id'] != purchase['sku_id']:
                        raise AppError(409, 'COMPARISON_STALE', '已展示候选发生变化，请重新比较')
                service = PurchaseService(db, self.owner_id)
                if purchase.get('question_selection'):
                    selection = questions.select_products(session_id, purchase['question_selection'])
                    plan = service.prepare_selected(anchor[1], selection['items'], assistant_id)
                    questions.record_selection(selection)
                else:
                    plan = service.prepare_dish(anchor[1], purchase, assistant_id) if 'dish_id' in purchase else service.prepare(anchor[1], purchase['sku_id'], purchase['quantity'], assistant_id)
                anchor = (anchor[0], anchor[1], db.get(GuideTask, anchor[1]).state_version)
                outcome['message'] = render_plan(plan)
            if status in ('deadline', 'tool_budget'):
                ComparisonService(db, self.owner_id).clear(session_id, comparison_snapshot_refs)
            cards = ComparisonService(db, self.owner_id).publish(session_id, outcome['products'], assistant_id, body.get('view_context')) if status == 'completed' and outcome.get('comparison') else []
            if outcome.get('policy_message'):
                outcome['messages'] = [outcome['message'], outcome['policy_message']]
            public_messages = [{'message_id': assistant_id if index == 0 else f'msg-{uuid4().hex}', 'content': content} for index, content in enumerate(outcome.get('messages', [outcome['message']]))]
            user = db.scalar(select(GuideMessage).where(GuideMessage.session_id == session_id,
                GuideMessage.owner_id == self.owner_id, GuideMessage.request_id == body['request_id'], GuideMessage.role == 'user'))
            assistant_offset = 1 if user is not None else 2
            if user is None:
                db.add(GuideMessage(message_id=f'msg-{uuid4().hex}', session_id=session_id, owner_id=self.owner_id, task_id=anchor[1], sequence=sequence + 1, role='user', kind='text', content=body['message'], request_id=body['request_id']))
            for index, message in enumerate(public_messages):
                db.add(GuideMessage(message_id=message['message_id'], session_id=session_id, owner_id=self.owner_id, task_id=anchor[1], sequence=sequence + index + assistant_offset, role='assistant', kind='general' if outcome.get('answer_kind') == 'general_explanation' else 'text', content=message['content'], request_id=body['request_id']))
            if outcome.get('exploration'):
                question = questions.publish(session_id, outcome['exploration'], assistant_id)
                db.flush()
                question_message = db.get(GuideMessage, assistant_id)
                question_message.kind = 'question'
                question_message.content = json.dumps(question, ensure_ascii=False)
                db.flush()
            task = db.get(GuideTask, anchor[1]) if anchor[1] else None
            retained_context = bounded_dialogue_context(db, self.owner_id, session_id, anchor, run_id) if status == 'completed' and runtime.route_result and runtime.route_result['kind'] in ('question', 'progress') else {}
            pending = [{'slot': outcome['clarification_slot'], 'question': outcome['message']}] if status == 'waiting' and outcome.get('clarification_slot') else ([retained_context['pending_clarification']] if retained_context.get('pending_clarification') else [])
            result = {
                'request_id': body['request_id'], 'session_id': session_id, 'task_id': anchor[1],
                'state_version': anchor[2], 'session_version': anchor[0],
                'status': 'stopped' if status == 'stopped' else (task.current_step if task else 'understanding'),
                'answer_status': 'failed' if status in ('deadline', 'tool_budget') else 'accepted',
                'message': outcome['message'], 'messages': public_messages, 'answer_kind': outcome.get('answer_kind', 'business_facts'), 'plan': json.loads(task.plan_json) if task and task.plan_json else None,
                'history_sources':history_result.get('sources', []) if history_result else [], 'history_reminder': task_projection(db, owned_session(db, self.owner_id, session_id))['history_reminder'],
                'plan_effect': 'replace' if purchase or history_selection else 'keep', 'pending_clarifications': pending, 'available_actions': plan_actions(json.loads(task.plan_json)) if task and task.plan_json else ['send_message'],
                'assistant_message_id': assistant_id, 'trace_id': run_id,
                'action_results': [confirmation] if confirmation else [memory_result] if memory_result else [], 'confirmation_result':confirmation, 'committed': bool(confirmation or (memory_result and memory_result['action'] != 'list')), 'runtime': 'pi-agent-core',
                'runtime_status': status, 'tool_rounds': runtime.tool_rounds,
                'dish_candidates': outcome.get('dish_candidates', retained_context.get('dish_candidates', [])), 'runtime_events': runtime.events, 'product_evidence': outcome['products'], 'product_cards':cards,
                'no_matches': outcome.get('no_matches', False),
                'model_mode': 'live', 'business_data_mode': 'demo',
            }
            result.update(questions.projection(session_id))
            receipt.status = {'stopped': 'stopped', 'waiting': 'waiting_clarification', 'deadline': 'protected', 'tool_budget': 'protected'}.get(status, 'completed')
            if status == 'completed' and (purchase or history_selection) and result['plan']:
                receipt.status = 'waiting_confirmation'
            receipt.result_json = json.dumps(result, ensure_ascii=False)
            if purchase or history_selection:
                append_event(db, receipt, 'plan.ready', {'plan':result['plan']})
            publish_result(db, receipt, result)
            if status == 'completed' and not memory_result:
                from app.services.memory_background import enqueue_extraction
                enqueue_extraction(db, owner_id=self.owner_id, role='keke', source_id=receipt.run_id, source_text=body['message'])
            db.commit()
            return result
        except Exception as exc:
            if not isinstance(exc, AppError):
                log_host_failure(run_id, exc)
            db.rollback()
            if run_cancelled(run_id):
                raise
            detail = exc.detail['error'] if isinstance(exc, AppError) else {'code': 'PI_QUERY_FAILED', 'message': 'Pi 查询失败'}
            failed = db.execute(update(GuideTurnReceipt).where(GuideTurnReceipt.run_id == run_id, GuideTurnReceipt.status.in_(['running', 'stop_requested'])).values(status='failed', result_json=json.dumps({**detail, 'http_status': exc.status_code if isinstance(exc, AppError) else 502})))
            if failed.rowcount:
                ComparisonService(db, self.owner_id).clear(session_id, comparison_snapshot_refs)
                receipt = db.get(GuideTurnReceipt, run_id)
                append_event(db, receipt, 'error', detail)
            db.commit()
            raise

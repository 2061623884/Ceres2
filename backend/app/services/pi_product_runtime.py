"""Pi stdio boundary. Python alone owns catalog facts and scoped references."""
from __future__ import annotations

import json
import hashlib
import logging
import re
import os
from pathlib import Path
import selectors
import subprocess
import time
from typing import Any, Callable
from uuid import uuid4

from app.core.config import get_settings
from app.core.errors import AppError
from app.services.catalog_service import CatalogService
from app.prompts.experience import keke_modules

MAX_TOOL_ROUNDS = 5
EXPLORATION_SECONDS = 30.0
LOGGER = logging.getLogger(__name__)
WORKER = Path(__file__).resolve().parents[3] / 'runtime' / 'pi' / 'dist' / 'worker.js'
ROLE_BOUNDARY_MESSAGE = '具体订单、退款或退货事项由墨墨处理。这里尚未查询订单资格，也未提交申请；你可以点击角色按钮前往墨墨。'


class PiProductRuntime:
    def __init__(self, catalog: CatalogService, assert_current: Callable[[], None], *, run_id: str, policy_scope: dict, route_request: Callable[[dict], dict], context: dict, memory_command: Callable[[dict], dict], product_search: Callable[[dict], tuple], comparison_search: Callable[[dict], tuple], candidate_resolve: Callable[[str], dict], history_command: Callable[[dict], dict], explore_products: Callable[[dict], dict], select_question_products: Callable[[dict], dict], activity_active: Callable[[], bool]):
        self.activity_active = activity_active
        self.select_question_products = select_question_products
        self.question_selections = {}
        self.explore_products = explore_products
        self.explorations = {}
        self.history_command = history_command
        self.history_results = {}
        self.policy_results = {}
        self.policy_attempts = []
        self.policy_scope = policy_scope
        self.policy_prefetch = None
        self.run_id = run_id
        self.route_request = route_request
        self.memory_command = memory_command
        self.product_search = product_search
        self.comparison_search = comparison_search
        self.candidate_resolve = candidate_resolve
        self.persisted_candidate_refs = set()
        self.comparison_requested = False
        self.comparison_refs = set()
        self.memory_results = {}
        self.context = context
        self.route_result = None
        self.general_candidates = {}
        self.approved_general = set()
        self.catalog = catalog
        self.assert_current = assert_current
        self.products: dict[str, dict[str, Any]] = {}
        self.proposals = {}
        self.dishes = {}
        self.dishes_searched = False
        self.events: list[dict[str, Any]] = []
        self.tool_rounds = 0
        self.searched = False
        self.diagnostic_id = f"pi-{uuid4().hex[:16]}"

    def _tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == 'select_question_products':
            if not self.route_result or self.route_result['kind'] not in ('new_goal', 'continue', 'amend'):
                raise AppError(422, 'PI_ROUTE_INVALID', '请先明确当前购买目标')
            result = self.select_question_products(arguments)
            ref = f'selection-{uuid4().hex}'
            self.question_selections[ref] = (arguments, result)
            return {**result, 'selection_ref':ref}
        if name == 'explore_products':
            if not self.route_result or self.route_result['kind'] not in ('new_goal', 'continue', 'amend'):
                raise AppError(422, 'PI_ROUTE_INVALID', '请先明确当前购买目标')
            result = self.explore_products(arguments)
            ref = f'exploration-{uuid4().hex}'
            self.explorations[ref] = result
            return {**result, 'exploration_ref':ref}
        if name == 'search_after_sales_policy':
            return self._query_policy(arguments['query'], arguments.get('category'), origin='tool')
        if name == 'history_command':
            result = self.history_command(arguments)
            self.history_results[result['history_ref']] = result
            return result
        if name == 'memory_command':
            result = self.memory_command(arguments)
            self.memory_results[result['memory_ref']] = result
            return result
        if name == 'guide_request':
            if self.route_result is not None or self.searched:
                raise AppError(422, 'PI_ROUTE_INVALID', '消息相关性只能在查询前登记一次')
            self.route_result = self.route_request(arguments)
            return self.route_result
        if name == 'validate_general_text':
            if not self.route_result or self.route_result['kind'] != 'question' or self.searched:
                raise AppError(422, 'PI_GENERAL_CHANNEL_FORBIDDEN', '普通解释不能承载商家查询上下文')
            messages = arguments['messages']
            if not isinstance(messages, list) or not messages or any(not isinstance(text, str) or not text.strip() for text in messages):
                raise AppError(422, 'PI_ANSWER_INVALID', '普通解释内容无效')
            ref = f'general-{uuid4().hex}'
            self.general_candidates[ref] = messages
            return {'general_ref': ref}
        if name == 'search_products':
            products, total = self.product_search(arguments)
            self.searched = True
            rows = []
            for product in products:
                ref = f'product-{uuid4().hex[:16]}'
                self.products[ref] = {**product, 'ref': ref}
                rows.append(self.products[ref])
            return {'products': rows, 'total': total, 'is_demo': True}
        if name == 'compare_products':
            self.comparison_requested = True
            products, total = self.comparison_search(arguments)
            self.searched = True
            self.products = {}
            for product in products:
                ref = f'product-{uuid4().hex[:16]}'
                self.products[ref] = {**product, 'ref':ref}
            self.comparison_refs = set(self.products)
            return {'products':list(self.products.values()), 'total':total, 'is_demo':True}
        if name == 'search_dishes':
            if self.activity_active():
                raise AppError(422, 'ACTIVITY_SCOPE_CONFLICT', '当前活动只选购成品；如需菜谱食材，请明确开始新的购买目标。')
            self.dishes_searched = True
            from app.services.dish_service import DishService
            service = DishService(self.catalog)
            rows = []
            for dish in service.search(arguments['query'])[:5]:
                ref = f'dish-{uuid4().hex}'
                self.dishes[ref] = dish
                rows.append({**dish, 'ref':ref, 'candidates':service.candidates(dish)})
            self.searched = True
            return {'dishes':rows, 'is_demo':True}
        if name == 'propose_dish':
            if self.activity_active():
                raise AppError(422, 'ACTIVITY_SCOPE_CONFLICT', '当前活动只选购成品；如需菜谱食材，请明确开始新的购买目标。')
            ref = arguments['dish_ref']
            people = arguments.get('people')
            if ref not in self.dishes or (people is not None and (type(people) is not int or people <= 0)):
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '菜谱必须来自本次查询，人数必须为正整数')
            if not self.route_result or self.route_result['kind'] not in ('new_goal', 'continue', 'amend'):
                raise AppError(422, 'PI_ROUTE_INVALID', '请先明确当前购买目标')
            proposal_ref = f'proposal-{uuid4().hex}'
            self.proposals[proposal_ref] = {'dish_id':self.dishes[ref]['dish_id'], 'people':people, 'selections':arguments.get('selections', {}), 'operation':arguments.get('operation', 'update'), 'group_id':arguments.get('group_id')}
            return {'proposal_ref':proposal_ref, 'message':'宿主将核对供给并准备完整方案或供给预览，尚未加购。'}
        if name == 'propose_purchase':
            ref, quantity = arguments['ref'], arguments['quantity']
            persisted_candidate = ref not in self.products
            if persisted_candidate:
                self.products[ref] = {**self.candidate_resolve(ref), 'ref':ref}
                self.persisted_candidate_refs.add(ref)
            if ref not in self.products or type(quantity) is not int or quantity <= 0:
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '清单必须引用本次已查询商品和正整数件数')
            if not self.route_result or self.route_result['kind'] not in ('new_goal', 'continue', 'amend'):
                raise AppError(422, 'PI_ROUTE_INVALID', '请先明确当前购买目标')
            proposal_ref = f'proposal-{uuid4().hex}'
            self.proposals[proposal_ref] = {'sku_id':self.products[ref]['sku_id'], 'quantity':quantity}
            if ref in self.persisted_candidate_refs:
                self.proposals[proposal_ref]['comparison_ref'] = ref
            return {'proposal_ref':proposal_ref, 'message':'选定商品仅准备清单，尚未加购。'}
        if name == 'product_details':
            ref = arguments['ref']
            if ref not in self.products:
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '商品引用不属于本次查询')
            product = self.catalog.get_product(self.products[ref]['sku_id'])
            if product is None:
                raise AppError(409, 'PI_PRODUCT_UNAVAILABLE', '商品已不再可查询')
            if self.activity_active() and not any(row['sku_id'] == product['sku_id'] for row in self.explore_products({})['products']):
                raise AppError(409, 'ACTIVITY_SCOPE_CONFLICT', '商品已不符合当前活动与购买条件，请重新查询。')
            self.products[ref] = {**product, 'ref': ref}
            return {'product': self.products[ref], 'is_demo': True}
        raise AppError(422, 'PI_TOOL_FORBIDDEN', '本次运行仅允许查询商品')

    def _query_policy(self, query, category, *, origin):
        from app.mercury.policy import search_policies, POLICY_SOURCE_VERSION, POLICY_SOURCE_NAME
        started = time.monotonic()
        # The Pi scheduler is sequential. Reuse only actual successful/empty
        # acquisitions in this trusted request, never a failed attempt.
        for evidence in self.policy_results.values():
            if (evidence['scope'] == self.policy_scope and evidence['query'] == query
                    and evidence['category'] == category and evidence['source_version'] == POLICY_SOURCE_VERSION):
                self.events.append({'type': 'policy_reuse', 'origin': origin, 'outcome': evidence['outcome'],
                                    'elapsed_ms': (time.monotonic() - started) * 1000,
                                    'source_version': POLICY_SOURCE_VERSION, 'policy_ref': evidence['policy_ref']})
                return {key: value for key, value in evidence.items() if key != 'scope'}
        evidence = {'request_id': self.policy_scope['request_id'], 'query': query,
                    'category': category, 'source_name': POLICY_SOURCE_NAME, 'source_version': POLICY_SOURCE_VERSION}
        try:
            result = search_policies(query, category)
        except Exception as exc:
            from app.services.guide_run_service import safe_failure_diagnostic
            LOGGER.warning('Policy fallback phase=policy_lookup run_id=%s request_id=%s causes=%s',
                           self.run_id, self.policy_scope['request_id'], safe_failure_diagnostic(exc))
            evidence.update(outcome='error', coverage='unknown', data=None, reason='lookup_failed')
            self.policy_attempts.append({**evidence, 'scope': dict(self.policy_scope)})
            self.events.append({'type': 'policy_lookup', 'origin': origin, 'outcome': 'error',
                                'elapsed_ms': (time.monotonic() - started) * 1000,
                                'source_version': POLICY_SOURCE_VERSION, 'reason': 'lookup_failed'})
            # A real tool call also returns its failed attempt to the same Pi;
            # it must remain able to finish the other parts of a mixed request.
            return evidence
        ref = f'policy-{uuid4().hex}'
        evidence.update(**result, policy_ref=ref, outcome='success' if result['data'] else 'empty',
                        coverage='partial' if result['data'] else 'none')
        # Owned by this Python runtime only; never reconstructed from model text.
        self.policy_results[ref] = {**evidence, 'scope': dict(self.policy_scope)}
        self.policy_attempts.append(self.policy_results[ref])
        self.events.append({'type': 'policy_lookup', 'origin': origin, 'outcome': evidence['outcome'],
                            'elapsed_ms': (time.monotonic() - started) * 1000,
                            'source_version': POLICY_SOURCE_VERSION, 'policy_ref': ref, 'reason': None})
        return evidence

    def prepare_policy(self, message: str, *, should_stop, on_phase, deadline):
        if should_stop():
            return self._close('stopped')
        if time.monotonic() >= deadline:
            return self._close('deadline')
        self.assert_current()
        if should_stop():
            return self._close('stopped')
        if time.monotonic() >= deadline:
            return self._close('deadline')
        from app.services.kev_provider import judge_policy, KevUnavailable, POLICY_CRITERIA_VERSION
        started = time.monotonic()
        reason = None
        try:
            decision, _raw = judge_policy({'message': message}, remaining_seconds=deadline - started)
        except KevUnavailable as exc:
            from app.services.guide_run_service import safe_failure_diagnostic
            decision, reason = exc.outcome, exc.reason
            LOGGER.warning('Policy fallback phase=policy_judgment run_id=%s request_id=%s causes=%s',
                           self.run_id, self.policy_scope['request_id'], safe_failure_diagnostic(exc))
        self.events.append({'type': 'policy_judgment', 'outcome': decision,
                            'elapsed_ms': (time.monotonic() - started) * 1000,
                            'reason': reason, 'rules_version': POLICY_CRITERIA_VERSION, 'usage': None})
        if should_stop():
            return self._close('stopped')
        if time.monotonic() >= deadline:
            return self._close('deadline')
        self.assert_current()
        if should_stop():
            return self._close('stopped')
        if time.monotonic() >= deadline:
            return self._close('deadline')
        if decision == 'yes':
            on_phase('retrieve')
            self.assert_current()
            if should_stop():
                return self._close('stopped')
            if time.monotonic() >= deadline:
                return self._close('deadline')
            self.policy_prefetch = self._query_policy(message, None, origin='prefetch')
            self.assert_current()
        if should_stop():
            return self._close('stopped')
        if time.monotonic() >= deadline:
            return self._close('deadline')
        return None

    def run(self, message: str, *, should_stop: Callable[[], bool], on_phase: Callable[[str], None], deadline: float) -> dict[str, Any]:
        if should_stop():
            return self._close('stopped')
        if time.monotonic() >= deadline:
            return self._close('deadline')
        settings = get_settings()
        if not settings.openai_base_url or not settings.openai_api_key or not settings.llm_model:
            raise AppError(503, 'PI_PROVIDER_UNCONFIGURED', 'Pi 模型配置不完整')
        if not WORKER.is_file():
            raise AppError(503, 'PI_WORKER_UNBUILT', 'Pi runtime 尚未构建')
        prepared = self.prepare_policy(message, should_stop=should_stop, on_phase=on_phase, deadline=deadline)
        if prepared is not None:
            return prepared
        categories = self.catalog.get_categories()
        self.assert_current()
        if should_stop():
            return self._close('stopped')
        if time.monotonic() >= deadline:
            return self._close('deadline')
        # The child gets no inherited API keys or database configuration.
        env = {key: os.environ[key] for key in ('PATH', 'SYSTEMROOT', 'HOME', 'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy', 'NODE_EXTRA_CA_CERTS') if key in os.environ}
        try:
            child = subprocess.Popen(['node', str(WORKER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        except OSError as exc:
            raise AppError(503, 'PI_WORKER_UNAVAILABLE', '无法启动 Pi runtime') from exc
        selector = selectors.DefaultSelector()
        selector.register(child.stdout, selectors.EVENT_READ, 'stdout')
        selector.register(child.stderr, selectors.EVENT_READ, 'stderr')
        stderr_tail = b''
        pending = b''
        input_sequence = 0
        output_sequence = 0
        def send(frame):
            nonlocal input_sequence
            input_sequence += 1
            frame = {**frame, 'run_id': self.run_id, 'sequence': input_sequence}
            child.stdin.write((json.dumps(frame, ensure_ascii=False) + '\n').encode())
            child.stdin.flush()
        try:
            self.assert_current()
            if should_stop():
                return self._close('stopped')
            if time.monotonic() >= deadline:
                return self._close('deadline')
            send({'type': 'start', 'message': message, 'categories': categories, 'context': self.context, 'policyEvidence': self.policy_prefetch, 'promptModules': keke_modules(), 'model': {'baseUrl': settings.openai_base_url, 'apiKey': settings.openai_api_key, 'id': settings.llm_model}, 'maxToolRounds': MAX_TOOL_ROUNDS, 'timeoutMs': max(1, int((deadline - time.monotonic()) * 1000))})
            while True:
                if should_stop():
                    return self._close('stopped')
                if time.monotonic() >= deadline:
                    return self._close('deadline')
                self.assert_current()
                if should_stop():
                    return self._close('stopped')
                if time.monotonic() >= deadline:
                    return self._close('deadline')
                ready = selector.select(timeout=min(0.05, max(0, deadline - time.monotonic())))
                if not ready:
                    if child.poll() is not None:
                        self._fail('PI_WORKER_EXITED', self._stderr_diagnostic(stderr_tail))
                    continue
                for key, _mask in sorted(ready, key=lambda item: item[0].data != 'stderr'):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if key.data == 'stderr':
                        stderr_tail = (stderr_tail + chunk)[-4096:]
                        if not chunk:
                            selector.unregister(key.fileobj)
                    elif not chunk:
                        self._fail('PI_PROTOCOL_EOF', self._stderr_diagnostic(stderr_tail))
                    else:
                        pending += chunk
                        if len(pending) > 262144:
                            raise AppError(502, 'PI_PROTOCOL_INVALID', 'Pi runtime 帧超出上限')
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    try:
                        frame = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise AppError(502, 'PI_PROTOCOL_INVALID', 'Pi runtime 协议错误') from exc
                    output_sequence += 1
                    if not isinstance(frame, dict) or frame.get('run_id') != self.run_id or frame.get('sequence') != output_sequence:
                        raise AppError(502, 'PI_PROTOCOL_INVALID', 'Pi runtime 运行关联或帧序号错误')
                    if frame['type'] == 'event':
                        self.events.append(frame['event'])
                        self.events = self.events[-256:]
                    elif frame['type'] == 'tool_call':
                        if should_stop():
                            return self._close('stopped')
                        if time.monotonic() >= deadline:
                            return self._close('deadline')
                        if frame['round'] > MAX_TOOL_ROUNDS:
                            return self._close('tool_budget')
                        self.tool_rounds = max(self.tool_rounds, frame['round'])
                        on_phase('speaking' if frame['name'] == 'validate_general_text' else 'understanding' if frame['name'] == 'guide_request' else 'retrieve')
                        # Both progress persistence and freshness reads can block.
                        # Recheck after them, before any ordinary tool/read starts.
                        self.assert_current()
                        if should_stop():
                            return self._close('stopped')
                        if time.monotonic() >= deadline:
                            return self._close('deadline')
                        result = self._tool(frame['name'], frame['arguments'])
                        self.assert_current()
                        if should_stop():
                            return self._close('stopped')
                        if time.monotonic() >= deadline:
                            return self._close('deadline')
                        send({'type': 'tool_result', 'id': frame['id'], 'result': result})
                    elif frame['type'] == 'general_validation':
                        ref = frame['general_ref']
                        if ref not in self.general_candidates or type(frame['approved']) is not bool:
                            raise AppError(502, 'PI_PROTOCOL_INVALID', '普通解释校验关联错误')
                        if not frame['approved']:
                            code = 'PI_GENERAL_VALIDATION_UNCERTAIN' if frame['reason'] == 'uncertain' else 'PI_UNGROUNDED_BUSINESS_TEXT'
                            raise AppError(422, code, '这段解释未通过事实边界核对，本次未展示。商家信息需要通过业务查询确认。')
                        self.approved_general.add(ref)
                    elif frame['type'] == 'result':
                        self.assert_current()
                        if should_stop():
                            return self._close('stopped')
                        if time.monotonic() >= deadline:
                            return self._close('deadline')
                        if frame['status'] in ('tool_budget', 'deadline', 'stopped'):
                            return self._close(frame['status'])
                        return self._answer(frame['answer'])
                    elif frame['type'] == 'error':
                        self._fail(frame['code'], frame['diagnostic'])
                    else:
                        raise AppError(502, 'PI_PROTOCOL_INVALID', 'Pi runtime 协议错误')
        finally:
            selector.close()
            if child.poll() is None:
                child.kill()
            child.wait()
            child.stdin.close()
            child.stdout.close()
            child.stderr.close()

    def _fail(self, code: str, diagnostic: dict[str, Any]) -> None:
        # This structured diagnostic is now public in SSE/receipts. Re-project
        # finite fields at the Python trust boundary; never expose raw text.
        kinds = {'Error', 'TypeError', 'SyntaxError', 'AbortError', 'ProviderError', 'WorkerProcessError'}
        codes = kinds | {'ECONNRESET', 'ECONNREFUSED', 'ENOTFOUND', 'EAI_AGAIN', 'ETIMEDOUT', 'CERT_HAS_EXPIRED', 'UNABLE_TO_VERIFY_LEAF_SIGNATURE', 'UND_ERR_CONNECT_TIMEOUT', 'UND_ERR_HEADERS_TIMEOUT', 'UND_ERR_BODY_TIMEOUT', 'UND_ERR_SOCKET', 'ERR_MODULE_NOT_FOUND', 'MODULE_NOT_FOUND', 'EACCES', 'ENOENT', 'WORKER_EXIT'}
        kind = diagnostic.get('kind')
        safe = {'diagnostic_id': self.diagnostic_id, 'kind': kind if isinstance(kind, str) and kind in kinds else 'Error'}
        supplied_code = diagnostic.get('code')
        safe['code'] = supplied_code if isinstance(supplied_code, str) and (supplied_code in codes or re.fullmatch(r'HTTP_[45]\d\d', supplied_code)) else 'Error'
        fingerprint = diagnostic.get('fingerprint')
        if isinstance(fingerprint, str) and re.fullmatch(r'[a-f0-9]{64}', fingerprint):
            safe['fingerprint'] = fingerprint
        status = diagnostic.get('upstream_http_status')
        safe['upstream_http_status'] = status if type(status) is int and 100 <= status <= 599 else None
        phase = diagnostic.get('transport_phase')
        safe['transport_phase'] = phase if isinstance(phase, str) and phase in {'not_started', 'request', 'response', 'fetch_error'} else 'not_started'
        error_class = diagnostic.get('transport_error_class')
        safe['transport_error_class'] = error_class if isinstance(error_class, str) and error_class in kinds else None
        error_code = diagnostic.get('transport_error_code')
        safe['transport_error_code'] = error_code if isinstance(error_code, str) and error_code in codes else None
        LOGGER.error("Pi failure %s %s", self.diagnostic_id, safe)
        cause = RuntimeError(json.dumps(safe))
        error = AppError(502, code, f"Pi 运行失败 [{self.diagnostic_id}; {safe['code']}]")
        error.detail['error']['diagnostic'] = safe
        raise error from cause

    @staticmethod
    def _stderr_diagnostic(raw: bytes) -> dict[str, str]:
        text = raw.decode('utf-8', errors='replace')
        marker = re.search(r'\b(ERR_MODULE_NOT_FOUND|MODULE_NOT_FOUND|SyntaxError|TypeError|EACCES|ENOENT)\b', text)
        return {'kind': 'WorkerProcessError', 'code': marker.group(1) if marker else 'WORKER_EXIT', 'fingerprint': hashlib.sha256(raw).hexdigest()}

    def _answer(self, raw: str) -> dict[str, Any]:
        try:
            answer = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AppError(502, 'PI_ANSWER_INVALID', 'Pi 回复不符合事实引用契约') from exc
        if not isinstance(answer, dict):
            raise AppError(502, 'PI_ANSWER_INVALID', 'Pi 回复必须为结构化对象')
        if 'role_boundary' in answer and type(answer['role_boundary']) is not bool:
            raise AppError(502, 'PI_ANSWER_INVALID', '售后职责标记必须为布尔值')
        outcome = self._answer_value(answer)
        # Every successful primary result may carry independently acquired
        # policy facts, including a clarification or an explicit memory result.
        if outcome['status'] in ('completed', 'waiting') and answer.get('answer_kind') != 'policy_result' and 'policy_ref' in answer:
            outcome['policy_message'] = self._policy_message(answer['policy_ref'])
        unavailable = self._policy_unavailable_message()
        if unavailable and not (answer.get('answer_kind') == 'policy_result' and 'policy_ref' not in answer):
            outcome['policy_message'] = '\n'.join(filter(None, (outcome.get('policy_message'), unavailable)))
        if answer.get('role_boundary') is True and answer.get('answer_kind') != 'role_boundary':
            outcome['role_boundary'] = True
            outcome['role_boundary_message'] = ROLE_BOUNDARY_MESSAGE
        return outcome

    def _policy_unavailable_message(self):
        # Projection only, not a cache: every requested lookup still executes.
        # A later success/empty resolves failure only for that exact real scope.
        latest = {}
        for attempt in self.policy_attempts:
            latest[(attempt['query'], attempt['category'], attempt['source_version'])] = attempt
        failures = [attempt for attempt in latest.values() if attempt['outcome'] == 'error']
        return '\n'.join(
            f"政策查询暂时失败，规则未知。查询范围：{json.dumps(attempt['query'], ensure_ascii=False)}；"
            f"类别：{attempt['category'] or '未指定'}；来源：{attempt['source_name']}（版本 {attempt['source_version']}）。"
            '具体订单资格尚未核实；未提交任何申请。'
            for attempt in failures)

    def _policy_message(self, ref):
        from app.mercury.policy import policy_summary, POLICY_SOURCE_VERSION
        if not isinstance(ref, str) or ref not in self.policy_results:
            raise AppError(422, 'PI_UNKNOWN_REFERENCE', '政策必须引用本次实际查询的规则')
        evidence = self.policy_results[ref]
        if evidence['scope'] != self.policy_scope or evidence['source_version'] != POLICY_SOURCE_VERSION:
            raise AppError(422, 'PI_UNKNOWN_REFERENCE', '政策引用的请求或来源版本已失效，请重新查询')
        text = policy_summary(evidence['data'])
        if evidence['outcome'] == 'empty':
            return f"{text} 来源：{evidence['source_name']}（版本 {evidence['source_version']}）。"
        return text + ' 本次仅展示检索命中的一般规则；未覆盖的条款或条件仍未知，不能视为完整问题已全部核实。'

    def _answer_value(self, answer):
        kind = answer.get('answer_kind')
        if kind == 'role_boundary':
            if not self.route_result or self.route_result['kind'] != 'question':
                raise AppError(422, 'PI_ROUTE_INVALID', '具体售后说明不能修改购买任务')
            return {'status': 'completed', 'answer_kind': 'role_boundary',
                    'message': ROLE_BOUNDARY_MESSAGE, 'role_boundary': True,
                    'products': []}
        if kind == 'question_selection':
            ref = answer.get('selection_ref')
            if not isinstance(ref, str) or ref not in self.question_selections:
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '选品必须引用本次核对结果')
            arguments, result = self.question_selections[ref]
            if result.get('exploration'):
                return {'status':'completed', 'message':result['exploration']['question'], 'products':[], 'exploration':result['exploration']}
            return {'status':'completed', 'message':'清单已准备好，请核对后明确确认加购。', 'products':[], 'purchase_proposal':{'question_selection':arguments}}
        if kind == 'exploration':
            ref = answer.get('exploration_ref')
            if not isinstance(ref, str) or ref not in self.explorations:
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '选择问题必须引用本次真实供给')
            result = self.explorations[ref]
            return {'status':'completed', 'message':result['question'], 'products':[], 'exploration':result}
        if kind == 'policy_result':
            if 'policy_ref' not in answer and (unavailable := self._policy_unavailable_message()):
                return {'status': 'completed', 'message': unavailable, 'products': []}
            return {'status':'completed', 'message':self._policy_message(answer.get('policy_ref')), 'products':[]}
        if kind == 'history_result':
            ref = answer.get('history_ref')
            if not isinstance(ref, str) or not self.history_results or ref != next(reversed(self.history_results)):
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '历史结果引用不属于本次请求')
            return {'status':'completed', 'message':self.history_results[ref]['message'], 'products':[], 'history_result':self.history_results[ref]}
        if kind == 'memory_result':
            ref = answer.get('memory_ref')
            if not isinstance(ref, str) or not self.memory_results or ref != next(reversed(self.memory_results)):
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '记忆结果引用不属于本次请求')
            return {'status':'completed', 'message':self.memory_results[ref]['message'], 'products':[], 'memory_result':self.memory_results[ref]}
        if kind == 'dish_candidates':
            refs = answer.get('dish_refs')
            if not isinstance(refs, list) or any(not isinstance(ref, str) or ref not in self.dishes for ref in refs):
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '菜品建议必须引用本次实际查询的菜谱')
            if not self.dishes_searched:
                raise AppError(422, 'PI_EVIDENCE_MISSING', '请先查询真实菜谱')
            dishes = [self.dishes[ref] for ref in dict.fromkeys(refs)][:5]
            candidates = [{'dish_id': dish['dish_id'], 'name': dish['name']} for dish in dishes]
            lines = ['可以考虑以下菜品，请选一道后再准备采购清单：'] if dishes else ['已查询到菜谱，但本次没有选定展示结果。' if self.dishes else '本次没有查到匹配菜谱。']
            lines.extend(f"{index + 1}. {dish['name']}" for index, dish in enumerate(dishes))
            if dishes:
                lines.append('尚未选定或加购；食材供给会在准备清单时核对，价格和库存为模拟数据。')
            return {'status': 'completed', 'message': '\n'.join(lines), 'products': [], 'dish_candidates': candidates}
        if kind == 'purchase_plan':
            if self.comparison_requested:
                raise AppError(422, 'COMPARISON_SELECTION_REQUIRED', '请先展示比较候选并由用户选定')
            ref = answer.get('proposal_ref')
            if not isinstance(ref, str) or ref not in self.proposals:
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '清单引用不属于本次提案')
            return {'status':'completed', 'message':'清单已准备好，请核对后确认加购。价格、库存和配送为模拟数据。', 'products':[], 'purchase_proposal':self.proposals[ref]}
        if kind == 'conversation':
            raise AppError(422, 'PI_GENERAL_VALIDATION_REQUIRED', '普通解释必须先核对再引用')
        if kind == 'general_explanation':
            ref = answer.get('general_ref')
            if not isinstance(ref, str) or ref not in self.approved_general:
                raise AppError(422, 'PI_UNKNOWN_REFERENCE', '普通解释引用未通过本次校验')
            messages = self.general_candidates[ref]
            return {'status': 'completed', 'answer_kind': 'general_explanation', 'message': '\n\n'.join(messages), 'messages': messages, 'products': []}
        if kind == 'status':
            if not self.route_result or self.route_result['kind'] not in ('progress', 'stop', 'abandon'):
                raise AppError(502, 'PI_ANSWER_INVALID', '状态回复没有可信操作结果')
            text = self.route_result['message']
            return {'status': 'completed', 'message': text, 'products': []}
        if answer.get('status') == 'waiting':
            questions = {
                'target': '你想查询哪种商品或品类？',
                'packaging': '你想看罐装还是瓶装，还是其他包装？',
                'brand': '你有偏好的品牌吗？',
                'budget': '你的预算上限是多少？',
            }
            slot = answer.get('clarification_slot')
            if not isinstance(slot, str) or slot not in questions:
                raise AppError(502, 'PI_ANSWER_INVALID', '等待回复缺少受支持的澄清项')
            return {'status': 'waiting', 'message': questions[slot], 'clarification_slot': slot, 'products': []}
        if kind == 'comparison' and not self.comparison_requested:
            raise AppError(422, 'PI_EVIDENCE_MISSING', '尚未执行品类比较')
        refs = answer.get('product_refs')
        if answer.get('status') != 'completed' or not isinstance(refs, list) or any(not isinstance(ref, str) or ref not in self.products or (self.comparison_requested and ref not in self.comparison_refs) for ref in refs):
            raise AppError(422, 'PI_UNKNOWN_REFERENCE', 'Pi 回复包含未经查询验证的商品引用')
        products = [self.products[ref] for ref in dict.fromkeys(refs)]
        if not products and not self.searched:
            raise AppError(502, 'PI_EVIDENCE_MISSING', '尚未执行商品查询，不能确认无匹配结果')
        message = '已查询到商品，但本次没有选定展示结果。' if not products and self.products else self._facts(products)
        return {'status': 'completed', 'message': message, 'products': products, 'comparison':self.comparison_requested, 'no_matches':not self.products}

    def _facts(self, products: list[dict[str, Any]]) -> str:
        if not products:
            return '本次没有查到匹配商品。价格、库存为模拟数据。'
        lines = ['查询到以下商品（价格、库存为模拟数据）：']
        for product in products:
            price = '暂无报价' if product['price_fen'] is None else f"¥{product['price_fen'] / 100:.2f}"
            spec = '' if product['spec_quantity'] is None else f"，{product['spec_quantity']:g}{product['spec_unit'] or ''}"
            stock = f"库存 {product['available_qty']}" if product['sellable'] else '当前不可售'
            lines.append(f"{product['name_zh'] or product['name']}{spec}，{price}，{stock}")
        return '\n'.join(lines)

    def _close(self, status: str) -> dict[str, Any]:
        explanation = {'stopped': '已停止本次查询。', 'deadline': '已达到 30 秒查询时限，未继续探索。', 'tool_budget': '已达到 5 轮工具查询上限，未继续探索。'}[status]
        products = list(self.products.values())[:5]
        return {'status': status, 'message': explanation + ('\n' + self._facts(products) if products else ''), 'products': products}

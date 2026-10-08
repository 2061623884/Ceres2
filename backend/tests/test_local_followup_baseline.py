"""The public baseline CLI records bounded runs through HTTP/SSE only."""
import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.parse import parse_qs, urlparse


class PublicGuideFixture:
    def __init__(self, switch_case_ids=(), no_interim_case_ids=(), delayed_stream_case_ids=(),
                 failure_case_ids=(), multi_turn_case_ids=()):
        self.owners = {}
        self.sessions = {}
        self.routes = {}
        self.runs = {}
        self.openings = {}
        self.carts = {}
        self.orders = {}
        self.requests = []
        self.bootstrap_cookies = []
        self.message_reads = []
        self.switch_case_ids = set(switch_case_ids)
        self.no_interim_case_ids = set(no_interim_case_ids)
        self.delayed_stream_case_ids = set(delayed_stream_case_ids)
        self.failure_case_ids = set(failure_case_ids)
        self.multi_turn_case_ids = set(multi_turn_case_ids)
        self.confirmations = {}
        self.confirm_calls = []
        self.product_facts = {
            'items': [{
                'sku_id': 'fixture:exact-offer', 'name': 'fixture product', 'name_zh': '测试商品',
                'category_id': 'dairy', 'brand': 'fixture', 'image_path': None, 'source': 'fixture',
                'review_status': 'approved', 'spec_quantity': 500, 'spec_unit': 'g',
                'ingredient_ids': [], 'usage_tags': [], 'product_type': 'food', 'metadata': {},
                'price_fen': 1234, 'available_qty': 3, 'sellable': False, 'offer_version': 6,
                'delivery_eta_minutes': None,
            }],
            'total': 1, 'page': 1, 'page_size': 500,
        }

    def handler(self):
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def owner(self):
                cookie = self.headers.get('Cookie', '')
                return next((part.split('=', 1)[1] for part in cookie.split('; ')
                             if part.startswith('sg_owner_id=')), None)

            def body(self):
                return json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))

            def respond(self, status, value, *, content_type='application/json', headers=()):
                data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
                self.send_response(status)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(data)))
                for name, value in headers:
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                parsed = urlparse(self.path)
                path = parsed.path
                owner_id = self.owner()
                fixture.requests.append(('GET', path, parsed.query, owner_id, None))
                if path == '/health':
                    self.respond(200, {'status': 'ok', 'database': 'connected'})
                    return

                if path == '/api/v1/bootstrap':
                    fixture.bootstrap_cookies.append(owner_id)
                    if owner_id is None:
                        owner_id = f'synthetic-owner-{len(fixture.owners) + 1}'
                        fixture.owners[owner_id] = {'session_id': f'session-{owner_id}'}
                        self.respond(200, {'owner_id': owner_id, 'store_id': 'store-demo-01',
                            'delivery_zone_id': 'zone-demo-01', 'llm_mode': 'live',
                            'business_data_mode': 'demo', 'demo_notice': '模拟数据'},
                            headers=[('Set-Cookie', f'sg_owner_id={owner_id}; Path=/; HttpOnly; SameSite=Lax')])
                    else:
                        self.respond(200, {'owner_id': owner_id, 'store_id': 'store-demo-01',
                            'delivery_zone_id': 'zone-demo-01', 'llm_mode': 'live',
                            'business_data_mode': 'demo', 'demo_notice': '模拟数据'})
                    return

                if path == '/api/v1/cart':
                    cart = fixture.carts.setdefault(owner_id, {
                        'store_id': 'store-demo-01', 'version': 1, 'items': [],
                        'total_price_fen': 0, 'business_data_mode': 'demo',
                    })
                    self.respond(200, cart)
                    return

                if path == '/api/v1/orders':
                    self.respond(200, fixture.orders.setdefault(owner_id, {'items': []}))
                    return

                if path == '/api/v1/products':
                    self.respond(200, fixture.product_facts)
                    return

                parts = path.strip('/').split('/')
                if len(parts) == 6 and parts[:3] == ['api', 'v1', 'navigation'] and parts[3] == 'sessions' and parts[5] == 'opening':
                    opening = fixture.openings.get((owner_id, parts[4]))
                    if opening is None:
                        self.respond(404, {'detail': 'OPENING_CLOSED'})
                        return
                    self.respond(200, opening)
                    return

                if len(parts) == 8 and parts[:3] == ['api', 'v1', 'guide'] and parts[3] == 'sessions' and parts[5] == 'runs' and parts[7] == 'events':
                    run_id = parts[6]
                    run = fixture.runs.get((owner_id, run_id))
                    if run is None:
                        self.respond(404, {'detail': 'RUN_NOT_FOUND'})
                        return
                    self.respond(200, {'events': run['events'], 'status': run['status']})
                    return

                if len(parts) == 8 and parts[:3] == ['api', 'v1', 'guide'] and parts[3] == 'sessions' and parts[5] == 'runs' and parts[7] == 'stream':
                    run_id = parts[6]
                    run = fixture.runs.get((owner_id, run_id))
                    if run is None:
                        self.respond(404, {'detail': 'RUN_NOT_FOUND'})
                        return
                    after = int(parse_qs(parsed.query).get('after_sequence', ['0'])[0])
                    events = [event for event in run['events'] if event['sequence'] > after]
                    if run['request_id'] in fixture.delayed_stream_case_ids:
                        chunks = ['data: ' + json.dumps(event, ensure_ascii=False) + '\n\n'
                                  for event in events]
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/event-stream')
                        self.send_header('Content-Length', str(sum(len(chunk.encode()) for chunk in chunks)))
                        self.end_headers()
                        for event, chunk in zip(events, chunks):
                            self.wfile.write(chunk.encode())
                            self.wfile.flush()
                            if event['type'] == 'message.interim':
                                time.sleep(0.12)
                    else:
                        body = ''.join('data: ' + json.dumps(event, ensure_ascii=False) + '\n\n'
                                       for event in events)
                        self.respond(200, body.encode(), content_type='text/event-stream')
                    return

                if len(parts) == 7 and parts[:3] == ['api', 'v1', 'guide'] and parts[3] == 'sessions' and parts[5] == 'turns':
                    session_id, request_id = parts[4], parts[6]
                    run = fixture.routes.get((owner_id, session_id, request_id))
                    if run is None:
                        self.respond(404, {'detail': 'TURN_NOT_FOUND'})
                        return
                    self.respond(200, {'run_id': run['run_id'], 'status': run['status'], 'result': run['result']})
                    return

                if len(parts) == 6 and parts[:3] == ['api', 'v1', 'guide'] and parts[3] == 'sessions' and parts[5] == 'messages':
                    session_id = parts[4]
                    state = fixture.sessions.get((owner_id, session_id))
                    if state is None:
                        self.respond(404, {'detail': 'SESSION_FORBIDDEN'})
                        return
                    query = parse_qs(parsed.query)
                    after_sequence = int(query.get('after_sequence', ['0'])[0])
                    limit = int(query.get('limit', ['200'])[0])
                    history = [message for message in state['message_history']
                               if message['sequence'] > after_sequence][:limit]
                    fixture.message_reads.append(history)
                    self.respond(200, {'messages': history})
                    return

                if len(parts) == 5 and parts[:3] == ['api', 'v1', 'guide'] and parts[3] == 'sessions':
                    session_id = parts[4]
                    state = fixture.sessions.get((owner_id, session_id))
                    if state is None:
                        self.respond(404, {'detail': 'SESSION_FORBIDDEN'})
                        return
                    projection = dict(state['projection'])
                    projection.pop('messages', None)
                    self.respond(200, projection)
                    return

                self.respond(404, {'detail': 'not found'})

            def do_POST(self):
                path = urlparse(self.path).path
                owner_id = self.owner()
                body = self.body()
                fixture.requests.append(('POST', path, '', owner_id, body))
                if path == '/api/v1/guide/sessions':
                    session_id = fixture.owners[owner_id]['session_id']
                    projection = {'session_id': session_id, 'task_id': None, 'state_version': 0,
                        'session_version': 0, 'entry_context': body['entry_context'], 'current_step': 'understanding',
                        'task_status': None, 'plan': None, 'product_cards': [], 'available_actions': ['send_message'],
                        'pending_clarifications': [], 'messages': []}
                    fixture.sessions[(owner_id, session_id)] = {
                        'projection': projection, 'messages': {}, 'message_history': [], 'request_id': None,
                    }
                    self.respond(200, projection)
                    return

                parts = path.strip('/').split('/')
                if len(parts) == 6 and parts[:4] == ['api', 'v1', 'guide', 'tasks'] and parts[5] == 'confirm':
                    task_id = parts[4]
                    idempotency_key = self.headers.get('idempotency-key')
                    fixture.confirm_calls.append((owner_id, task_id, idempotency_key, body))
                    prior = fixture.confirmations.get((owner_id, idempotency_key))
                    if prior is not None:
                        if prior['body'] != body:
                            self.respond(409, {'detail': 'IDEMPOTENCY_CONFLICT'})
                            return
                        self.respond(200, prior['receipt'])
                        return

                    owner_session = fixture.owners[owner_id]['session_id']
                    state = fixture.sessions[(owner_id, owner_session)]['projection']
                    plan = state['plan']
                    if (task_id != state['task_id'] or body['plan_id'] != plan['plan_id']
                            or body['plan_version'] != plan['plan_version']
                            or body['expected_state_version'] != state['state_version']
                            or body['expected_session_version'] != state['session_version']):
                        self.respond(409, {'detail': 'STALE_STATE'})
                        return
                    cart = fixture.carts.setdefault(owner_id, {
                        'store_id': 'store-demo-01', 'version': 1, 'items': [],
                        'total_price_fen': 0, 'business_data_mode': 'demo',
                    })
                    for selected in body['selected_items']:
                        existing = next((item for item in cart['items'] if item['sku_id'] == selected['sku_id']), None)
                        if existing is None:
                            cart['items'].append({'sku_id': selected['sku_id'], 'name': '测试商品',
                                'quantity': selected['quantity'], 'unit_price_fen': 100,
                                'line_total_fen': selected['quantity'] * 100, 'image_path': None,
                                'sellable': True})
                        else:
                            existing['quantity'] += selected['quantity']
                            existing['line_total_fen'] = existing['quantity'] * existing['unit_price_fen']
                    cart['version'] += 1
                    cart['total_price_fen'] = sum(item['line_total_fen'] for item in cart['items'])
                    state['state_version'] += 1
                    receipt = {'status': 'success', 'operation_id': 'fixture-operation-1',
                        'confirmation_id': 'fixture-confirmation-1', 'items_added': body['selected_items'],
                        'cart_version': cart['version'], 'task_id': task_id,
                        'state_version': state['state_version'], 'session_version': state['session_version']}
                    fixture.confirmations[(owner_id, idempotency_key)] = {'body': body, 'receipt': receipt}
                    self.respond(200, receipt)
                    return

                if len(parts) == 6 and parts[:3] == ['api', 'v1', 'navigation'] and parts[3] == 'sessions' and parts[5] == 'opening':
                    session_id = parts[4]
                    if (owner_id, session_id) not in fixture.sessions:
                        self.respond(404, {'detail': 'SESSION_FORBIDDEN'})
                        return
                    opening = {'opening_id': f'opening-{owner_id}', 'role': body['role'],
                        'prompt_displayed': False, 'closed': False, 'pending_request_id': None,
                        'latest_request_id': None, 'accepted_request_id': None, 'handoff': None}
                    fixture.openings[(owner_id, session_id)] = opening
                    self.respond(200, opening)
                    return

                if len(parts) == 6 and parts[:3] == ['api', 'v1', 'navigation'] and parts[3] == 'sessions' and parts[5] == 'routes':
                    session_id = parts[4]
                    case_id = body['request_id']
                    if (owner_id, session_id) not in fixture.sessions or body['role'] != 'keke':
                        self.respond(404, {'detail': 'SESSION_FORBIDDEN'})
                        return
                    session_state = fixture.sessions[(owner_id, session_id)]['projection']
                    anchor = [session_state['session_version'], session_state['task_id'], session_state['state_version']]
                    fixture.routes[(owner_id, session_id, case_id)] = {
                        'message': body['message'], 'opening_id': body['opening_id'], 'role': body['role'],
                        'anchor': anchor}
                    decision = {'routing_request_id': case_id, 'opening_id': body['opening_id'],
                        'original_message': body['message'], 'selected_object': body.get('selected_object'),
                        'source_role': body['role'], 'target_role': 'keke', 'authorized_role': 'keke',
                        'status': 'ready', 'show_prompt': False, 'continue_original': False, 'capability': None,
                        'criteria_version': 'fixture-role-entry-v1', 'anchor': anchor,
                        'entry_judgment': {'outcome': 'no', 'elapsed_ms': 2.0, 'reason': None}}
                    if case_id in fixture.switch_case_ids:
                        decision.update(target_role='momo', authorized_role=None, status='switch',
                            show_prompt=True, message='这件事可以交给墨墨。要切换吗？',
                            entry_judgment={'outcome': 'yes', 'elapsed_ms': 2.0, 'reason': None})
                    opening = fixture.openings[(owner_id, session_id)]
                    opening['latest_request_id'] = case_id
                    opening['pending_request_id'] = case_id if decision['status'] == 'switch' else None
                    self.respond(200, decision)
                    return

                if len(parts) == 6 and parts[:3] == ['api', 'v1', 'guide'] and parts[3] == 'sessions' and parts[5] == 'runs':
                    session_id = parts[4]
                    case_id = body['request_id']
                    routed = fixture.routes.get((owner_id, session_id, case_id))
                    expected_anchor = (body.get('expected_session_version'), body.get('expected_task_id'), body.get('expected_state_version'))
                    if (routed is None or routed['message'] != body['message']
                            or body.get('routing_request_id') != case_id or expected_anchor != tuple(routed['anchor'])):
                        self.respond(409, {'detail': 'ROUTE_REQUEST_MISMATCH'})
                        return
                    if case_id in fixture.failure_case_ids:
                        self.respond(503, {'detail': 'synthetic run failure'})
                        return
                    run_id = f'run-{case_id}'
                    runtime_version = {'source_revision': 'fixture-source-revision', 'source_scope': 'disk_at_admission',
                        'build_revision': None, 'build_scope': None, 'prompt_revision': None,
                        'captured_at_ms': 1700000000000.0, 'loaded_code_equivalence': 'unknown'}
                    runtime_summary = {'policy_lookups': 1, 'policy_tool_lookups': 0,
                        'policy_lookup_outcomes': {'success': 1, 'empty': 0, 'error': 0}, 'policy_reuses': 0,
                        'tool_starts': 1, 'primary_pi_turns': 1, 'policy_judgment': {'outcome': 'yes', 'elapsed_ms': 3.0},
                        'provider_calls': {'primary_pi': {'started': 1, 'completed': 1, 'usage_observed': 0,
                            'usage_missing': 1, 'observed_usage': None, 'usage_complete': False, 'cost': None}},
                        'provider_call_records': [{'stage': 'primary_pi', 'usage': None, 'cost': None}],
                        'provider_records_truncated': False, 'provider_calls_complete': False}
                    result = {'request_id': case_id, 'session_id': session_id, 'task_id': None, 'state_version': 0,
                        'session_version': 0, 'status': 'understanding', 'answer_status': 'accepted',
                        'message': f'受控回答：{body["message"]}', 'messages': [{'message_id': f'final-{case_id}',
                            'content': f'受控回答：{body["message"]}'}], 'answer_kind': 'general_explanation',
                        'runtime_status': 'completed', 'tool_rounds': 1, 'runtime_summary': runtime_summary,
                        'runtime_events': [{'type': 'policy_judgment', 'outcome': 'yes', 'elapsed_ms': 3.0},
                            {'type': 'policy_lookup', 'outcome': 'success', 'policy_ref': f'policy-{case_id}'}],
                        'runtime_version': runtime_version, 'entry_judgment': {'outcome': 'no', 'elapsed_ms': 2.0,
                            'reason': None, 'routing_request_id': case_id, 'rules_version': 'fixture-role-entry-v1', 'usage': None},
                        'confirmation_result': None, 'committed': False}
                    execution_id = case_id.split(':step:', 1)[0]
                    special_multiturn = execution_id in fixture.multi_turn_case_ids
                    if special_multiturn:
                        projection = fixture.sessions[(owner_id, session_id)]['projection']
                        plan_version = 1 if projection['plan'] is None else projection['plan']['plan_version'] + 1
                        quantity = 2 if plan_version == 1 else 3
                        task_id = projection['task_id'] or f'task-{owner_id}'
                        plan = {'plan_id': f'plan-{owner_id}', 'plan_version': plan_version,
                            'items': [{'sku_id': 'sku-demo-confirm', 'quantity': quantity,
                                'remaining_quantity': quantity, 'selected': True, 'added_quantity': 0,
                                'unit_price_fen': 100}], 'can_confirm': True, 'total_price_fen': quantity * 100}
                        projection.update(task_id=task_id, state_version=projection['state_version'] + 1,
                            current_step='awaiting_confirmation', task_status='active', plan=plan,
                            available_actions=['send_message', 'modify', 'confirm'])
                        result.update(task_id=task_id, state_version=projection['state_version'],
                            session_version=projection['session_version'], status='waiting_confirmation',
                            plan=plan)
                    started = 1700000000000.0
                    interim_id = f'{run_id}:interim:1'
                    messages = [{'message_id': f'user-{case_id}', 'session_id': session_id, 'task_id': None,
                        'sequence': 1, 'role': 'user', 'kind': 'text', 'content': body['message'], 'request_id': case_id}]
                    events = [{'protocol_version': 1, 'run_id': run_id, 'sequence': 1, 'type': 'accepted',
                        'recorded_at_ms': started, 'elapsed_ms': 0.0, 'session_id': session_id,
                        'target_task_id': None, 'payload': {'request_id': case_id}},
                        {'protocol_version': 1, 'run_id': run_id, 'sequence': 2, 'type': 'progress',
                         'recorded_at_ms': started + 20, 'elapsed_ms': 20.0, 'session_id': session_id,
                         'target_task_id': None, 'payload': {'phase': 'tool_progress'}}]
                    sequence = 3
                    if case_id not in fixture.no_interim_case_ids:
                        messages.append({'message_id': interim_id, 'session_id': session_id, 'task_id': None,
                            'sequence': len(messages) + 1, 'role': 'assistant', 'kind': 'interim',
                            'content': '我先核对一下相关信息。', 'request_id': case_id})
                        events.append({'protocol_version': 1, 'run_id': run_id, 'sequence': sequence,
                            'type': 'message.interim', 'recorded_at_ms': started + 100, 'elapsed_ms': 100.0,
                            'session_id': session_id, 'target_task_id': None,
                            'payload': {'message_id': interim_id, 'content': '我先核对一下相关信息。'}})
                        sequence += 1
                    messages.append({'message_id': f'final-{case_id}', 'session_id': session_id, 'task_id': None,
                        'sequence': len(messages) + 1, 'role': 'assistant', 'kind': 'text',
                        'content': result['message'], 'request_id': case_id})
                    events.extend([
                        {'protocol_version': 1, 'run_id': run_id, 'sequence': sequence, 'type': 'answer.delta',
                         'recorded_at_ms': started + 200, 'elapsed_ms': 200.0, 'session_id': session_id,
                         'target_task_id': None, 'payload': {'delta': result['message'], 'replace': True,
                             'final': True, 'message_id': f'final-{case_id}', 'answer_kind': 'general_explanation'}},
                        {'protocol_version': 1, 'run_id': run_id, 'sequence': sequence + 1, 'type': 'turn.completed',
                         'recorded_at_ms': started + 250, 'elapsed_ms': 250.0, 'session_id': session_id,
                         'target_task_id': None, 'payload': result},
                    ])
                    run_status = result['status'] if special_multiturn else 'completed'
                    fixture.runs[(owner_id, run_id)] = {'request_id': case_id, 'session_id': session_id,
                        'status': run_status, 'result': result, 'events': events}
                    fixture.routes[(owner_id, session_id, case_id)].update({'run_id': run_id,
                        'status': run_status, 'result': result})
                    fixture.sessions[(owner_id, session_id)]['request_id'] = case_id
                    fixture.sessions[(owner_id, session_id)]['messages'][case_id] = messages
                    message_history = fixture.sessions[(owner_id, session_id)]['message_history']
                    for sequence_index, message in enumerate(messages, start=len(message_history) + 1):
                        message['sequence'] = sequence_index
                        message_history.append(message)
                    self.respond(202, {'run_id': run_id, 'request_id': case_id})
                    return

                self.respond(404, {'detail': 'not found'})

        return Handler


def test_baseline_cli_captures_current_public_runs_without_business_confirmation(tmp_path):
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'synthetic-public-contract-v1',
        'cases': [
            {'case_id': 'policy-shopping-mixed', 'category': 'policy_mixed', 'core': False,
             'message': '查一下退货政策，也帮我看看三人份番茄炒蛋食材。',
             'expected_behavior': 'Preserve both policy and recipe-shopping requests.', 'fact_sources': []},
            {'case_id': 'product-selection', 'category': 'product_selection', 'core': False,
             'message': '帮我选两款低糖酸奶，先比较不要加购。',
             'expected_behavior': 'Compare products without adding them to the cart.', 'fact_sources': []},
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'batch.json'
    fixture = PublicGuideFixture()
    server = ThreadingHTTPServer(('127.0.0.1', 0), fixture.handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        command = [sys.executable, '-m', 'app.evaluation.run_baseline',
            '--api-base', f'http://127.0.0.1:{server.server_port}',
            '--cases', str(cases_path), '--output', str(output)]
        process = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
                                 capture_output=True, text=True, timeout=20)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert process.returncode == 0, process.stderr
    assert output.is_file()
    batch = json.loads(output.read_text(encoding='utf-8'))
    assert batch['schema_version'] == 'ceres-local-followup-batch-v1'
    assert batch['case_set'] == {'version': cases['version'],
        'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest()}
    assert [row['case_id'] for row in batch['cases']] == [row['case_id'] for row in cases['cases']]

    captures = [row['capture'] for row in batch['cases']]
    assert all(capture['schema_version'] == 'ceres-eval-capture-v2' for capture in captures)
    execution_ids = [f"{row['case_id']}:trial:1" for row in cases['cases']]
    assert all(capture['request_id'] == execution_id for capture, execution_id in zip(captures, execution_ids))
    assert len({capture['owner_id'] for capture in captures}) == 2
    assert len({capture['session_id'] for capture in captures}) == 2
    assert [capture['run_id'] for capture in captures] == [f'run-{execution_id}' for execution_id in execution_ids]
    assert all(capture['status'] == 'completed' and capture['labels'] is None for capture in captures)
    assert all(capture['execution_id'] is None for capture in captures)
    assert all(capture['export_source_snapshot'] is None for capture in captures)
    assert all(capture['runtime_version']['source_revision'] == 'fixture-source-revision' for capture in captures)
    assert all(capture['runtime_version']['loaded_code_equivalence'] == 'unknown' for capture in captures)
    assert all(capture['runtime_summary']['provider_calls']['primary_pi']['observed_usage'] is None for capture in captures)
    assert all(capture['runtime_summary']['provider_calls']['primary_pi']['cost'] is None for capture in captures)
    assert all(any(event['type'] == 'message.interim' for event in capture['events']) for capture in captures)
    assert all(any(message['kind'] == 'interim' for message in capture['messages']) for capture in captures)
    assert all(any(message['role'] == 'user' and message['content'] == case['message']
                   for message in capture['messages']) for capture, case in zip(captures, cases['cases']))

    assert fixture.bootstrap_cookies == [None, None], 'Each case must bootstrap with a fresh HTTP cookie jar.'
    assert len({row[3] for row in fixture.requests if row[0] == 'POST'}) == 2
    run_posts = [row for row in fixture.requests if row[0] == 'POST' and row[1].endswith('/runs')]
    assert [row[4]['request_id'] for row in run_posts] == execution_ids
    assert all(row[4]['routing_request_id'] == row[4]['request_id'] for row in run_posts)
    assert all(row[4]['message'] == case['message'] for row, case in zip(run_posts, cases['cases']))
    route_posts = [row for row in fixture.requests if row[0] == 'POST' and row[1].endswith('/routes')]
    assert all(row[4]['message'] == case['message'] for row, case in zip(route_posts, cases['cases']))
    receipt_reads = [row for row in fixture.requests if row[0] == 'GET' and '/turns/' in row[1]]
    assert len(receipt_reads) == len(cases['cases'])
    assert [row[1].rsplit('/', 1)[1] for row in receipt_reads] == execution_ids
    stream_reads = [row for row in fixture.requests if row[0] == 'GET' and row[1].endswith('/stream')]
    assert [row[1].split('/')[-2:] for row in stream_reads] == [
        [f'run-{execution_id}', 'stream'] for execution_id in execution_ids]
    assert all(row[3] == capture['owner_id'] for row, capture in zip(receipt_reads, captures))
    assert all(row[3] == capture['owner_id'] for row, capture in zip(stream_reads, captures))
    assert all(not (method == 'POST' and ('/confirm' in path or path.startswith('/api/v1/cart')))
               for method, path, *_ in fixture.requests)


def test_baseline_cli_preserves_role_choice_and_continues_remaining_cases(tmp_path):
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'synthetic-role-choice-contract-v1',
        'cases': [
            {'case_id': 'role-choice-required', 'category': 'role_entry', 'core': False,
             'message': '查一下这个订单的退款进度。',
             'expected_behavior': 'Ask before switching roles.', 'fact_sources': []},
            {'case_id': 'after-role-choice', 'category': 'product_selection', 'core': False,
             'message': '帮我选两款低糖酸奶，先比较不要加购。',
             'expected_behavior': 'Capture the next case without replaying the first.', 'fact_sources': []},
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'batch.json'
    fixture = PublicGuideFixture(switch_case_ids={'role-choice-required:trial:1'})
    server = ThreadingHTTPServer(('127.0.0.1', 0), fixture.handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        command = [sys.executable, '-m', 'app.evaluation.run_baseline',
            '--api-base', f'http://127.0.0.1:{server.server_port}',
            '--cases', str(cases_path), '--output', str(output)]
        process = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
                                 capture_output=True, text=True, timeout=20)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert process.returncode == 0, process.stderr
    batch = json.loads(output.read_text(encoding='utf-8'))
    assert [row['case_id'] for row in batch['cases']] == [row['case_id'] for row in cases['cases']]

    choice, following = batch['cases']
    choice_execution_id = 'role-choice-required:trial:1'
    following_execution_id = 'after-role-choice:trial:1'
    assert choice['outcome'] == 'role_choice_required'
    assert choice['capture'] is None
    assert choice['error'] is None
    assert choice['navigation'] == {
        'routing_request_id': choice_execution_id,
        'opening_id': 'opening-synthetic-owner-1',
        'source_role': 'keke',
        'target_role': 'momo',
        'authorized_role': None,
        'status': 'switch',
        'show_prompt': True,
        'continue_original': False,
        'criteria_version': 'fixture-role-entry-v1',
        'anchor': [0, None, 0],
        'entry_judgment': {'outcome': 'yes', 'elapsed_ms': 2.0, 'reason': None},
        'message': '这件事可以交给墨墨。要切换吗？',
    }
    assert following['outcome'] == 'guide_run'
    assert following['navigation']['status'] == 'ready'
    assert following['capture']['request_id'] == following_execution_id
    assert following['capture']['status'] == 'completed'
    assert following['error'] is None

    run_posts = [row for row in fixture.requests if row[0] == 'POST' and row[1].endswith('/runs')]
    assert [row[4]['request_id'] for row in run_posts] == [following_execution_id]
    assert all('/switches' not in row[1] for row in fixture.requests)
    assert all(not (method == 'POST' and ('/confirm' in path or path.startswith('/api/v1/cart')))
               for method, path, *_ in fixture.requests)


def test_baseline_cli_records_public_before_after_state_and_exact_catalog_offers(tmp_path):
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'synthetic-public-state-contract-v1',
        'cases': [{
            'case_id': 'public-state-and-offer', 'category': 'product_selection', 'core': False,
            'message': '比较测试商品，只查看，不要加购。',
            'expected_behavior': 'Use the current public Offer and do not change cart or orders.',
            'fact_sources': [],
        }],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'batch.json'
    fixture = PublicGuideFixture()
    server = ThreadingHTTPServer(('127.0.0.1', 0), fixture.handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        command = [sys.executable, '-m', 'app.evaluation.run_baseline',
            '--api-base', f'http://127.0.0.1:{server.server_port}',
            '--cases', str(cases_path), '--output', str(output)]
        process = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
                                 capture_output=True, text=True, timeout=20)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert process.returncode == 0, process.stderr
    batch = json.loads(output.read_text(encoding='utf-8'))
    record = batch['cases'][0]
    assert record['outcome'] == 'guide_run'
    assert record['capture']['request_id'] == 'public-state-and-offer:trial:1'
    assert set(record['before']) == {'guide', 'cart', 'orders', 'opening'}
    assert set(record['after']) == {'guide', 'cart', 'orders', 'opening'}
    assert record['before']['guide']['session_id'] == record['capture']['session_id']
    assert record['before']['guide']['session_version'] == 0
    assert 'messages' not in record['before']['guide']
    assert record['before']['cart'] == {
        'store_id': 'store-demo-01', 'version': 1, 'items': [],
        'total_price_fen': 0, 'business_data_mode': 'demo',
    }
    assert record['after']['cart'] == record['before']['cart']
    assert record['before']['orders'] == {'items': []}
    assert record['after']['orders'] == record['before']['orders']
    assert record['before']['opening']['role'] == record['after']['opening']['role'] == 'keke'
    assert record['before']['opening']['latest_request_id'] is None
    assert record['before']['opening']['pending_request_id'] is None
    assert record['after']['opening']['latest_request_id'] == 'public-state-and-offer:trial:1'
    assert record['after']['opening']['pending_request_id'] is None

    assert record['catalog_facts'] == fixture.product_facts
    offer = record['catalog_facts']['items'][0]
    assert (offer['sku_id'], offer['price_fen'], offer['available_qty'],
            offer['sellable'], offer['offer_version']) == ('fixture:exact-offer', 1234, 3, False, 6)
    assert record['catalog_facts']['total'] == 1
    assert record['catalog_facts']['page_size'] == 500

    paths = [row[1] for row in fixture.requests if row[0] == 'GET']
    for path in (
        '/api/v1/guide/sessions/session-synthetic-owner-1',
        '/api/v1/cart', '/api/v1/orders',
        '/api/v1/navigation/sessions/session-synthetic-owner-1/opening',
    ):
        assert paths.count(path) == 2, f'{path} must be read both before and after the Guide run.'
    product_reads = [row for row in fixture.requests if row[0] == 'GET' and row[1] == '/api/v1/products']
    assert len(product_reads) == 1
    assert parse_qs(product_reads[0][2]) == {'page_size': ['500']}
    assert product_reads[0][3] == record['capture']['owner_id']
    assert all(not (method == 'POST' and ('/confirm' in path or path.startswith('/api/v1/cart')))
               for method, path, *_ in fixture.requests)


def test_baseline_cli_measures_client_sse_arrival_and_keeps_missing_interim_unknown(tmp_path):
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'synthetic-client-timing-contract-v1',
        'cases': [
            {'case_id': 'timing-with-interim', 'category': 'planning', 'core': False,
             'message': '先帮我查清楚需要买什么。', 'expected_behavior': 'Expose the interim before terminal output.',
             'fact_sources': []},
            {'case_id': 'timing-without-interim', 'category': 'product_selection', 'core': False,
             'message': '列出两款低糖酸奶。', 'expected_behavior': 'Do not infer an interim from tool progress.',
             'fact_sources': []},
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'batch.json'
    fixture = PublicGuideFixture(
        no_interim_case_ids={'timing-without-interim:trial:1'},
        delayed_stream_case_ids={'timing-with-interim:trial:1'},
    )
    server = ThreadingHTTPServer(('127.0.0.1', 0), fixture.handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        command = [sys.executable, '-m', 'app.evaluation.run_baseline',
            '--api-base', f'http://127.0.0.1:{server.server_port}',
            '--cases', str(cases_path), '--output', str(output)]
        process = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
                                 capture_output=True, text=True, timeout=20)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert process.returncode == 0, process.stderr
    records = json.loads(output.read_text(encoding='utf-8'))['cases']
    with_interim, without_interim = records
    assert with_interim['first_interim_ms'] is not None
    assert with_interim['first_final_ms'] > with_interim['first_interim_ms']
    assert with_interim['stream_complete_ms'] > with_interim['first_interim_ms']
    assert without_interim['first_interim_ms'] is None
    assert without_interim['first_final_ms'] is not None
    assert without_interim['stream_complete_ms'] is not None
    assert all(row['timing_source'] == 'client_monotonic_from_run_post_start' for row in records)
    assert any(event['type'] == 'message.interim' and 'recorded_at_ms' in event
               for event in with_interim['capture']['events'])
    assert any(event['type'] == 'progress' for event in without_interim['capture']['events'])
    assert not any(event['type'] == 'message.interim' for event in without_interim['capture']['events'])


def test_baseline_cli_plans_core_repeats_and_resumes_without_repeating_attempts(tmp_path):
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'synthetic-plan-resume-contract-v1',
        'cases': [
            {'case_id': 'core-a', 'category': 'planning', 'core': True, 'message': '规划一个简单晚餐。'},
            {'case_id': 'side-setup', 'category': 'setup_contract', 'core': False,
             'message': '检查准备步骤。', 'setup': [{'kind': 'unsupported_fixture_setup'}]},
            {'case_id': 'core-b', 'category': 'policy', 'core': True, 'message': '说明退货期限。'},
            {'case_id': 'side-steps', 'category': 'steps_contract', 'core': False,
             'message': '比较两款商品。', 'steps': [{'op': 'unsupported_fixture_step'}]},
            {'case_id': 'side-normal', 'category': 'product_selection', 'core': False,
             'message': '比较测试商品。'},
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'batch.json'
    fixture = PublicGuideFixture(failure_case_ids={'core-a:trial:1'})
    server = ThreadingHTTPServer(('127.0.0.1', 0), fixture.handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    api_base = f'http://127.0.0.1:{server.server_port}'

    def invoke(*extra_args, case_file=cases_path, base=api_base):
        command = [sys.executable, '-m', 'app.evaluation.run_baseline',
            '--api-base', base, '--cases', str(case_file), '--output', str(output), *extra_args]
        return subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
                              capture_output=True, text=True, timeout=20)

    def expected_plan():
        rows = []
        core = [case['case_id'] for case in cases['cases'] if case['core']]
        remaining = [case['case_id'] for case in cases['cases'] if not case['core']]
        for case_id in core + remaining:
            rows.append({'case_id': case_id, 'trial': 1, 'execution_id': f'{case_id}:trial:1'})
        for trial in (2, 3):
            for case_id in core:
                rows.append({'case_id': case_id, 'trial': trial, 'execution_id': f'{case_id}:trial:{trial}'})
        return rows

    try:
        first = invoke('--core-repeats', '3', '--max-executions', '2')
        assert first.returncode == 0, first.stderr
        initial_bytes = output.read_bytes()
        initial = json.loads(initial_bytes)
        plan = expected_plan()
        assert initial['schema_version'] == 'ceres-local-followup-batch-v1'
        assert initial['api_base'] == api_base
        assert initial['case_set'] == {'version': cases['version'],
            'sha256': hashlib.sha256(cases_path.read_bytes()).hexdigest()}
        assert initial['plan'] == plan
        first_rows = initial['cases']
        assert [{key: row[key] for key in ('case_id', 'trial', 'execution_id')} for row in first_rows] == plan
        assert first_rows[0]['outcome'] == 'runner_failed'
        assert first_rows[0]['capture'] is None
        assert first_rows[0]['error']['type'] == 'HTTPStatusError'
        assert first_rows[1]['outcome'] == 'guide_run'
        assert first_rows[1]['capture']['request_id'] == 'core-b:trial:1'
        assert all(row['outcome'] == 'not_run' and row['capture'] is None for row in first_rows[2:])

        resumed = invoke('--core-repeats', '3', '--max-executions', '4', '--resume')
        assert resumed.returncode == 0, resumed.stderr
        batch = json.loads(output.read_text(encoding='utf-8'))
        rows = batch['cases']
        assert batch['plan'] == plan
        assert [row['outcome'] for row in rows] == [
            'runner_failed', 'guide_run', 'runner_failed', 'runner_failed',
            'guide_run', 'guide_run', 'not_run', 'not_run', 'not_run',
        ]
        assert rows[0]['error'] == first_rows[0]['error']
        assert rows[0]['capture'] is None
        assert rows[1]['capture'] == first_rows[1]['capture']
        for index, expected in ((2, 'setup'), (3, 'unsupported_fixture_step')):
            assert expected in rows[index]['error']['reason'].lower()
            assert rows[index]['before'] is None and rows[index]['catalog_facts'] is None
        assert rows[4]['capture']['request_id'] == 'side-normal:trial:1'
        assert rows[5]['capture']['request_id'] == 'core-a:trial:2'
        captures = [row['capture'] for row in rows if row['capture'] is not None]
        assert len({capture['owner_id'] for capture in captures}) == len(captures)

        run_posts = [row for row in fixture.requests if row[0] == 'POST' and row[1].endswith('/runs')]
        assert [row[4]['request_id'] for row in run_posts] == [
            'core-a:trial:1', 'core-b:trial:1', 'side-normal:trial:1', 'core-a:trial:2',
        ]
        route_posts = [row for row in fixture.requests if row[0] == 'POST' and row[1].endswith('/routes')]
        assert [row[4]['request_id'] for row in route_posts] == [row[4]['request_id'] for row in run_posts]

        request_count = len(fixture.requests)
        preserved_bytes = output.read_bytes()
        mismatches = [
            invoke('--core-repeats', '2', '--resume'),
        ]
        changed = dict(cases)
        changed['cases'] = [dict(row) for row in cases['cases']]
        changed['cases'][0]['message'] = 'changed case set must be rejected'
        changed_path = tmp_path / 'changed-cases.json'
        changed_path.write_text(json.dumps(changed, ensure_ascii=False), encoding='utf-8')
        mismatches.append(invoke('--core-repeats', '3', '--resume', case_file=changed_path))
        mismatches.append(invoke('--core-repeats', '3', '--resume', base='http://127.0.0.1:1'))
        assert all(process.returncode != 0 for process in mismatches)
        assert output.read_bytes() == preserved_bytes
        assert len(fixture.requests) == request_count
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_baseline_cli_runs_declared_followup_confirm_and_idempotent_replay(tmp_path):
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'synthetic-multiturn-confirm-contract-v1',
        'cases': [
            {'case_id': 'multi-turn-confirm', 'category': 'purchase_planning', 'core': False,
             'message': '先整理一份晚餐采购清单。',
             'steps': [
                 {'op': 'turn', 'message': '调整为两人份，继续核对。'},
                 {'op': 'confirm_plan'},
                 {'op': 'repeat_confirmation'},
             ]},
            {'case_id': 'fresh-owner', 'category': 'product_selection', 'core': False,
             'message': '列出一款测试商品。'},
        ],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'batch.json'
    fixture = PublicGuideFixture(multi_turn_case_ids={'multi-turn-confirm:trial:1'})
    server = ThreadingHTTPServer(('127.0.0.1', 0), fixture.handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        command = [sys.executable, '-m', 'app.evaluation.run_baseline',
            '--api-base', f'http://127.0.0.1:{server.server_port}',
            '--cases', str(cases_path), '--output', str(output)]
        process = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
                                 capture_output=True, text=True, timeout=20)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert process.returncode == 0, process.stderr
    batch = json.loads(output.read_text(encoding='utf-8'))
    first, second = batch['cases']
    execution_id = 'multi-turn-confirm:trial:1'
    followup_id = f'{execution_id}:step:1'
    assert first['outcome'] == second['outcome'] == 'guide_run'
    assert first['before']['cart']['items'] == []
    assert first['after']['cart']['items'][0]['quantity'] == 3
    assert len(first['steps']) == 4
    assert [step['op'] for step in first['steps']] == [
        'turn', 'turn', 'confirm_plan', 'repeat_confirmation',
    ]
    assert [step['index'] for step in first['steps']] == [0, 1, 2, 3]
    initial_turn, followup_turn, confirm, replay = first['steps']
    assert initial_turn['request_id'] == execution_id
    assert initial_turn['message'] == cases['cases'][0]['message']
    assert followup_turn['request_id'] == followup_id
    assert followup_turn['message'] == cases['cases'][0]['steps'][0]['message']
    assert initial_turn['before']['cart']['items'] == initial_turn['after']['cart']['items'] == []
    assert followup_turn['before']['cart']['items'] == followup_turn['after']['cart']['items'] == []
    assert initial_turn['capture']['request_id'] == execution_id
    assert followup_turn['capture']['request_id'] == followup_id
    assert confirm['capture'] is None and replay['capture'] is None
    assert confirm['before']['cart']['items'] == []
    assert confirm['after']['cart']['items'][0]['quantity'] == 3
    assert replay['before']['cart'] == replay['after']['cart']
    assert replay['after']['cart']['items'][0]['quantity'] == 3
    assert confirm['confirmation_receipt']['status'] == 'success'
    assert replay['confirmation_receipt'] == confirm['confirmation_receipt']
    assert confirm['idempotency_key'] == replay['idempotency_key']
    assert confirm['confirmation_body'] == replay['confirmation_body']
    assert confirm['confirmation_body'] == {
        'plan_id': 'plan-synthetic-owner-1', 'plan_version': 2,
        'expected_state_version': 2, 'expected_session_version': 0,
        'selected_items': [{'sku_id': 'sku-demo-confirm', 'quantity': 3}],
    }
    assert len(first['captures']) == 2
    assert [capture['request_id'] for capture in first['captures']] == [execution_id, followup_id]
    assert first['capture'] == first['captures'][-1] == followup_turn['capture']

    assert second['steps'][0]['request_id'] == 'fresh-owner:trial:1'
    assert second['before']['cart']['items'] == second['after']['cart']['items'] == []
    assert second['capture']['owner_id'] != first['capture']['owner_id']
    assert {capture['owner_id'] for capture in first['captures']} == {first['capture']['owner_id']}
    assert [call[1] for call in fixture.confirm_calls] == ['task-synthetic-owner-1'] * 2
    assert len(fixture.confirm_calls) == 2
    assert fixture.confirm_calls[0][2] == fixture.confirm_calls[1][2] == confirm['idempotency_key']
    assert fixture.confirm_calls[0][3] == fixture.confirm_calls[1][3] == confirm['confirmation_body']
    route_posts = [row for row in fixture.requests if row[0] == 'POST' and row[1].endswith('/routes')]
    run_posts = [row for row in fixture.requests if row[0] == 'POST' and row[1].endswith('/runs')]
    assert [row[4]['request_id'] for row in route_posts] == [execution_id, followup_id, 'fresh-owner:trial:1']
    assert [row[4]['request_id'] for row in run_posts] == [execution_id, followup_id, 'fresh-owner:trial:1']
    assert all(not (method == 'POST' and path.startswith('/api/v1/cart'))
               for method, path, *_ in fixture.requests)


def test_baseline_cli_filters_public_session_history_to_each_capture_request(tmp_path):
    initial_message = '首轮消息只属于首轮capture。'
    followup_message = '续问消息只属于续问capture。'
    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'synthetic-public-message-history-v1',
        'cases': [{
            'case_id': 'messages-per-run', 'category': 'planning', 'core': False,
            'message': initial_message,
            'steps': [{'op': 'turn', 'message': followup_message}],
        }],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    output = tmp_path / 'batch.json'
    fixture = PublicGuideFixture(multi_turn_case_ids={'messages-per-run:trial:1'})
    server = ThreadingHTTPServer(('127.0.0.1', 0), fixture.handler())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        command = [sys.executable, '-m', 'app.evaluation.run_baseline',
            '--api-base', f'http://127.0.0.1:{server.server_port}',
            '--cases', str(cases_path), '--output', str(output)]
        process = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(),
                                 capture_output=True, text=True, timeout=20)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert process.returncode == 0, process.stderr
    record = json.loads(output.read_text(encoding='utf-8'))['cases'][0]
    first_request_id = 'messages-per-run:trial:1'
    followup_request_id = f'{first_request_id}:step:1'
    assert record['outcome'] == 'guide_run'
    assert [capture['request_id'] for capture in record['captures']] == [
        first_request_id, followup_request_id,
    ]
    assert record['capture'] == record['captures'][-1]
    assert [message['content'] for message in record['captures'][0]['messages'] if message['role'] == 'user'] == [initial_message]
    assert [message['content'] for message in record['captures'][1]['messages'] if message['role'] == 'user'] == [followup_message]
    assert all(followup_message not in message['content'] for message in record['captures'][0]['messages'])
    assert all(initial_message not in message['content'] for message in record['captures'][1]['messages'])
    assert [message['sequence'] for message in record['captures'][0]['messages']] == [1, 2, 3]
    assert [message['sequence'] for message in record['captures'][1]['messages']] == [4, 5, 6]

    assert [message['request_id'] for message in fixture.message_reads[0]] == [first_request_id] * 3
    assert [message['request_id'] for message in fixture.message_reads[1]] == [
        first_request_id, first_request_id, first_request_id,
        followup_request_id, followup_request_id, followup_request_id,
    ]
    assert [message['sequence'] for message in fixture.message_reads[1]] == [1, 2, 3, 4, 5, 6]

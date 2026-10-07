"""Policy prefetch through public Guide SSE and the actual Pi HTTP boundary."""
import json
import threading
import time
from types import SimpleNamespace

import httpx
import pytest

from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE
from test_guide_semantics import turn
from test_guide_clarification_context import answer, call


@pytest.fixture
def policy_transport(monkeypatch):
    from app.services import kev_provider
    control = {'calls': [], 'choice': 'yes'}

    def handle(request):
        payload = json.loads(request.content)
        control['calls'].append(payload)
        purpose = next(iter(payload['questions']))
        choice = control['choice'] if purpose == 'policy' else 'no'
        if isinstance(choice, httpx.HTTPError):
            raise choice
        return httpx.Response(200, json={'model': 'kev-latest', 'answers': {purpose: {
            'type': 'choice', 'choice': choice,
            'probabilities': {key: float(key == choice) for key in ('yes', 'no', 'uncertain')},
        }}})

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        monkeypatch.setattr(kev_provider, 'client', lambda: client)
        monkeypatch.setattr(kev_provider, 'get_settings', lambda: SimpleNamespace(kev_base_url='http://kev-controlled.invalid'))
        yield control


def message_text(message):
    content = message.get('content')
    return content if isinstance(content, str) else ''.join(part['text'] for part in content or [] if part['type'] == 'text')


def prefetched(body):
    for message in body['messages']:
        content = message_text(message)
        if message['role'] == 'user' and content.startswith('CERES_POLICY_EVIDENCE\n'):
            return json.loads(content.split('\n', 1)[1])
    return None


def test_yes_prefetch_is_actual_low_trust_input_and_registered_policy_evidence(pi_client, policy_transport, monkeypatch):
    from app.mercury import policy
    client, requests = pi_client
    original = '先了解退货条件，签收时间和能否退货还不清楚'
    lookups = []
    search = policy.search_policies

    def observe(query, category=None):
        lookups.append((query, category))
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)

    def respond(body):
        evidence = prefetched(body)
        outputs = [m for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'question'})
        return answer({'status': 'completed', 'answer_kind': 'policy_result',
                       'policy_ref': evidence['policy_ref'] if evidence else 'missing-prefetch'})

    requests.answer_hook = respond
    events = turn(client, original, 'prefetch-first')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert lookups == [(original, None)]
    assert [next(iter(row['questions'])) for row in policy_transport['calls']] == ['service', 'policy']
    assert policy_transport['calls'][1]['state']['message'] == original
    first = requests[0]
    evidence = prefetched(first)
    assert evidence['query'] == original and evidence['category'] is None
    assert evidence['request_id'] == 'prefetch-first'
    assert evidence['source_version'] == '2026-10-06'
    assert evidence['outcome'] == 'success' and evidence['coverage'] == 'partial'
    assert evidence['policy_ref'].startswith('policy-')
    assert any(row['policy_id'] == 'P-RET-01' and '7 天' in row['content'] for row in evidence['data'])
    assert any(m['role'] == 'user' and message_text(m) == original for m in first['messages'])
    assert all(m['role'] != 'tool' for m in first['messages'])
    assert all('P-RET-01' not in m['content'] for m in first['messages'] if m['role'] == 'system')
    assert 'search_after_sales_policy' in {tool['function']['name'] for tool in first['tools']}
    assert all('P-RET-01' in json.dumps(prefetched(body), ensure_ascii=False) for body in requests)
    text = result['message']
    assert all(part in text for part in ('P-RET-01', '2026-10-06', '7 天', '未知', '具体订单资格尚未核实', '未提交任何申请'))
    judgment = next(event for event in result['runtime_events'] if event['type'] == 'policy_judgment')
    assert judgment['outcome'] == 'yes' and judgment['elapsed_ms'] >= 0
    assert judgment['rules_version'] and judgment['usage'] is None
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    assert client.get('/api/v1/mercury/orders').json()['orders'] == []
    assert turn(client, original, 'prefetch-first')[-1]['payload'] == result
    assert len(policy_transport['calls']) == 2 and len(lookups) == 1


@pytest.mark.parametrize('decision', ['no', 'uncertain', 'timeout', 'error'])
def test_policy_judgment_fallback_keeps_ordinary_pi_policy_tools(pi_client, policy_transport, monkeypatch, caplog, decision):
    from app.mercury import policy
    from test_next_shared_policy_public import policy_hook
    client, requests = pi_client
    secret = 'PRIVATE_PROVIDER_RESPONSE_MUST_NOT_ESCAPE'
    policy_transport['choice'] = {'timeout': httpx.ReadTimeout(secret), 'error': httpx.ConnectError(secret)}.get(decision, decision)
    lookups = []
    search = policy.search_policies

    def observe(query, category=None):
        lookups.append((query, category))
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)

    def respond(body):
        if not [m for m in body['messages'] if m['role'] == 'tool']:
            assert lookups == [], 'Non-yes policy decisions must not prefetch'
        assert prefetched(body) is None
        assert 'search_after_sales_policy' in {tool['function']['name'] for tool in body['tools']}
        return policy_hook(body)

    requests.answer_hook = respond
    events = turn(client, '退货有什么条件？', 'policy-fallback-' + decision)
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert 'P-RET-01' in result['message']
    assert lookups == [('退货政策', 'return')]
    assert len(policy_transport['calls']) == 2
    judgment = next(event for event in result['runtime_events'] if event['type'] == 'policy_judgment')
    assert judgment['outcome'] == decision and judgment['elapsed_ms'] >= 0
    assert judgment['reason'] == {'timeout': 'ReadTimeout', 'error': 'ConnectError'}.get(decision)
    assert judgment['rules_version'] and judgment['usage'] is None
    assert secret not in caplog.text and secret not in json.dumps(events)
    if decision in ('timeout', 'error'):
        assert result['trace_id'] in caplog.text and 'policy_judgment' in caplog.text
        assert 'fingerprint' in caplog.text and 'frames' in caplog.text
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_prefetch_lookup_failure_is_observable_and_the_same_pi_can_recover(pi_client, policy_transport, monkeypatch, caplog):
    from app.mercury import policy
    client, requests = pi_client
    original = '查询退货条件'
    lookups = []
    search = policy.search_policies

    def flaky(query, category=None):
        lookups.append((query, category))
        if len(lookups) == 1:
            try:
                raise OSError('PRIVATE_POLICY_SOURCE_DETAIL')
            except OSError as cause:
                raise RuntimeError('PRIVATE_POLICY_LOOKUP_DETAIL') from cause
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', flaky)

    def respond(body):
        evidence = prefetched(body)
        assert evidence['outcome'] == 'error' and evidence['coverage'] == 'unknown'
        assert evidence['data'] is None and 'policy_ref' not in evidence
        assert evidence['query'] == original and evidence['category'] is None
        assert 'search_after_sales_policy' in {tool['function']['name'] for tool in body['tools']}
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(outputs) == 1:
            return call(body, 'search_after_sales_policy', {'query': '退货政策', 'category': 'return'})
        return answer({'status': 'completed', 'answer_kind': 'policy_result', 'policy_ref': outputs[-1]['policy_ref']})

    requests.answer_hook = respond
    events = turn(client, original, 'prefetch-lookup-error')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert 'P-RET-01' in result['message'] and '未找到匹配' not in result['message']
    assert lookups == [(original, None), ('退货政策', 'return')]
    acquisitions = [event for event in result['runtime_events'] if event['type'] == 'policy_lookup']
    assert [(event['origin'], event['outcome']) for event in acquisitions] == [('prefetch', 'error'), ('tool', 'success')]
    assert all(event['elapsed_ms'] >= 0 and event['source_version'] == '2026-10-06' for event in acquisitions)
    assert result['trace_id'] in caplog.text and 'policy_lookup' in caplog.text
    assert 'fingerprint' in caplog.text and 'OSError' in caplog.text and 'RuntimeError' in caplog.text
    assert 'PRIVATE_POLICY' not in caplog.text and 'PRIVATE_POLICY' not in json.dumps(events)
    assert client.get(BASE).json()['task_id'] is None and client.get('/api/v1/cart').json()['items'] == []


def test_waiting_policy_and_momo_boundary_all_survive_public_projection(pi_client, policy_transport):
    client, requests = pi_client
    original = '帮我选饮品，包装还没决定，说明退货条件，再查具体订单退款'

    def respond(body):
        evidence = prefetched(body)
        if not any(m['role'] == 'tool' for m in body['messages']):
            return call(body, 'guide_request', {'kind': 'question'})
        return answer({'status': 'waiting', 'clarification_slot': 'packaging',
                       'policy_ref': evidence['policy_ref'], 'role_boundary': True})

    requests.answer_hook = respond
    events = turn(client, original, 'waiting-policy-boundary')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['runtime_status'] == 'waiting'
    assert len(result['messages']) == 3
    assert '瓶装' in result['messages'][0]['content']
    assert 'P-RET-01' in result['messages'][1]['content']
    assert '具体订单、退款或退货事项由墨墨处理' in result['messages'][2]['content']
    assert result['pending_clarifications'] == [{'slot': 'packaging', 'question': result['message']}]
    assert result['navigation_action']['request']['target_role'] == 'momo'
    assert result['navigation_action']['request']['routing_request_id'] is None
    history = client.get(BASE + '/messages').json()['messages']
    assert [row['content'] for row in history if row['role'] == 'assistant'] == [row['content'] for row in result['messages']]
    assert all(row['kind'] != 'general' for row in history if row['role'] == 'assistant')
    assert client.get(BASE.replace('/guide/', '/navigation/') + '/opening').json()['role'] == 'keke'
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    assert client.get('/api/v1/mercury/orders').json()['orders'] == []


def test_general_units_keep_their_provenance_when_policy_and_boundary_are_appended(pi_client, policy_transport):
    from test_guide_clarification_context import context
    from test_guide_semantics import hook as conversation_hook
    client, requests = pi_client
    ordinary = ['彩虹来自阳光在水滴中的折射和反射。', '不同颜色偏折的角度不同，所以会分开。']

    def respond(body):
        if 'CERES_GENERAL_CLAIM_CHECK' in json.dumps(body['messages'], ensure_ascii=False):
            return answer({'merchant_claims': False, 'execution_claims': False})
        evidence = prefetched(body)
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(outputs) == 1:
            return call(body, 'validate_general_text', {'messages': ordinary})
        return answer({'status': 'completed', 'answer_kind': 'general_explanation',
                       'general_ref': outputs[-1]['general_ref'], 'policy_ref': evidence['policy_ref'], 'role_boundary': True})

    requests.answer_hook = respond
    events = turn(client, '解释彩虹原理、说明退货条件，也想查具体订单退款', 'general-policy-boundary')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['answer_kind'] == 'general_explanation'
    assert [row['content'] for row in result['messages'][:2]] == ordinary
    assert len(result['messages']) == 4
    assert 'P-RET-01' in result['messages'][2]['content']
    assert '具体订单、退款或退货事项由墨墨处理' in result['messages'][3]['content']
    history = client.get(BASE + '/messages').json()['messages']
    assert [row['content'] for row in history if row['kind'] == 'general'] == ordinary
    assert all(row['kind'] == 'text' for row in history if row['role'] == 'assistant' and row['content'] not in ordinary)
    policy_transport['choice'] = 'no'
    requests.clear()
    requests.answer_hook = conversation_hook
    later = turn(client, '再说说彩虹', 'after-mixed-general')
    assert later[-1]['type'] == 'turn.completed', later
    assert context(requests[0])['general_history'] == ordinary
    assert client.get(BASE).json()['task_id'] is None and client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('original, outcome', [('火星定制条款', 'empty'), ('退货条件和火星定制条款', 'success')])
def test_empty_and_partial_policy_facts_never_claim_complete_coverage(pi_client, policy_transport, original, outcome):
    client, requests = pi_client

    def respond(body):
        evidence = prefetched(body)
        if not any(m['role'] == 'tool' for m in body['messages']):
            return call(body, 'guide_request', {'kind': 'question'})
        return answer({'status': 'completed', 'answer_kind': 'policy_result',
                       'policy_ref': evidence['policy_ref'], 'message': '火星定制商品无条件永久可退，已经退款到账。'})

    requests.answer_hook = respond
    events = turn(client, original, 'policy-coverage-' + outcome)
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    evidence = prefetched(requests[0])
    assert evidence['outcome'] == outcome
    assert evidence['coverage'] == ('none' if outcome == 'empty' else 'partial')
    assert evidence['query'] == original and evidence['category'] is None
    text = result['message']
    assert '来源' in text and '2026-10-06' in text and '未知' in text
    assert '无条件永久可退' not in text and '已经退款到账' not in text
    if outcome == 'empty':
        assert '未找到匹配' in text and 'P-RET-01' not in text
    else:
        assert 'P-RET-01' in text and '未覆盖' in text
        assert '未找到匹配' not in text
    assert client.get(BASE).json()['task_id'] is None and client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('stage', ['prefetch', 'ordinary_tool'])
def test_deadline_after_blocking_progress_prevents_the_next_policy_read(pi_client, policy_transport, monkeypatch, stage):
    from sqlalchemy import event
    from app.mercury import policy
    from app.services import pi_product_runtime
    client, requests = pi_client
    policy_transport['choice'] = 'yes' if stage == 'prefetch' else 'no'
    clock = {'elapsed': 0.0}
    monkeypatch.setattr(pi_product_runtime, 'time', SimpleNamespace(monotonic=lambda: time.monotonic() + clock['elapsed']))
    lookups = []
    search = policy.search_policies

    def observe(query, category=None):
        lookups.append((query, category))
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)
    delayed = threading.Event()

    def stall_clock(_connection, _cursor, statement, parameters, _context, _many):
        if not delayed.is_set() and threading.current_thread().name.startswith('guide-') and statement.startswith('INSERT INTO guide_run_events') and 'retrieve' in str(parameters):
            # Simulate a blocking public progress write crossing the unchanged
            # 30-second deadline; only the runtime clock boundary is replaced.
            clock['elapsed'] = 31.0
            delayed.set()

    def respond(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'question'})
        return call(body, 'search_after_sales_policy', {'query': '退货政策'})

    requests.answer_hook = respond
    event.listen(requests.engine, 'after_cursor_execute', stall_clock)
    try:
        events = turn(client, '查询退货条件', 'late-progress-' + stage)
    finally:
        event.remove(requests.engine, 'after_cursor_execute', stall_clock)
    assert delayed.is_set()
    assert events[-1]['type'] == 'turn.completed', events
    assert events[-1]['payload']['runtime_status'] == 'deadline'
    assert lookups == [], 'Deadline must be rechecked after blocking on_phase before the actual read'
    assert len(requests) == (0 if stage == 'prefetch' else 2)
    assert 'P-RET-01' not in events[-1]['payload']['message']
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('boundary', ['publication_lock', 'staged_history'])
def test_policy_facts_cannot_publish_after_a_blocking_final_transaction(pi_client, policy_transport, monkeypatch, boundary):
    from sqlalchemy import event
    from app.services import pi_product_runtime, pi_product_turn_service
    client, requests = pi_client
    clock = {'elapsed': 0.0}
    clock_source = SimpleNamespace(monotonic=lambda: time.monotonic() + clock['elapsed'])
    monkeypatch.setattr(pi_product_runtime, 'time', clock_source)
    monkeypatch.setattr(pi_product_turn_service, 'time', clock_source, raising=False)
    answer_ready, delayed = threading.Event(), threading.Event()

    def respond(body):
        if not any(m['role'] == 'tool' for m in body['messages']):
            return call(body, 'guide_request', {'kind': 'question'})
        answer_ready.set()
        return answer({'status': 'completed', 'answer_kind': 'policy_result', 'policy_ref': prefetched(body)['policy_ref']})

    def stall_clock(_connection, _cursor, statement, _parameters, _context, _many):
        target = statement.startswith('UPDATE guide_sessions') if boundary == 'publication_lock' else statement.startswith('INSERT INTO guide_messages')
        if answer_ready.is_set() and not delayed.is_set() and threading.current_thread().name.startswith('guide-') and target:
            clock['elapsed'] = 31.0
            delayed.set()

    requests.answer_hook = respond
    event.listen(requests.engine, 'after_cursor_execute', stall_clock)
    try:
        events = turn(client, '说明退货条件', 'late-publication-' + boundary)
    finally:
        event.remove(requests.engine, 'after_cursor_execute', stall_clock)
    assert delayed.is_set()
    if boundary == 'publication_lock':
        assert events[-1]['type'] == 'turn.completed', events
        assert events[-1]['payload']['runtime_status'] == 'deadline'
    else:
        assert events[-1]['type'] == 'error', events
        assert events[-1]['payload']['code'] == 'PI_DEADLINE_EXCEEDED'
    assert all('P-RET-01' not in event['payload'].get('delta', '') for event in events)
    history = client.get(BASE + '/messages').json()['messages']
    assert all('P-RET-01' not in row['content'] for row in history)
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('operation', ['cart', 'memory'])
def test_late_final_transaction_rolls_back_staged_business_writes(pi_client, policy_transport, monkeypatch, operation):
    from sqlalchemy import event
    from app.services import pi_product_runtime, pi_product_turn_service
    from test_purchase_public import prepare, purchase_turn
    from test_memory_public import memory_turn
    client, requests = pi_client
    policy_transport['choice'] = 'no'
    before = prepare(client, requests) if operation == 'cart' else client.get(BASE).json()
    before_cart = client.get('/api/v1/cart').json()
    before_orders = client.get('/api/v1/mercury/orders').json()
    policy_transport['choice'] = 'yes'
    clock = {'elapsed': 0.0}
    clock_source = SimpleNamespace(monotonic=lambda: time.monotonic() + clock['elapsed'])
    monkeypatch.setattr(pi_product_runtime, 'time', clock_source)
    monkeypatch.setattr(pi_product_turn_service, 'time', clock_source, raising=False)
    delayed = threading.Event()

    def respond(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(outputs) == 1:
            return call(body, 'memory_command', {'action': 'save', 'category': 'user', 'domain': 'shopping',
                        'key': 'drink', 'content': '喜欢无糖饮品', 'source_quote': '请记住我喜欢无糖饮品'})
        return answer({'status': 'completed', 'answer_kind': 'memory_result', 'memory_ref': outputs[-1]['memory_ref'],
                       'policy_ref': prefetched(body)['policy_ref']})

    def stall_clock(_connection, _cursor, statement, _parameters, _context, _many):
        target = 'INSERT INTO cart_items' if operation == 'cart' else 'INSERT INTO shopping_memories'
        if not delayed.is_set() and threading.current_thread().name.startswith('guide-') and statement.startswith(target):
            clock['elapsed'] = 31.0
            delayed.set()

    requests.answer_hook = respond
    event.listen(requests.engine, 'after_cursor_execute', stall_clock)
    request_id = 'late-staged-' + operation
    try:
        events = purchase_turn(client, '就按这个加购', request_id) if operation == 'cart' else turn(client, '请记住我喜欢无糖饮品，也说明退货条件', request_id)
    finally:
        event.remove(requests.engine, 'after_cursor_execute', stall_clock)
    assert delayed.is_set()
    assert events[-1]['type'] == 'error', events
    assert events[-1]['payload']['code'] == 'PI_DEADLINE_EXCEEDED'
    assert not any(event['type'] == 'answer.delta' for event in events)
    assert client.get('/api/v1/cart').json() == before_cart
    assert client.get('/api/v1/mercury/orders').json() == before_orders
    after = client.get(BASE).json()
    assert after['plan'] == before['plan'] and after['state_version'] == before['state_version']
    assert not any(row['request_id'] == request_id for row in client.get(BASE + '/messages').json()['messages'])
    clock['elapsed'] = 0.0
    policy_transport['choice'] = 'no'
    assert memory_turn(client, requests, '查看全部记忆', {'action': 'list'}, 'after-late-' + operation)['records'] == []

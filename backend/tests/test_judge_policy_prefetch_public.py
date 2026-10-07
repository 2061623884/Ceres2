"""Policy prefetch through public Guide SSE and the actual Pi HTTP boundary."""
import json
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

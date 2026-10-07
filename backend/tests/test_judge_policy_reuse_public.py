"""Request-local policy reuse at public Guide SSE and actual Pi HTTP seams."""
import json

from test_runtime_pi_product_query import pi_client
from test_judge_policy_prefetch_public import policy_transport, prefetched
from test_guide_lifecycle import BASE
from test_guide_semantics import turn
from test_guide_clarification_context import answer, call


def test_prefetch_and_same_batch_exact_queries_return_the_same_complete_evidence(pi_client, policy_transport, monkeypatch):
    from app.mercury import policy
    client, requests = pi_client
    original = '退货政策'
    lookups = []
    search = policy.search_policies

    def observe(query, category=None):
        lookups.append((query, category))
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)

    def respond(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(outputs) == 1:
            return {'role': 'assistant', 'tool_calls': [
                {'index': index, 'id': f'repeat-{index}', 'type': 'function',
                 'function': {'name': 'search_after_sales_policy', 'arguments': json.dumps({'query': original})}}
                for index in range(2)
            ]}, 'tool_calls'
        return answer({'status': 'completed', 'answer_kind': 'policy_result', 'policy_ref': outputs[-1]['policy_ref']})

    requests.answer_hook = respond
    events = turn(client, original, 'reuse-batch')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert lookups == [(original, None)]
    evidence = prefetched(requests[0])
    returned = [json.loads(m['content']) for m in requests[-1]['messages'] if m['role'] == 'tool'][1:]
    assert returned == [evidence, evidence]
    assert 'scope' not in evidence
    assert evidence['data'] and 'P-RET-01' in result['message']
    assert result['tool_rounds'] == 2 and len(requests) == 3
    assert len([e for e in result['runtime_events'] if e['type'] == 'policy_lookup']) == 1
    reused = [e for e in result['runtime_events'] if e['type'] == 'policy_reuse']
    assert len(reused) == 2 and all(e['policy_ref'] == evidence['policy_ref'] for e in reused)
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_a_later_subquestion_does_not_retire_an_earlier_applicable_reference(pi_client, policy_transport):
    client, requests = pi_client

    def respond(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(outputs) == 1:
            return call(body, 'search_after_sales_policy', {'query': '配送进度规则'})
        return answer({'status': 'completed', 'answer_kind': 'policy_result',
                       'policy_ref': prefetched(body)['policy_ref']})

    requests.answer_hook = respond
    events = turn(client, '退货政策', 'earlier-policy-ref')
    assert events[-1]['type'] == 'turn.completed', events
    assert 'P-RET-01' in events[-1]['payload']['message']
    acquisitions = [e for e in events[-1]['payload']['runtime_events'] if e['type'] == 'policy_lookup']
    assert len(acquisitions) == 2
    assert acquisitions[0]['policy_ref'] != acquisitions[1]['policy_ref']


def test_an_acquired_reference_expires_when_the_authoritative_source_version_changes(pi_client, policy_transport, monkeypatch):
    from app.mercury import policy
    client, requests = pi_client

    def respond(body):
        if not any(m['role'] == 'tool' for m in body['messages']):
            return call(body, 'guide_request', {'kind': 'question'})
        monkeypatch.setattr(policy, 'POLICY_SOURCE_VERSION', 'controlled-v2')
        return answer({'status': 'completed', 'answer_kind': 'policy_result',
                       'policy_ref': prefetched(body)['policy_ref']})

    requests.answer_hook = respond
    events = turn(client, '退货政策', 'stale-source-ref')
    assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'PI_UNKNOWN_REFERENCE', events
    assert not any(e['type'] == 'answer.delta' for e in events)
    assert client.get(BASE + '/messages').json()['messages'] == []
    assert client.get('/api/v1/cart').json()['items'] == []

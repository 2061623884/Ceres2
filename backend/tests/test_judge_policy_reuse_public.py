"""Request-local policy reuse at public Guide SSE and actual Pi HTTP seams."""
import json

import pytest

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
    # Each reissued call carries the full body, so a model that no longer
    # retains earlier context can answer from the newest tool result alone.
    assert returned == [evidence, evidence]
    assert 'scope' not in evidence
    assert evidence['data'] and 'P-RET-01' in result['message']
    assert result['tool_rounds'] == 2 and len(requests) == 3
    assert len([e for e in result['runtime_events'] if e['type'] == 'turn_start']) == 3
    assert len([e for e in result['runtime_events'] if e['type'] == 'tool_execution_start' and e['toolName'] == 'search_after_sales_policy']) == 2
    assert len([e for e in result['runtime_events'] if e['type'] == 'policy_lookup']) == 1
    reused = [e for e in result['runtime_events'] if e['type'] == 'policy_reuse']
    assert len(reused) == 2 and all(e['policy_ref'] == evidence['policy_ref'] for e in reused)
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('shape', ['multiple', 'legacy_and_multiple'])
def test_multiple_policy_scopes_keep_all_actual_sources_and_query_boundaries(pi_client, policy_transport, shape):
    client, requests = pi_client

    def respond(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(outputs) == 1:
            return call(body, 'search_after_sales_policy', {'query': '配送进度规则'})
        result = {'status': 'completed', 'answer_kind': 'policy_result',
                  'policy_refs': [outputs[-1]['policy_ref']]}
        if shape == 'multiple':
            result['policy_refs'].insert(0, prefetched(body)['policy_ref'])
        else:
            result['policy_ref'] = prefetched(body)['policy_ref']
        return answer(result)

    requests.answer_hook = respond
    events = turn(client, '退货政策', 'many-policy-refs-' + shape)
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert all(value in result['message'] for value in ('P-RET-01', 'P-DEL-01', '退货政策', '配送进度规则', '未覆盖'))
    assert len([e for e in result['runtime_events'] if e['type'] == 'policy_lookup']) == 2
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


@pytest.mark.parametrize('change', ['subquestion', 'condition', 'exact_text', 'category', 'version'])
def test_only_the_exact_effective_query_scope_and_version_are_reused(pi_client, policy_transport, monkeypatch, change):
    from app.mercury import policy
    client, requests = pi_client
    original = '退货政策'
    arguments = {'query': {'subquestion': '配送进度规则', 'condition': '签收超过7天的退货政策',
                           'exact_text': '退货 政策'}.get(change, original)}
    if change == 'category':
        arguments['category'] = 'return'
    lookups, search = [], policy.search_policies

    def observe(query, category=None):
        lookups.append((query, category, policy.POLICY_SOURCE_VERSION))
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)

    def respond(body):
        rows = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not rows:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(rows) == 1 and change == 'version':
            monkeypatch.setattr(policy, 'POLICY_SOURCE_VERSION', 'controlled-v2')
        if len(rows) < 3:
            return call(body, 'search_after_sales_policy', arguments)
        return answer({'status': 'completed', 'answer_kind': 'policy_result', 'policy_ref': rows[-1]['policy_ref']})

    requests.answer_hook = respond
    events = turn(client, original, 'scope-change-' + change)
    assert events[-1]['type'] == 'turn.completed', events
    current_version = 'controlled-v2' if change == 'version' else '2026-10-06'
    assert lookups == [(original, None, '2026-10-06'), (arguments['query'], arguments.get('category'), current_version)]
    rows = [json.loads(m['content']) for m in requests[-1]['messages'] if m['role'] == 'tool']
    assert rows[-1] == rows[-2] and rows[-1]['data']
    assert rows[-1]['policy_ref'] != prefetched(requests[0])['policy_ref']
    assert rows[-1]['source_version'] == current_version
    result = events[-1]['payload']
    assert len([e for e in result['runtime_events'] if e['type'] == 'policy_lookup']) == 2
    assert len([e for e in result['runtime_events'] if e['type'] == 'policy_reuse']) == 1


@pytest.mark.parametrize('state', ['empty', 'recover', 'error'])
def test_empty_is_reusable_but_actual_failed_attempts_never_are(pi_client, policy_transport, monkeypatch, state):
    from app.mercury import policy
    client, requests = pi_client
    original = '火星定制条款' if state == 'empty' else '退货政策'
    lookups, search = [], policy.search_policies

    def observe(query, category=None):
        lookups.append((query, category))
        if state == 'error' or (state == 'recover' and len(lookups) == 1):
            raise OSError('controlled source failure')
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)

    def respond(body):
        rows = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not rows:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(rows) < 3:
            return call(body, 'search_after_sales_policy', {'query': original})
        result = {'status': 'completed', 'answer_kind': 'policy_result'}
        if state != 'error':
            result['policy_ref'] = rows[-1]['policy_ref']
        return answer(result)

    requests.answer_hook = respond
    events = turn(client, original, 'reuse-outcome-' + state)
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    actual_count, reuse_count = {'empty': (1, 2), 'recover': (2, 1), 'error': (3, 0)}[state]
    assert lookups == [(original, None)] * actual_count
    assert len([e for e in result['runtime_events'] if e['type'] == 'policy_lookup']) == actual_count
    assert len([e for e in result['runtime_events'] if e['type'] == 'policy_reuse']) == reuse_count
    summary = result['runtime_summary']
    assert summary['policy_lookups'] == actual_count and summary['policy_reuses'] == reuse_count
    assert summary['policy_tool_lookups'] == actual_count - 1
    assert summary['policy_lookup_outcomes'] == {
        'empty': {'success': 0, 'empty': 1, 'error': 0},
        'recover': {'success': 1, 'empty': 0, 'error': 1},
        'error': {'success': 0, 'empty': 0, 'error': 3},
    }[state]
    assert summary['events_truncated'] is False
    if state == 'error':
        assert '政策查询暂时失败' in result['message'] and '未找到匹配' not in result['message']
        assert all('policy_ref' not in e for e in result['runtime_events'] if e['type'] == 'policy_lookup')
    else:
        assert '政策查询暂时失败' not in result['message']
        assert ('未找到匹配' in result['message']) if state == 'empty' else ('P-RET-01' in result['message'])
    assert client.get('/api/v1/cart').json()['items'] == []


def test_request_and_owner_boundaries_always_acquire_their_own_evidence(pi_client, policy_transport, monkeypatch):
    from app.mercury import policy
    client, requests = pi_client
    lookups, search, refs = [], policy.search_policies, []

    def observe(query, category=None):
        lookups.append((query, category))
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)

    def respond(body):
        rows = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not rows:
            refs.append(prefetched(body)['policy_ref'])
            return call(body, 'guide_request', {'kind': 'question'})
        if len(rows) == 1:
            return call(body, 'search_after_sales_policy', {'query': '退货政策'})
        return answer({'status': 'completed', 'answer_kind': 'policy_result', 'policy_ref': rows[-1]['policy_ref']})

    requests.answer_hook = respond
    for owner, session, request_id in [('a', 'a', 'same-id'), ('a', 'a', 'new-id'), ('b', 'b', 'same-id')]:
        client.cookies.set('sg_owner_id', 'pi-owner-' + owner)
        target = BASE.replace('pi-session-a', 'pi-session-' + session)
        current = client.get(target).json()
        response = client.post(target + '/turns/stream', json={'request_id': request_id, 'message': '退货政策',
            'expected_task_id': current['task_id'], 'expected_state_version': current['state_version'],
            'expected_session_version': current['session_version']})
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        assert events[-1]['type'] == 'turn.completed', events
    assert len(set(refs)) == 3 and lookups == [('退货政策', None)] * 3


def test_bounded_event_tail_does_not_erase_actual_request_accounting(pi_client, policy_transport, monkeypatch):
    from app.mercury import policy
    client, requests = pi_client
    lookups, search = [], policy.search_policies

    def observe(query, category=None):
        lookups.append((query, category))
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)

    def respond(body):
        rows = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not rows:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(rows) < 49:
            # Three legal sequential batches, then a final answer: four tool
            # rounds total, with the production output/deadline caps unchanged.
            return {'role': 'assistant', 'tool_calls': [
                {'index': index, 'id': f'b{len(rows)}-{index}', 'type': 'function',
                 'function': {'name': 'search_after_sales_policy', 'arguments': '{"query":"退货"}'}}
                for index in range(16)
            ]}, 'tool_calls'
        return answer({'status': 'completed', 'answer_kind': 'policy_result', 'policy_ref': rows[-1]['policy_ref']})

    requests.answer_hook = respond
    events = turn(client, '退货', 'roll-runtime-event-tail')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['runtime_status'] == 'completed' and result['tool_rounds'] == 4
    assert len(requests) == 5 and all(body['max_completion_tokens'] == 1536 for body in requests)
    assert lookups == [('退货', None)] and 'P-RET-01' in result['message']
    assert len(result['runtime_events']) == 256
    assert not any(e['type'] == 'policy_judgment' for e in result['runtime_events'])
    summary = result['runtime_summary']
    assert summary['events_truncated'] is True
    assert summary['policy_lookups'] == 1 and summary['policy_tool_lookups'] == 0
    assert summary['policy_lookup_outcomes'] == {'success': 1, 'empty': 0, 'error': 0}
    assert summary['policy_reuses'] == 48 and summary['tool_starts'] == 49
    assert summary['primary_pi_turns'] == 5
    assert summary['policy_judgment']['outcome'] == 'yes'
    assert summary['policy_judgment']['rules_version'] and summary['policy_judgment']['usage'] is None
    assert summary['policy_judgment']['elapsed_ms'] >= 0
    assert client.get(BASE + '/turns/roll-runtime-event-tail').json()['result']['runtime_summary'] == summary
    assert client.get('/api/v1/cart').json()['items'] == []

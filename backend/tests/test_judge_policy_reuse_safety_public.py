"""Multi-ref trust, mixed results and interrupted reuse at public boundaries."""
import json
import threading
import time
from types import SimpleNamespace

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from test_runtime_pi_product_query import pi_client
from test_judge_policy_prefetch_public import policy_transport, prefetched
from test_judge_policy_safety_public import policy_answer, outputs
from test_guide_clarification_context import answer, call
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn


@pytest.mark.parametrize('source', ['forged', 'other_request', 'other_owner', 'old_version'])
@pytest.mark.parametrize('representation', ['legacy_invalid', 'list_invalid'])
def test_both_reference_forms_validate_every_supplied_value(pi_client, policy_transport, monkeypatch, source, representation):
    from app.mercury import policy
    client, requests = pi_client
    invalid_ref = 'policy-forged'
    target = BASE
    if source in ('other_request', 'other_owner'):
        requests.answer_hook = policy_answer
        assert turn(client, '退货政策', 'source-ref')[-1]['type'] == 'turn.completed'
        invalid_ref = prefetched(requests[0])['policy_ref']
        if source == 'other_owner':
            client.cookies.set('sg_owner_id', 'pi-owner-b')
            target = BASE.replace('pi-session-a', 'pi-session-b')

    def respond(body):
        rows = outputs(body)
        if not rows:
            return call(body, 'guide_request', {'kind': 'question'})
        if source == 'old_version' and len(rows) == 1:
            monkeypatch.setattr(policy, 'POLICY_SOURCE_VERSION', 'controlled-v2')
            return call(body, 'search_after_sales_policy', {'query': '退货政策'})
        valid = rows[-1]['policy_ref'] if source == 'old_version' else prefetched(body)['policy_ref']
        invalid = prefetched(body)['policy_ref'] if source == 'old_version' else invalid_ref
        result = {'status': 'completed', 'answer_kind': 'policy_result',
                  'policy_ref': invalid if representation == 'legacy_invalid' else valid,
                  'policy_refs': [valid] if representation == 'legacy_invalid' else [valid, invalid]}
        return answer(result)

    requests.answer_hook = respond
    state = client.get(target).json()
    response = client.post(target + '/turns/stream', json={'request_id': 'reject-all-supplied', 'message': '退货政策',
        'expected_task_id': state['task_id'], 'expected_state_version': state['state_version'],
        'expected_session_version': state['session_version']})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'PI_UNKNOWN_REFERENCE', events
    assert not any(e['type'] == 'answer.delta' for e in events)
    assert all(row['request_id'] != 'reject-all-supplied' for row in client.get(target + '/messages').json()['messages'])


@pytest.mark.parametrize('invalid', [None, [], 'policy-ref-string', [None], [['nested']]])
def test_a_valid_legacy_reference_does_not_hide_a_malformed_list(pi_client, policy_transport, invalid):
    client, requests = pi_client

    def respond(body):
        if not outputs(body):
            return call(body, 'guide_request', {'kind': 'question'})
        return answer({'status': 'completed', 'answer_kind': 'policy_result',
                       'policy_ref': prefetched(body)['policy_ref'], 'policy_refs': invalid})

    requests.answer_hook = respond
    events = turn(client, '退货政策', 'malformed-policy-list')
    assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'PI_UNKNOWN_REFERENCE', events
    assert client.get(BASE + '/messages').json()['messages'] == []


def test_mixed_purchase_keeps_all_scopes_and_confirmation_replay_has_no_new_work(pi_client, policy_transport, monkeypatch):
    from app.models.store import Store
    from app.mercury import policy
    from test_purchase_public import confirmation_body
    client, requests = pi_client
    with Session(requests.engine) as db:
        db.get(Store, 'pi-store').delivery_reachable = True
        db.commit()
    original = '选定两件测试可乐，预算10元，准备清单并说明退货政策及配送进度规则'
    lookups, search = [], policy.search_policies

    def observe(query, category=None):
        lookups.append((query, category))
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)

    def respond(body):
        rows = outputs(body)
        if not rows:
            return call(body, 'guide_request', {'kind': 'new_goal', 'goal': '买两件测试可乐',
                                               'conditions': {'quantity': 2, 'budget_fen': 1000}})
        if len(rows) == 1:
            return call(body, 'search_products', {'query': '测试可乐'})
        if len(rows) == 2:
            return call(body, 'search_after_sales_policy', {'query': '配送进度规则'})
        if len(rows) == 3:
            return call(body, 'propose_purchase', {'ref': rows[1]['products'][0]['ref'], 'quantity': 2})
        return answer({'status': 'completed', 'answer_kind': 'purchase_plan', 'proposal_ref': rows[-1]['proposal_ref'],
                       'policy_refs': [prefetched(body)['policy_ref'], rows[2]['policy_ref']]})

    requests.answer_hook = respond
    initial = client.get(BASE).json()
    body = {'request_id': 'mixed-purchase-refs', 'message': original, 'expected_task_id': initial['task_id'],
            'expected_state_version': initial['state_version'], 'expected_session_version': initial['session_version']}
    response = client.post(BASE + '/turns/stream', json=body)
    result = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')][-1]
    assert result['type'] == 'turn.completed', result
    result = result['payload']
    assert len(result['messages']) == 2 and result['plan']['items'][0]['quantity'] == 2
    assert all(value in result['messages'][1]['content'] for value in ('P-RET-01', 'P-DEL-01', original, '配送进度规则'))
    state = client.get(BASE).json()
    assert state['conditions'] == {'quantity': 2, 'budget_fen': 1000}
    assert client.get('/api/v1/cart').json()['items'] == []
    confirmed = client.post('/api/v1/guide/tasks/' + state['task_id'] + '/confirm',
                            json=confirmation_body(state), headers={'Idempotency-Key': 'mixed-confirm'})
    assert confirmed.status_code == 200, confirmed.text
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2
    before = (len(requests), len(lookups), len(policy_transport['calls']))
    replay = client.post(BASE + '/turns/stream', json=body)
    assert [json.loads(line[6:]) for line in replay.text.splitlines() if line.startswith('data: ')][-1]['payload'] == result
    assert client.get(BASE + '/turns/mixed-purchase-refs').json()['result'] == result
    assert client.post('/api/v1/guide/tasks/' + state['task_id'] + '/confirm',
                       json=confirmation_body(state), headers={'Idempotency-Key': 'mixed-confirm'}).json() == confirmed.json()
    assert before == (len(requests), len(lookups), len(policy_transport['calls']))
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2


def test_waiting_multi_scope_result_keeps_empty_scope_unknown_and_role_boundary(pi_client, policy_transport):
    client, requests = pi_client

    def respond(body):
        rows = outputs(body)
        if not rows:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(rows) == 1:
            return call(body, 'search_after_sales_policy', {'query': '火星定制条款'})
        return answer({'status': 'waiting', 'clarification_slot': 'packaging', 'role_boundary': True,
                       'policy_refs': [prefetched(body)['policy_ref'], rows[-1]['policy_ref']]})

    requests.answer_hook = respond
    events = turn(client, '帮我选饮品，说明退货政策及火星定制条款，再查具体订单', 'waiting-many-scopes')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['runtime_status'] == 'waiting' and len(result['messages']) == 3
    assert '瓶装' in result['messages'][0]['content']
    assert all(value in result['messages'][1]['content'] for value in ('P-RET-01', '火星定制条款', '未找到匹配', '规则未知'))
    assert '具体订单、退款或退货事项由墨墨处理' in result['messages'][2]['content']
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('interruption,guard', [('deadline', 'progress'), ('deadline', 'current_state'),
                                             ('stop', 'current_state'), ('new_goal', 'current_state')])
def test_reuse_obeys_guards_after_blocking_callbacks_and_replay_stays_terminal(pi_client, policy_transport, monkeypatch, interruption, guard):
    from app.mercury import policy
    from app.services import pi_product_runtime
    client, requests = pi_client
    search, lookups = policy.search_policies, []
    clock = {'elapsed': 0.0}
    monkeypatch.setattr(pi_product_runtime, 'time', SimpleNamespace(monotonic=lambda: time.monotonic() + clock['elapsed']))
    queued, phase_seen, blocked, release = (threading.Event() for _ in range(4))

    def observe(query, category=None):
        lookups.append((query, category))
        return search(query, category)

    monkeypatch.setattr(policy, 'search_policies', observe)

    def respond(body):
        rows = outputs(body)
        if not rows:
            return call(body, 'guide_request', {'kind': 'question'})
        queued.set()
        return call(body, 'search_after_sales_policy', {'query': '退货政策'})

    def after_sql(_connection, _cursor, statement, parameters, _context, _many):
        if not queued.is_set() or not threading.current_thread().name.startswith('guide-'):
            return
        progress = statement.startswith('INSERT INTO guide_run_events') and 'retrieve' in str(parameters)
        if progress:
            phase_seen.set()
        current = phase_seen.is_set() and statement.startswith('SELECT guide_sessions')
        if interruption == 'deadline' and not blocked.is_set() and ((guard == 'progress' and progress) or (guard == 'current_state' and current)):
            clock['elapsed'] = 31.0
            blocked.set()

    def before_sql(_connection, _cursor, statement, _parameters, _context, _many):
        if (interruption != 'deadline' and phase_seen.is_set() and not blocked.is_set()
                and threading.current_thread().name.startswith('guide-') and statement.startswith('SELECT guide_sessions')):
            blocked.set()
            assert release.wait(timeout=10)

    requests.answer_hook = respond
    event.listen(requests.engine, 'after_cursor_execute', after_sql)
    event.listen(requests.engine, 'before_cursor_execute', before_sql)
    request_id = 'reuse-interrupted-' + interruption + '-' + guard
    state = client.get(BASE).json()
    body = {'request_id': request_id, 'message': '退货政策', 'expected_task_id': state['task_id'],
            'expected_state_version': state['state_version'], 'expected_session_version': state['session_version']}
    try:
        admitted = client.post(BASE + '/runs', json=body)
        assert admitted.status_code == 202 and blocked.wait(timeout=5), admitted.text
        if interruption == 'stop':
            assert client.post(BASE + '/turns/stop', json={'request_id': request_id}).json()['cancelled'] is True
        elif interruption == 'new_goal':
            changed = command(client, 'new_goal', goal='买饮品')
            assert changed.status_code == 200, changed.text
        release.set()
        stream = client.get(BASE + '/runs/' + admitted.json()['run_id'] + '/stream')
    finally:
        release.set()
        event.remove(requests.engine, 'after_cursor_execute', after_sql)
        event.remove(requests.engine, 'before_cursor_execute', before_sql)
    events = [json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith('data: ')]
    if interruption == 'new_goal':
        assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'STALE_STATE', events
    else:
        assert events[-1]['payload']['runtime_status'] == ('stopped' if interruption == 'stop' else 'deadline'), events
        assert not any(e['type'] == 'policy_reuse' for e in events[-1]['payload']['runtime_events'])
        summary = events[-1]['payload']['runtime_summary']
        assert summary['policy_lookups'] == 1 and summary['policy_reuses'] == 0
        assert summary['events_truncated'] is False
    assert lookups == [('退货政策', None)] and len(requests) == 2
    assert not any('P-RET-01' in e['payload'].get('delta', '') for e in events)
    before = (len(requests), len(lookups), len(policy_transport['calls']))
    repeated = client.post(BASE + '/runs', json=body)
    assert repeated.status_code == 202 and repeated.json()['run_id'] == admitted.json()['run_id']
    assert client.get(BASE + '/runs/' + admitted.json()['run_id'] + '/events').json()['events'] == events
    assert before == (len(requests), len(lookups), len(policy_transport['calls']))
    assert client.get('/api/v1/cart').json()['items'] == []

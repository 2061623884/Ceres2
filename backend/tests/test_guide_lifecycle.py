"""TASK03 public lifecycle contracts. Synthetic data; real Pi fixture shared with P01."""
import json
from concurrent.futures import ThreadPoolExecutor
from test_runtime_pi_product_query import pi_client

BASE = '/api/v1/guide/sessions/pi-session-a'


def entry(client):
    return client.post('/api/v1/guide/sessions', json={'entry_context': {'page': 'home', 'store_id': 'pi-store', 'delivery_zone_id': 'zone-default'}})


def command(client, kind, *, snapshot=None, goal=None, conditions=None):
    snapshot = snapshot or client.get(BASE).json()
    return client.post(BASE + '/tasks/current', json={
        'request_id': kind + '-' + str(snapshot['session_version']) + '-' + str(snapshot['state_version']),
        'kind': kind, 'goal': goal, 'conditions': conditions,
        'expected_task_id': snapshot['task_id'], 'expected_state_version': snapshot['state_version'],
        'expected_session_version': snapshot['session_version'],
    })


def test_owner_reenters_one_canonical_session_preserving_history(pi_client):
    client, _ = pi_client
    first = entry(client)
    second = entry(client)
    assert first.status_code == second.status_code == 200
    assert first.json()['session_id'] == second.json()['session_id'] == 'pi-session-a'
    client.cookies.set('sg_owner_id', 'pi-owner-b')
    assert entry(client).json()['session_id'] == 'pi-session-b'


def test_new_goal_amend_abandon_are_versioned_and_do_not_touch_cart(pi_client):
    client, _ = pi_client
    before = client.get('/api/v1/cart').json()
    started = command(client, 'new_goal', goal='选可乐')
    assert started.status_code == 200, started.text
    one = started.json()
    assert one['task_id'] and one['task_status'] == 'active'
    amended = command(client, 'amend', conditions={'budget_fen': 1000})
    assert amended.status_code == 200, amended.text
    assert amended.json()['task_id'] == one['task_id']
    assert amended.json()['state_version'] == one['state_version'] + 1
    assert amended.json()['conditions']['budget_fen'] == 1000
    assert command(client, 'amend', snapshot=one, conditions={'budget_fen': 2000}).status_code == 409
    changed = command(client, 'new_goal', goal='选牛奶')
    assert changed.status_code == 200
    assert changed.json()['task_id'] != one['task_id']
    abandoned = command(client, 'abandon')
    assert abandoned.status_code == 200
    assert abandoned.json()['task_id'] is None
    tasks = client.get(BASE + '/tasks').json()['tasks']
    assert {t['status'] for t in tasks} == {'superseded', 'abandoned'}
    assert client.get('/api/v1/cart').json() == before


def test_command_replay_does_not_create_second_task_and_rejects_body_conflict(pi_client):
    client, _ = pi_client
    snapshot = client.get(BASE).json()
    first = command(client, 'new_goal', snapshot=snapshot, goal='选可乐')
    replay = command(client, 'new_goal', snapshot=snapshot, goal='选可乐')
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert command(client, 'new_goal', snapshot=snapshot, goal='选牛奶').status_code == 409
    assert len(client.get(BASE + '/tasks').json()['tasks']) == 1


def test_owner_cannot_read_or_change_other_task_lifecycle(pi_client):
    client, _ = pi_client
    started = command(client, 'new_goal', goal='选可乐')
    assert started.status_code == 200
    client.cookies.set('sg_owner_id', 'pi-owner-b')
    assert client.get(BASE + '/tasks').status_code == 403
    assert command(client, 'abandon', snapshot=started.json()).status_code == 403


def test_run_admission_is_durable_before_stop_and_status_does_not_cancel(pi_client):
    client, requests = pi_client
    started = command(client, 'new_goal', goal='选可乐').json()
    body = {'request_id': 'durable-slow', 'message': '受控慢查询可乐', 'expected_task_id': started['task_id'], 'expected_state_version': started['state_version'], 'expected_session_version': started['session_version']}
    accepted = client.post(BASE + '/runs', json=body)
    assert accepted.status_code == 202, accepted.text
    run = accepted.json()
    assert requests.started.wait(timeout=5)
    state = client.get(BASE + '/status').json()
    assert state['task_id'] == started['task_id']
    assert state['runs'][0]['run_id'] == run['run_id']
    assert state['runs'][0]['status'] == 'running'
    assert state['runs'][0]['input']['message'] == body['message']
    stopped = client.post(BASE + '/turns/stop', json={'request_id': body['request_id']})
    assert stopped.json()['cancelled'] is True
    response = client.get(BASE + f"/runs/{run['run_id']}/stream")
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.stopped', events
    assert events[-1]['payload']['task_id'] == started['task_id']
    assert client.get(BASE).json()['task_status'] == 'active'
    replay = client.get(BASE + f"/runs/{run['run_id']}/events", params={'after_sequence': events[0]['sequence']}).json()['events']
    assert replay == events[1:]
    assert [e['sequence'] for e in events] == list(range(1, len(events) + 1))
    requests.release.set()


def test_detached_run_finishes_and_replay_does_not_reexecute_model(pi_client):
    client, requests = pi_client
    body = {'request_id': 'detached', 'message': '查可乐', 'expected_state_version': 0, 'expected_session_version': 0}
    accepted = client.post(BASE + '/runs', json=body)
    assert accepted.status_code == 202, accepted.text
    run_id = accepted.json()['run_id']
    response = client.get(BASE + f'/runs/{run_id}/stream')
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed'
    original = client.get(BASE + f'/runs/{run_id}/events').json()
    repeated = client.post(BASE + '/runs', json=body)
    assert repeated.status_code == 202
    assert repeated.json()['run_id'] == run_id
    assert client.get(BASE + f'/runs/{run_id}/events').json() == original
    assert len(requests) == 3
    client.cookies.set('sg_owner_id', 'pi-owner-b')
    assert client.get(BASE + f'/runs/{run_id}/events').status_code == 403


def test_amendment_keeps_original_run_anchor_and_fences_stale_result(pi_client):
    client, requests = pi_client
    started = command(client, 'new_goal', goal='选可乐').json()
    body = {'request_id': 'refined-slow', 'message': '受控慢查询可乐', 'expected_task_id': started['task_id'], 'expected_state_version': started['state_version'], 'expected_session_version': started['session_version']}
    accepted = client.post(BASE + '/runs', json=body)
    assert accepted.status_code == 202, accepted.text
    assert requests.started.wait(timeout=5)
    amended = command(client, 'amend', conditions={'budget_fen': 1000})
    assert amended.status_code == 200
    requests.release.set()
    response = client.get(BASE + f"/runs/{accepted.json()['run_id']}/stream")
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error'
    assert events[-1]['payload']['code'] == 'STALE_STATE'
    receipt = client.get(BASE + '/status').json()['runs'][0]
    assert receipt['anchor']['state_version'] == 0
    assert client.get(BASE).json()['state_version'] == 1
    assert not any('测试可乐' in row['content'] for row in client.get(BASE + '/messages').json()['messages'])


def test_message_pagination_and_completed_stop_return_actual_receipt(pi_client):
    client, _ = pi_client
    body = {'request_id': 'already-complete', 'message': '查可乐', 'expected_state_version': 0, 'expected_session_version': 0}
    response = client.post(BASE + '/turns/stream', json=body)
    terminal = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')][-1]
    stop = client.post(BASE + '/turns/stop', json={'request_id': body['request_id']}).json()
    assert stop['cancelled'] is False
    assert stop['result'] == terminal['payload']
    first = client.get(BASE + '/messages', params={'after_sequence': 0, 'limit': 1}).json()
    assert len(first['messages']) == 1
    second = client.get(BASE + '/messages', params={'after_sequence': first['messages'][0]['sequence'], 'limit': 1}).json()
    assert len(second['messages']) == 1
    assert second['messages'][0]['role'] == 'assistant'


def test_legacy_session_is_readable_but_cannot_create_second_active_task(pi_client):
    client, requests = pi_client
    from sqlalchemy.orm import Session
    from app.models.guide import GuideSession
    with Session(requests.engine) as db:
        db.add(GuideSession(session_id='zz-legacy', owner_id='pi-owner-a', entry_context_json=json.dumps({'page': 'home', 'store_id': 'pi-store', 'delivery_zone_id': 'zone-default'})))
        db.commit()
    started = command(client, 'new_goal', goal='选可乐')
    assert started.status_code == 200
    assert client.get('/api/v1/guide/sessions/zz-legacy').status_code == 200
    refused = client.post('/api/v1/guide/sessions/zz-legacy/tasks/current', json={'request_id': 'second-task', 'kind': 'new_goal', 'goal': '买牛奶', 'expected_task_id': None, 'expected_state_version': 0, 'expected_session_version': 0})
    assert refused.status_code == 409
    assert refused.json()['error']['code'] == 'LEGACY_SESSION_READ_ONLY'
    assert client.get(BASE).json()['task_id'] == started.json()['task_id']


def test_host_failure_logs_safe_locations_and_cause_chain_not_provider_text(pi_client, caplog):
    client, requests = pi_client
    from sqlalchemy import event
    def fail_with_private_cause(_conn, _cursor, statement, *_args):
        if 'SELECT catalog_products.category_id' in statement:
            try:
                raise ValueError('secret-inner-provider-body')
            except ValueError as cause:
                raise RuntimeError('secret-outer-provider-token') from cause
    event.listen(requests.engine, 'before_cursor_execute', fail_with_private_cause)
    try:
        client.post(BASE + '/turns/stream', json={'request_id': 'diagnostic-chain', 'message': '查可乐', 'expected_state_version': 0, 'expected_session_version': 0})
    finally:
        event.remove(requests.engine, 'before_cursor_execute', fail_with_private_cause)
    assert 'fail_with_private_cause' in caplog.text
    assert 'ValueError' in caplog.text
    assert 'test_guide_lifecycle.py' in caplog.text
    assert 'secret-inner-provider-body' not in caplog.text
    assert 'secret-outer-provider-token' not in caplog.text

"""Fifteen-second admitted-run budget at public Guide HTTP/SSE seams."""
import json
import time

import pytest

from test_runtime_pi_product_query import pi_client
from test_judge_policy_prefetch_public import policy_transport
from test_judge_policy_safety_public import policy_answer
from test_guide_lifecycle import BASE


@pytest.mark.parametrize('endpoint', ['/runs', '/turns/stream'])
def test_guide_ingress_passes_one_fifteen_second_deadline_and_replay_does_not_restart(pi_client, policy_transport, monkeypatch, endpoint):
    from app.api import guide
    from app.services.knowledge_service import knowledge
    client, requests = pi_client
    requests.answer_hook = policy_answer
    launches, lookup_deadlines = [], []
    launch, search = guide.launch_run, knowledge.search

    def observe_launch(factory, owner_id, session_id, body, run_id, deadline):
        launches.append((time.monotonic(), deadline))
        return launch(factory, owner_id, session_id, body, run_id, deadline)

    def observe_search(*args, **kwargs):
        lookup_deadlines.append(kwargs['deadline'])
        return search(*args, **kwargs)

    monkeypatch.setattr(guide, 'launch_run', observe_launch)
    monkeypatch.setattr(knowledge, 'search', observe_search)
    state = client.get(BASE).json()
    body = {'request_id': 'fifteen-second-ingress', 'message': '退货条件',
            'expected_task_id': state['task_id'], 'expected_state_version': state['state_version'],
            'expected_session_version': state['session_version']}
    response = client.post(BASE + endpoint, json=body)
    if endpoint == '/runs':
        assert response.status_code == 202
        run_id = response.json()['run_id']
        response = client.get(BASE + f'/runs/{run_id}/stream')
    else:
        run_id = client.get(BASE + '/turns/' + body['request_id']).json()['run_id']
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    assert len(launches) == 1
    assert 14.0 < launches[0][1] - launches[0][0] <= 15.0
    assert lookup_deadlines == [launches[0][1]]
    provider_calls = len(requests)
    replay = client.post(BASE + endpoint, json=body)
    assert replay.status_code in (200, 202)
    reconnect = client.get(BASE + f'/runs/{run_id}/stream')
    assert 'turn.completed' in reconnect.text
    assert len(launches) == 1 and len(requests) == provider_calls

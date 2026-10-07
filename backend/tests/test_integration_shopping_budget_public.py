"""Original Guide budget survives product retrieval and question re-projection."""
import json
import time

from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_clarification_context import call


def test_native_exploration_and_reprojection_keep_original_request_budget(pi_client, controlled_product_source, monkeypatch):
    from app.api import guide
    client, requests = pi_client
    control = controlled_product_source
    command(client, 'new_goal', goal='可乐', conditions={'query':'可乐'})
    state = client.get(BASE).json()
    launches = []
    original = guide.launch_run
    def launch(factory, owner_id, session_id, body, run_id, deadline):
        launches.append(deadline)
        return original(factory, owner_id, session_id, body, run_id, deadline)
    monkeypatch.setattr(guide, 'launch_run', launch)
    def respond(body):
        outputs = [json.loads(message['content']) for message in body['messages'] if message['role']=='tool']
        if not outputs:
            return call(body, 'guide_request', {'kind':'continue'})
        if len(outputs)==1:
            return call(body, 'explore_products', {'category_id':'beverage','query':'可乐'})
        return call(body, 'finish_response', {'status':'completed','answer_kind':'exploration','exploration_ref':outputs[-1]['exploration_ref']})
    requests.answer_hook = respond
    body = {'request_id':'budget-explore','message':'查看可乐', 'expected_task_id':state['task_id'],
        'expected_state_version':state['state_version'],'expected_session_version':state['session_version']}
    response = client.post(BASE+'/turns/stream', json=body)
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type']=='turn.completed', events
    assert len(launches)==1
    assert len(control['calls'])>=2  # Tool evidence and final current-question projection.
    assert all(row['deadline']==launches[0] for row in control['calls'])
    before = len(control['calls'])
    started = time.monotonic()
    recovered = client.get(BASE).json()
    assert recovered['active_question']['question_id']==events[-1]['payload']['active_question']['question_id']
    assert len(control['calls'])>before
    assert all(started < row['deadline'] <= started+15.2 for row in control['calls'][before:])
    assert client.get('/api/v1/cart').json()['items']==[]

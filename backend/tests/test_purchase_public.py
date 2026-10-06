"""TASK04 public Pi proposal and authoritative confirmation journeys."""
import json
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn


def purchase_hook(body):
    outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
    def call(name, args):
        return {'role':'assistant','tool_calls':[{'index':0,'id':f'tool-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
    if not outputs:
        return call('guide_request', {'kind':'continue'})
    if len(outputs) == 1:
        return call('search_products', {'query':'测试可乐'})
    if len(outputs) == 2:
        return call('propose_purchase', {'ref':outputs[-1]['products'][0]['ref'], 'quantity':2})
    return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'purchase_plan','proposal_ref':outputs[-1]['proposal_ref']})}, 'stop'


def prepare(client, requests):
    from sqlalchemy import update
    from sqlalchemy.orm import Session
    from app.models.store import Store
    with Session(requests.engine) as db:
        db.execute(update(Store).where(Store.store_id == 'pi-store').values(delivery_reachable=True))
        db.commit()
    command(client, 'new_goal', goal='买两件测试可乐')
    requests.answer_hook = purchase_hook
    events = turn(client, '选定测试可乐，两件，先给我清单', 'prepare')
    assert events[-1]['type'] == 'turn.completed', events
    state = client.get(BASE).json()
    assert state['plan'] is not None, events
    assert state['plan']['items'][0]['quantity'] == 2
    assert 'modify' in state['available_actions']
    assert client.get('/api/v1/cart').json()['items'] == []
    return state


def confirmation_body(state):
    return {'plan_id':state['plan']['plan_id'], 'plan_version':state['plan']['plan_version'], 'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'], 'selected_items':[{'sku_id':'pi-cola','quantity':2}]}


def test_explicit_selection_persists_plan_then_button_confirmation_is_atomic_and_replayable(pi_client):
    client, requests = pi_client
    state = prepare(client, requests)
    url = '/api/v1/guide/tasks/' + state['task_id'] + '/confirm'
    body = confirmation_body(state)
    first = client.post(url, json=body, headers={'Idempotency-Key':'confirm-1'})
    assert first.status_code == 200, first.text
    receipt = first.json()
    assert receipt['items_added'] == [{'sku_id':'pi-cola','quantity':2}]
    assert receipt['status'] == 'success'
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2
    assert client.post(url, json=body, headers={'Idempotency-Key':'confirm-1'}).json() == receipt
    assert client.post(url, json=body, headers={'Idempotency-Key':'other-key'}).status_code == 409
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2
    restored = client.get(BASE).json()
    assert restored['confirmation_result'] == receipt
    assert restored['plan']['items'][0]['added_quantity'] == 2



def purchase_turn(client, message, request_id, shown=None):
    state = client.get('/api/v1/guide/sessions/pi-session-a').json()
    shown = shown if shown is not None else state
    plan = shown.get('plan')
    displayed = {'task_id':shown['task_id'], 'plan_id':plan['plan_id'], 'plan_version':plan['plan_version'], 'state_version':shown['state_version'], 'session_version':shown['session_version']} if plan else None
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream',json={'request_id':request_id,'message':message,'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],'displayed_plan':displayed})
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]

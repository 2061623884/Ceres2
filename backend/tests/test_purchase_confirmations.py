"""Dual confirmation entry points, unambiguous authority and revision fences."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_purchase_public import prepare, confirmation_body
from test_purchase_public import purchase_turn as turn
from test_guide_lifecycle import BASE, command


def test_explicit_text_uses_same_real_cart_and_durable_receipt(pi_client):
    client, requests = pi_client
    state = prepare(client, requests)
    events = turn(client, '就按这个加购', 'text-confirm')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['confirmation_result']['items_added'] == [{'sku_id':'pi-cola','quantity':2}]
    assert result['committed'] is True
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2
    receipt = client.get(BASE + '/turns/text-confirm').json()
    assert receipt['result']['confirmation_result'] == result['confirmation_result']
    assert client.get(BASE).json()['confirmation_result'] == result['confirmation_result']
    retry = client.post('/api/v1/guide/tasks/' + state['task_id'] + '/confirm', json=confirmation_body(state), headers={'Idempotency-Key':'cross-entry'})
    assert retry.status_code == 409


@pytest.mark.parametrize('message', ['好的', '可以', '“就按这个加购”是用户以前说的', '上次那份就按这个加购'])
def test_ack_or_quoted_old_confirmation_never_authorizes_write(pi_client, message):
    client, requests = pi_client
    prepare(client, requests)
    # A malicious/incorrect model may claim confirmation. It cannot mint it.
    requests.answer_hook = lambda body: ({'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'confirm_purchase','confirmed':True})}, 'stop')
    turn(client, message, 'ambiguous')
    assert client.get('/api/v1/cart').json()['items'] == []


def test_selection_revision_invalidates_old_confirmation_and_persists_ui_state(pi_client):
    client, requests = pi_client
    state = prepare(client, requests)
    path = '/api/v1/guide/tasks/' + state['task_id']
    revised = client.post(path + '/plan-revisions', json={'request_id':'revise-1', 'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'], 'base_plan_id':state['plan']['plan_id'], 'base_plan_version':state['plan']['plan_version'], 'coverage_intent':'selection_only', 'items':[{'sku_id':'pi-cola','quantity':3,'selected':True}]})
    assert revised.status_code == 200, revised.text
    assert revised.json()['plan_version'] == 2
    assert client.post(path + '/confirm', json=confirmation_body(state), headers={'Idempotency-Key':'old-plan'}).status_code == 409
    current = client.get(BASE).json()
    assert current['plan']['items'][0]['quantity'] == 3
    body = confirmation_body(current)
    body['selected_items'][0]['quantity'] = 3
    confirmed = client.post(path + '/confirm', json=body, headers={'Idempotency-Key':'new-plan'})
    assert confirmed.status_code == 200, confirmed.text
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 3


def test_stale_displayed_anchor_cannot_confirm_newer_plan_by_text(pi_client):
    client, requests = pi_client
    shown = prepare(client, requests)
    path = '/api/v1/guide/tasks/' + shown['task_id']
    revised = client.post(path + '/plan-revisions',json={'request_id':'other-tab','expected_state_version':shown['state_version'],'expected_session_version':shown['session_version'],'base_plan_id':shown['plan']['plan_id'],'base_plan_version':shown['plan']['plan_version'],'coverage_intent':'selection_only','items':[{'sku_id':'pi-cola','quantity':3,'selected':True}]})
    assert revised.status_code == 200
    response = client.post(BASE + '/turns/stream',json={'request_id':'confirm-shown-old','message':'就按这个加购','expected_task_id':shown['task_id'],'expected_state_version':shown['state_version'],'expected_session_version':shown['session_version']})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error'
    assert events[-1]['payload']['code'] == 'STALE_STATE'
    assert client.get('/api/v1/cart').json()['items'] == []


def test_purchase_reply_displays_actual_sku_count_and_price_before_confirmation(pi_client):
    client, requests = pi_client
    prepare(client, requests)
    history = client.get(BASE + '/messages').json()['messages']
    text = history[-1]['content']
    assert '测试可乐' in text
    assert '2' in text
    assert '7.00' in text


def test_fresh_run_anchor_never_substitutes_for_unseen_displayed_plan(pi_client):
    client, requests = pi_client
    shown = prepare(client, requests)
    path = '/api/v1/guide/tasks/' + shown['task_id']
    client.post(path + '/plan-revisions',json={'request_id':'other-tab-fresh','expected_state_version':shown['state_version'],'expected_session_version':shown['session_version'],'base_plan_id':shown['plan']['plan_id'],'base_plan_version':shown['plan']['plan_version'],'coverage_intent':'selection_only','items':[{'sku_id':'pi-cola','quantity':3,'selected':True}]})
    current = client.get(BASE).json()
    response = client.post(BASE + '/turns/stream',json={'request_id':'fresh-run-old-display','message':'就按这个加购','expected_task_id':current['task_id'],'expected_state_version':current['state_version'],'expected_session_version':current['session_version'],'displayed_plan':{'task_id':shown['task_id'],'plan_id':shown['plan']['plan_id'],'plan_version':shown['plan']['plan_version'],'state_version':shown['state_version'],'session_version':shown['session_version']}})
    assert response.status_code == 200, response.text
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error'
    assert events[-1]['payload']['code'] == 'DISPLAYED_PLAN_STALE'
    assert client.get('/api/v1/cart').json()['items'] == []

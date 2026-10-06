"""Approved budget negotiation: factual quote acceptance is not cart authority."""
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_dish_public import dish_seed, prepare_dish
from test_multidish_public import confirm_body


def accept_quote(client, state, key='accept-quote'):
    return client.post('/api/v1/guide/tasks/' + state['task_id'] + '/plan-revisions', json={
        'request_id':key, 'base_plan_id':state['plan']['plan_id'], 'base_plan_version':state['plan']['plan_version'],
        'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'],
        'coverage_intent':'accept_quote', 'items':[]})


def test_factual_over_budget_quote_requires_separate_acceptance_and_cart_confirmation(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client, 'new_goal', goal='番茄炒蛋，预算10元', conditions={'budget_fen':1000})
    state = prepare_dish(client, requests)
    plan = state['plan']
    assert plan['budget_quote'] == {'budget_fen':1000, 'total_fen':1500}
    assert plan['can_confirm'] is False
    assert state['conditions']['budget_fen'] == 1000
    assert '15.00' in client.get(BASE + '/messages').text
    url = '/api/v1/guide/tasks/' + state['task_id'] + '/confirm'
    old_body = confirm_body(state)
    assert client.post(url, json=old_body, headers={'Idempotency-Key':'before-quote'}).status_code == 409
    assert client.get('/api/v1/cart').json()['items'] == []
    accepted = accept_quote(client, state)
    assert accepted.status_code == 200, accepted.text
    assert accept_quote(client, state).json() == accepted.json()
    current = client.get(BASE).json()
    assert current['conditions']['budget_fen'] == 1500
    assert 'budget_quote' not in current['plan']
    assert current['plan']['can_confirm'] is True
    assert client.get('/api/v1/cart').json()['items'] == []
    assert client.post(url, json=old_body, headers={'Idempotency-Key':'old-approval'}).status_code == 409
    assert client.post(url, json=confirm_body(current), headers={'Idempotency-Key':'after-quote'}).status_code == 200
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']} == {'tomato-500':1,'egg-6':1}


def test_changed_supply_rejects_old_quote_without_relaxing_budget(pi_client):
    from sqlalchemy import update
    from sqlalchemy.orm import Session
    from app.models.store import Offer
    client, requests = pi_client
    dish_seed(requests)
    command(client, 'new_goal', goal='番茄炒蛋', conditions={'budget_fen':1000})
    state = prepare_dish(client, requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='tomato-500').values(price_fen=800, offer_version=2))
        db.commit()
    assert accept_quote(client, state).status_code == 409
    assert client.get(BASE).json()['conditions']['budget_fen'] == 1000
    assert client.get('/api/v1/cart').json()['items'] == []
    refreshed = prepare_dish(client, requests, request_id='refresh-price')
    assert refreshed['plan']['budget_quote'] == {'budget_fen':1000,'total_fen':1700}
    assert accept_quote(client, refreshed, 'accept-current').status_code == 200
    current = client.get(BASE).json()
    assert current['conditions']['budget_fen'] == 1700
    assert client.get('/api/v1/cart').json()['items'] == []


def test_quote_acceptance_keeps_supply_choice_and_later_budget_checks_separate(pi_client):
    from sqlalchemy import update
    from sqlalchemy.orm import Session
    from app.models.store import Offer
    from test_supply_public import supply_revision
    from test_dish_public import revise_dish
    client, requests = pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=0))
        db.commit()
    command(client, 'new_goal', goal='番茄炒蛋', conditions={'budget_fen':1000})
    state = prepare_dish(client, requests)
    assert state['plan']['plan_kind'] == 'supply_preview'
    assert accept_quote(client, state).status_code == 200
    current = client.get(BASE).json()
    assert current['conditions']['budget_fen'] == 1500
    assert current['plan']['can_confirm'] is False
    assert current['plan']['plan_kind'] == 'supply_preview'
    assert supply_revision(client,current,'choose-current-partial','choose_partial').status_code == 200
    current = client.get(BASE).json()
    assert current['plan']['plan_kind'] == 'partial_purchase'
    assert current['plan']['can_confirm'] is True
    assert client.get('/api/v1/cart').json()['items'] == []
    assert revise_dish(client,current,'more-people',people=8).status_code == 200
    expanded = client.get(BASE).json()
    assert expanded['conditions']['budget_fen'] == 1500
    assert expanded['plan']['budget_quote']['total_fen'] > 1500
    assert expanded['plan']['can_confirm'] is False
    assert client.get('/api/v1/cart').json()['items'] == []

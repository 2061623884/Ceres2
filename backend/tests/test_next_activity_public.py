"""Existing homepage activity uses the ordinary public product/plan authority."""
from sqlalchemy.orm import Session
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn


ACTIVITY_SKUS = {'demo:AC-salad-250g-box', 'demo:AC-fruit-platter-300g-box', 'demo:AC-juice-300ml-bottle'}


@pytest.fixture
def activity_client(pi_client):
    """Use shipped demo supply and normal public cart creation, not pi-store's empty cart."""
    from sqlalchemy import select
    from app.models.cart import Cart, CartItem
    from app.services.seed_service import seed_catalog
    client, requests = pi_client
    with Session(requests.engine) as db:
        seed_catalog(db)
        cart = db.scalar(select(Cart).where(Cart.owner_id == 'pi-owner-a'))
        assert not db.scalars(select(CartItem).where(CartItem.cart_id == cart.id)).all()
        db.delete(cart)
        db.commit()
    assert client.get('/api/v1/cart').json()['store_id'] == 'store-demo-01'
    return client, requests


def activity_entry(client, requests, request_id='activity-first'):
    from app.services.seed_service import seed_catalog
    with Session(requests.engine) as db:
        seed_catalog(db)
        db.commit()
    before = client.get(BASE).json()
    switched = client.post(BASE+'/supply-context', json={'request_id':'activity-store', 'store_id':'store-demo-01', 'delivery_zone_id':'zone-default', 'expected_session_version':before['session_version']})
    assert switched.status_code == 200, switched.text
    snapshot = switched.json()
    body = {'request_id':request_id, 'expected_task_id':snapshot['task_id'], 'expected_state_version':snapshot['state_version'], 'expected_session_version':snapshot['session_version']}
    return client.post(BASE+'/activities/light-meal', json=body), body


def test_existing_activity_entry_returns_only_finished_demo_products_without_model_or_cart(activity_client, controlled_kev_transport):
    client, requests = activity_client
    cart_before = client.get('/api/v1/cart').json()
    result, body = activity_entry(client, requests)
    assert result.status_code == 200, result.text
    state = result.json()
    assert state['conditions']['activity_id'] == 'light-meal'
    question = state['active_question']
    assert question['kind'] == 'products'
    assert {o['value'] for o in question['options']} == ACTIVITY_SKUS
    for option in question['options']:
        product = option['product']
        assert product['source'] == 'demo'
        assert product['metadata']['finished_product'] is True
        assert product['metadata']['activity_ids'] == ['light-meal']
        assert not product['ingredient_ids']
        assert product['price_fen'] > 0 and product['available_qty'] > 0
        assert product['spec_quantity'] > 0
        assert not product['metadata'].get('attribute_evidence')
    assert state['plan'] is None
    assert client.get('/api/v1/cart').json() == cart_before
    assert len(requests) == 0
    assert controlled_kev_transport['entry_calls'] == []
    repeated = client.post(BASE+'/activities/light-meal', json=body)
    assert repeated.status_code == 200 and repeated.json() == state
    assert client.get(BASE).json()['active_question'] == question


def test_activity_raw_model_search_cannot_escape_finished_pool_without_routing(activity_client):
    import json
    client, requests = activity_client
    entered, _ = activity_entry(client, requests)
    assert entered.status_code == 200, entered.text
    def search_hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return {'role':'assistant','tool_calls':[{'index':0,'id':'raw-search','type':'function','function':{'name':'search_products','arguments':json.dumps({'category_id':'beverage'})}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','product_refs':[p['ref'] for p in outputs[-1]['products']]})}, 'stop'
    requests.answer_hook = search_hook
    events = turn(client, '看看活动里的饮品', 'activity-raw-search')
    assert events[-1]['type'] == 'turn.completed', events
    state = events[-1]['payload']
    assert {p['sku_id'] for p in state['product_evidence']} == {'demo:AC-juice-300ml-bottle'}
    assert client.get('/api/v1/cart').json()['items'] == []


def test_activity_comparison_preserves_hard_dietary_constraints(activity_client):
    import json
    client, requests = activity_client
    retained = {'excluded_allergens':['peanut'], 'budget_fen':5000, 'quantity':2}
    assert command(client, 'new_goal', goal='有过敏限制的采购', conditions=retained).status_code == 200
    entered, _ = activity_entry(client, requests)
    assert entered.status_code == 200, entered.text
    assert entered.json()['conditions'] == {**retained, 'activity_id':'light-meal'}
    assert entered.json()['active_question']['options'] == []
    def compare_hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return {'role':'assistant','tool_calls':[{'index':0,'id':'activity-compare','type':'function','function':{'name':'compare_products','arguments':json.dumps({'category_id':'beverage'})}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'comparison','product_refs':[p['ref'] for p in outputs[-1]['products']]})}, 'stop'
    requests.answer_hook = compare_hook
    events = turn(client, '比较活动里的饮品，过敏限制保持不变', 'activity-compare-hard')
    assert events[-1]['type'] == 'turn.completed', events
    assert events[-1]['payload']['product_evidence'] == []
    assert events[-1]['payload']['product_cards'] == []
    assert client.get(BASE).json()['conditions'] == {**retained, 'activity_id':'light-meal'}
    assert client.get('/api/v1/cart').json()['items'] == []


def test_activity_scope_is_host_owned_and_explicit_new_goal_exits(activity_client):
    from test_next_snack_public import answer_question
    client, requests = activity_client
    entered, _ = activity_entry(client, requests)
    assert entered.status_code == 200
    question = entered.json()['active_question']
    escaped = command(client, 'amend', conditions={'activity_id':None})
    assert escaped.status_code == 422, escaped.text
    assert client.get(BASE).json()['conditions']['activity_id'] == 'light-meal'
    cart_before = client.get('/api/v1/cart').json()
    changed = command(client, 'new_goal', goal='改为买可乐', conditions={'category_id':'beverage'})
    assert changed.status_code == 200, changed.text
    assert 'activity_id' not in changed.json()['conditions']
    restored = client.get(BASE).json()
    assert restored['active_question'] is None
    assert restored['question_history'][0]['status'] == 'stale'
    old = answer_question(client, question, [question['options'][0]['option_id']], 'old-activity-choice', {question['options'][0]['option_id']:1})
    assert old.status_code == 409
    assert client.get('/api/v1/cart').json() == cart_before


def confirm_activity(client, state, key):
    plan = state['plan']
    return client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm', json={
        'plan_id':plan['plan_id'], 'plan_version':plan['plan_version'],
        'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'],
        'selected_items':[{'sku_id':r['sku_id'], 'quantity':r['quantity']} for r in plan['items']],
    }, headers={'Idempotency-Key':key})


@pytest.mark.parametrize('choices', [
    {'demo:AC-salad-250g-box':1, 'demo:AC-juice-300ml-bottle':2},
    {'demo:AC-fruit-platter-300g-box':2},
])
def test_activity_model_composes_selected_finished_skus_then_separate_confirmation(activity_client, controlled_kev_transport, choices):
    from test_next_snack_public import selection_hook
    client, requests = activity_client
    entered, _ = activity_entry(client, requests)
    question = entered.json()['active_question']
    selected = [{'option_id':o['option_id'], 'quantity':choices[o['value']]} for o in question['options'] if o['value'] in choices]
    requests.answer_hook = selection_hook(question['question_id'], selected)
    events = turn(client, '按我选定的这些成品和数量生成清单', 'activity-dynamic-choice')
    assert events[-1]['type'] == 'turn.completed', events
    state = client.get(BASE).json()
    assert {r['sku_id']:r['quantity'] for r in state['plan']['items']} == choices
    prices = {o['value']:o['product']['price_fen'] for o in question['options']}
    assert state['plan']['selected_total_fen'] == sum(prices[sku]*quantity for sku, quantity in choices.items())
    assert len(controlled_kev_transport['entry_calls']) == 1
    assert client.get('/api/v1/cart').json()['items'] == []
    confirmed = confirm_activity(client, state, 'activity-confirm')
    repeated = confirm_activity(client, state, 'activity-confirm')
    assert confirmed.status_code == repeated.status_code == 200, confirmed.text
    assert confirmed.json() == repeated.json()
    cart = client.get('/api/v1/cart').json()
    assert {r['sku_id']:r['quantity'] for r in cart['items']} == choices
    assert command(client, 'new_goal', goal='改买普通零食').status_code == 200
    assert client.get('/api/v1/cart').json() == cart
    assert 'activity_id' not in client.get(BASE).json()['conditions']


@pytest.mark.parametrize('change', ['price', 'stock', 'membership'])
def test_activity_confirmation_rechecks_current_offer_and_membership(activity_client, change):
    import json
    from sqlalchemy import select
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    from test_next_snack_public import answer_question
    client, requests = activity_client
    entered, _ = activity_entry(client, requests)
    question = entered.json()['active_question']
    chosen = next(o for o in question['options'] if o['value'] == 'demo:AC-salad-250g-box')
    prepared = answer_question(client, question, [chosen['option_id']], 'activity-prepare', {chosen['option_id']:1})
    assert prepared.status_code == 200, prepared.text
    state = client.get(BASE).json()
    with Session(requests.engine) as db:
        offer = db.scalar(select(Offer).where(Offer.sku_id == chosen['value']))
        if change == 'price':
            offer.price_fen += 100
            offer.offer_version += 1
        elif change == 'stock':
            offer.available_qty = 0
            offer.offer_version += 1
        else:
            product = db.get(CatalogProduct, chosen['value'])
            metadata = json.loads(product.metadata_json)
            metadata['activity_ids'] = []
            product.metadata_json = json.dumps(metadata)
        db.commit()
    rejected = confirm_activity(client, state, 'activity-changed-confirm')
    assert rejected.status_code == 409, rejected.text
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('conditions, expected', [
    ({'budget_fen':1000}, {'demo:AC-juice-300ml-bottle'}),
    ({'budget_fen':2000, 'quantity':2}, {'demo:AC-juice-300ml-bottle'}),
    ({'quantity':13}, {'demo:AC-juice-300ml-bottle'}),
    ({'exclusions':['demo:AC-juice-300ml-bottle']}, ACTIVITY_SKUS-{'demo:AC-juice-300ml-bottle'}),
    ({'dietary_requirements':['low_sugar']}, set()),
])
def test_activity_entry_retains_current_hard_constraints(activity_client, conditions, expected):
    client, requests = activity_client
    assert command(client, 'new_goal', goal='按当前条件选购', conditions=conditions).status_code == 200
    entered, _ = activity_entry(client, requests)
    assert entered.status_code == 200, entered.text
    state = entered.json()
    assert state['conditions'] == {**conditions, 'activity_id':'light-meal'}
    assert {o['value'] for o in state['active_question']['options']} == expected
    assert state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_activity_recipe_request_cannot_expand_finished_products_into_ingredients(activity_client):
    import json
    client, requests = activity_client
    assert activity_entry(client, requests)[0].status_code == 200
    requests.answer_hook = lambda body: ({'role':'assistant','tool_calls':[{'index':0,'id':'recipe','type':'function','function':{'name':'search_dishes','arguments':json.dumps({'query':'沙拉'})}}]}, 'tool_calls')
    events = turn(client, '看看这个活动能做什么菜', 'activity-no-recipe')
    assert events[-1]['type'] == 'error', events
    assert 'ACTIVITY_SCOPE_CONFLICT' in json.dumps(events)
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_activity_seed_never_resets_mutable_offer_and_old_supply_choice_stales(activity_client):
    from sqlalchemy import select
    from app.models.store import Offer
    from app.services.seed_service import seed_catalog
    from test_next_snack_public import answer_question
    client, requests = activity_client
    entered, _ = activity_entry(client, requests)
    question = entered.json()['active_question']
    chosen = question['options'][0]
    with Session(requests.engine) as db:
        offer = db.scalar(select(Offer).where(Offer.sku_id == chosen['value']))
        offer.available_qty = 0
        offer.price_fen = 100
        offer.offer_version += 1
        db.commit()
        seed_catalog(db)
        db.commit()
        assert offer.available_qty == 0 and offer.price_fen == 100
    restored = client.get(BASE).json()
    assert restored['active_question'] is None
    assert restored['question_history'][0]['status'] == 'stale'
    assert answer_question(client, question, [chosen['option_id']], 'activity-stale', {chosen['option_id']:1}).status_code == 409
    assert client.get('/api/v1/cart').json()['items'] == []

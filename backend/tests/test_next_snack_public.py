"""TASK01 public journey: controlled provider, actual Pi and authoritative API/SSE."""
import json
from sqlalchemy.orm import Session
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn


def seed_snacks(requests):
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer, Store
    with Session(requests.engine) as db:
        db.get(Store, 'pi-store').delivery_reachable = True
        for sku, name, kind, label, price in [
            ('snack-chips', '原味薯片70克', 'potato_chips', '薯片', 600),
            ('snack-chips-small', '原味薯片35克', 'potato_chips', '薯片', 400),
            ('snack-crackers', '苏打饼干100克', 'soda_crackers', '饼干', 800),
        ]:
            db.add(CatalogProduct(sku_id=sku, name=name, name_zh=name, category_id='snack', product_type=kind, spec_quantity=70 if sku == 'snack-chips' else 100, spec_unit='g', metadata_json=json.dumps({'type_label':label,'pack_count':1,'packaging':'bag'})))
            db.flush()
            db.add(Offer(store_id='pi-store', sku_id=sku, price_fen=price, available_qty=5))
        db.commit()


def exploration_hook(body):
    outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
    if len(outputs) < 2:
        name, args = ('guide_request', {'kind':'continue'}) if not outputs else ('explore_products', {'category_id':'snack'})
        return {'role':'assistant','tool_calls':[{'index':0,'id':f'explore-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
    return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'exploration','exploration_ref':outputs[-1].get('exploration_ref', 'missing')})}, 'stop'


def test_generic_snack_opens_one_supply_derived_question_without_purchase(pi_client):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='来点零食', conditions={'budget_fen':1000})
    requests.answer_hook = exploration_hook
    events = turn(client, '来点零食', 'snack-first')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    question = result['active_question']
    assert question['kind'] == 'category'
    assert {o['label'] for o in question['options']} == {'薯片', '饼干'}
    assert len({o['option_id'] for o in question['options']}) == 2
    assert question['question_id'] and question['status'] == 'active'
    assert result['plan'] is None
    restored = client.get(BASE).json()
    assert restored['active_question'] == question
    assert restored['question_history'] == [question]
    assert client.get('/api/v1/cart').json()['items'] == []


def answer_question(client, question, option_ids, request_id, quantities=None):
    return client.post(BASE + '/questions/' + question['question_id'] + '/answers', json={
        'request_id':request_id, 'option_ids':option_ids, 'quantities':quantities or {},
        'expected_task_id':question['task_id'], 'expected_state_version':question['state_version'],
        'expected_session_version':question['session_version'],
    })


def test_category_and_multiple_product_choices_prepare_plan_then_explicit_idempotent_cart(pi_client):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='买零食', conditions={'budget_fen':3000})
    requests.answer_hook = exploration_hook
    question = turn(client, '来点零食', 'multi-first')[-1]['payload']['active_question']
    chips = next(o for o in question['options'] if o['label'] == '薯片')
    calls_before = len(requests)
    picked = answer_question(client, question, [chips['option_id']], 'multi-type')
    assert picked.status_code == 200, picked.text
    candidates = picked.json()['active_question']
    assert candidates['kind'] == 'products'
    assert {o['value'] for o in candidates['options']} == {'snack-chips', 'snack-chips-small'}
    assert picked.json()['question_history'][0]['status'] == 'answered'
    assert picked.json()['question_history'][0]['selected_option_ids'] == [chips['option_id']]
    assert client.get('/api/v1/cart').json()['items'] == []
    selected = [o['option_id'] for o in candidates['options']]
    prepared = answer_question(client, candidates, selected, 'multi-products', {oid:1 for oid in selected})
    assert prepared.status_code == 200, prepared.text
    state = client.get(BASE).json()
    assert len(requests) == calls_before, 'Structured choices must not call a model'
    assert {r['sku_id'] for r in state['plan']['items']} == {'snack-chips', 'snack-chips-small'}
    assert state['plan']['selected_total_fen'] == 1000
    assert state['active_question'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    body = {'plan_id':state['plan']['plan_id'], 'plan_version':state['plan']['plan_version'],
            'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'],
            'selected_items':[{'sku_id':r['sku_id'],'quantity':r['quantity']} for r in state['plan']['items']]}
    first = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm', json=body, headers={'Idempotency-Key':'snack-confirm'})
    again = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm', json=body, headers={'Idempotency-Key':'snack-confirm'})
    assert first.status_code == again.status_code == 200
    assert first.json() == again.json()
    assert sorted((r['sku_id'],r['quantity']) for r in client.get('/api/v1/cart').json()['items']) == [('snack-chips',1),('snack-chips-small',1)]


def test_free_text_answers_displayed_type_after_cart_aside_and_preserves_history(pi_client):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='零食', conditions={'budget_fen':1000})
    requests.answer_hook = exploration_hook
    question = turn(client, '来点零食', 'text-first')[-1]['payload']['active_question']
    chips = next(o for o in question['options'] if o['label'] == '薯片')
    client.get('/api/v1/cart')
    assert client.get(BASE).json()['active_question']['question_id'] == question['question_id']
    def answer_hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            name, args = ('guide_request', {'kind':'continue'}) if not outputs else ('explore_products', {'category_id':'snack', 'product_type':'potato_chips', 'answer_question_id':question['question_id']})
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'answer-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'exploration','exploration_ref':outputs[-1].get('exploration_ref', 'missing')})}, 'stop'
    requests.answer_hook = answer_hook
    events = turn(client, '薯片，预算还是十元', 'text-answer')
    assert events[-1]['type'] == 'turn.completed', events
    state = client.get(BASE).json()
    assert state['conditions']['budget_fen'] == 1000
    assert state['question_history'][0]['status'] == 'answered'
    assert state['question_history'][0]['selected_option_ids'] == [chips['option_id']]
    assert state['active_question']['kind'] == 'products'
    assert all(o['product']['product_type'] == 'potato_chips' for o in state['active_question']['options'])
    assert any(question['question_id'] in m['content'] for request in requests for m in request['messages'] if m['role'] == 'system'), 'Current question identity must reach the text interpreter'
    assert client.get('/api/v1/cart').json()['items'] == []


def test_supply_change_invalidates_restored_question_and_rejects_old_choice(pi_client):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='零食')
    requests.answer_hook = exploration_hook
    question = turn(client, '来点零食', 'supply-first')[-1]['payload']['active_question']
    from app.models.store import Offer
    from sqlalchemy import select
    with Session(requests.engine) as db:
        offer = db.scalar(select(Offer).where(Offer.sku_id == 'snack-chips'))
        offer.price_fen = 900
        offer.offer_version += 1
        db.commit()
    restored = client.get(BASE).json()
    assert restored['active_question'] is None
    assert restored['question_history'][0]['status'] == 'stale'
    result = answer_question(client, question, [question['options'][0]['option_id']], 'supply-old')
    assert result.status_code == 409, result.text
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_unknown_allergens_never_satisfy_explicit_safety_constraint(pi_client):
    client, requests = pi_client
    seed_snacks(requests)
    conditions = {'budget_fen':1000, 'quantity':2, 'excluded_allergens':['peanut']}
    command(client, 'new_goal', goal='两包不含花生的零食', conditions=conditions)
    requests.answer_hook = exploration_hook
    result = turn(client, '花生过敏，两包零食，十元以内', 'safety-unknown')[-1]['payload']
    assert result['active_question']['options'] == [], 'Unknown allergen evidence is not allergy-safe supply'
    state = client.get(BASE).json()
    assert state['conditions'] == conditions
    assert state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    assert '未知' in result['message'] or '无法核实' in result['message']


def test_allergen_evidence_change_blocks_plan_confirmation_without_cart_write(pi_client):
    client, requests = pi_client
    seed_snacks(requests)
    from app.models.catalog import CatalogProduct
    with Session(requests.engine) as db:
        for sku in ('snack-chips', 'snack-chips-small', 'snack-crackers'):
            p = db.get(CatalogProduct, sku)
            metadata = json.loads(p.metadata_json)
            metadata['attribute_evidence'] = {'allergens':{'value':[], 'source':'controlled-fixture:complete-allergen-statement'}}
            p.metadata_json = json.dumps(metadata)
        db.commit()
    command(client, 'new_goal', goal='不含花生零食', conditions={'excluded_allergens':['peanut']})
    requests.answer_hook = exploration_hook
    q = turn(client, '不含花生的零食', 'allergen-first')[-1]['payload']['active_question']
    chips = next(o for o in q['options'] if o['label'] == '薯片')
    q = answer_question(client, q, [chips['option_id']], 'allergen-type').json()['active_question']
    chosen = q['options'][0]
    assert answer_question(client, q, [chosen['option_id']], 'allergen-plan', {chosen['option_id']:1}).status_code == 200
    state = client.get(BASE).json()
    with Session(requests.engine) as db:
        p = db.get(CatalogProduct, chosen['value'])
        metadata = json.loads(p.metadata_json)
        metadata['attribute_evidence']['allergens']['value'] = ['peanut']
        p.metadata_json = json.dumps(metadata)
        db.commit()
    confirmed = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm', json={
        'plan_id':state['plan']['plan_id'], 'plan_version':state['plan']['plan_version'],
        'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'],
        'selected_items':[{'sku_id':chosen['value'],'quantity':1}],
    }, headers={'Idempotency-Key':'unsafe-changed'})
    assert confirmed.status_code == 409, confirmed.text
    assert confirmed.json()['error']['code'] == 'DIETARY_CONFLICT'
    assert client.get('/api/v1/cart').json()['items'] == []


def selection_hook(question_id, selections):
    def hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            name, args = ('guide_request', {'kind':'continue'}) if not outputs else ('select_question_products', {'question_id':question_id, 'selections':selections})
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'choice-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'question_selection','selection_ref':outputs[-1].get('selection_ref','missing')})}, 'stop'
    return hook


def test_text_product_choice_asks_only_missing_quantity_then_prepares_without_cart(pi_client):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='零食', conditions={'budget_fen':2000})
    requests.answer_hook = exploration_hook
    category = turn(client, '来点零食', 'quantity-first')[-1]['payload']['active_question']
    chips = next(o for o in category['options'] if o['label'] == '薯片')
    question = answer_question(client, category, [chips['option_id']], 'quantity-type').json()['active_question']
    large = next(o for o in question['options'] if o['value'] == 'snack-chips')
    requests.answer_hook = selection_hook(question['question_id'], [{'option_id':large['option_id']}])
    events = turn(client, '选70克这一款', 'quantity-missing')
    assert events[-1]['type'] == 'turn.completed', events
    pending = events[-1]['payload']['active_question']
    assert pending['kind'] == 'quantity'
    assert [o['value'] for o in pending['options']] == ['snack-chips']
    assert client.get(BASE).json()['plan'] is None
    requests.answer_hook = selection_hook(pending['question_id'], [{'option_id':pending['options'][0]['option_id'], 'quantity':2}])
    first_request = len(requests)
    events = turn(client, '两包', 'quantity-answer')
    assert events[-1]['type'] == 'turn.completed', events
    from test_guide_clarification_context import context
    initial_context = context(requests[first_request])
    assert initial_context['active_question'] == pending
    assert initial_context['current_task']['conditions'] == {'budget_fen':2000}
    assert 'capability' not in initial_context
    state = client.get(BASE).json()
    assert state['active_question'] is None
    assert all(q['status'] == 'answered' for q in state['question_history'])
    assert [(r['sku_id'],r['quantity']) for r in state['plan']['items']] == [('snack-chips',2)]
    assert state['conditions']['budget_fen'] == 2000
    assert client.get('/api/v1/cart').json()['items'] == []


def test_repeatable_released_catalog_supports_real_snack_types_and_package_choices(pi_client):
    client, requests = pi_client
    from app.services.seed_service import seed_catalog
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    from sqlalchemy import select
    with Session(requests.engine) as db:
        seed_catalog(db)
        # Represents a catalog already imported before the new labels existed.
        for sku in ('demo:snack-original-potato-chips-70g-bag', 'demo:snack-soda-crackers-100g-box'):
            p = db.get(CatalogProduct, sku)
            metadata = json.loads(p.metadata_json); metadata.pop('type_label', None)
            p.metadata_json = json.dumps(metadata)
        offer = db.scalar(select(Offer).where(Offer.sku_id == 'demo:snack-original-potato-chips-70g-bag'))
        offer.available_qty = 4
        db.commit()
        seed_catalog(db)
        db.commit()
    before = client.get(BASE).json()
    switched = client.post(BASE+'/supply-context', json={'request_id':'fixture-store', 'store_id':'store-demo-01', 'delivery_zone_id':'zone-default', 'expected_session_version':before['session_version']})
    assert switched.status_code == 200, switched.text
    command(client, 'new_goal', goal='零食')
    requests.answer_hook = exploration_hook
    result = turn(client, '来点零食', 'fixture-snack')[-1]['payload']
    question = result['active_question']
    assert question['kind'] == 'category'
    assert {o['label'] for o in question['options']} == {'薯片','苏打饼干'}
    choice = next(o for o in question['options'] if o['value'] == 'potato_chips')
    selected = answer_question(client, question, [choice['option_id']], 'fixture-type')
    assert selected.status_code == 200, selected.text
    products = [o['product'] for o in selected.json()['active_question']['options']]
    assert {(p['spec_quantity'],p['spec_unit']) for p in products} == {(35,'g'),(70,'g')}
    assert next(p for p in products if p['spec_quantity'] == 70)['available_qty'] == 4, 'Repeat import must not reset mutable Offer inventory'
    assert all(p['price_fen'] is not None and p['source'] == 'demo' for p in products)
    assert client.get('/api/v1/cart').json()['items'] == []


def test_existing_packaging_constraint_is_not_silently_dropped_during_exploration(pi_client):
    client, requests = pi_client
    seed_snacks(requests)
    conditions = {'pack_count_mode':'multi', 'budget_fen':2000}
    command(client, 'new_goal', goal='多件装零食', conditions=conditions)
    requests.answer_hook = exploration_hook
    result = turn(client,'保留多件装条件看看零食','keep-pack-mode')[-1]['payload']
    assert result['active_question']['options'] == []
    assert client.get(BASE).json()['conditions'] == conditions
    assert client.get('/api/v1/cart').json()['items'] == []

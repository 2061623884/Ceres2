"""TASK04 controlled public drink journey; no live retailer/model claims."""
import json
from sqlalchemy.orm import Session
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_next_snack_public import answer_question


def seed_drinks(requests):
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer, Store
    with Session(requests.engine) as db:
        db.get(Store, 'pi-store').delivery_reachable = True
        for sku, kind, label, brand, flavor, volume, price in [
            ('DR-tea-peach-small', 'tea', '茶饮', '演示甲', '桃味', 330, 400),
            ('DR-tea-peach-large', 'tea', '茶饮', '演示甲', '桃味', 500, 600),
            ('DR-tea-lemon', 'tea', '茶饮', '演示乙', '柠檬味', 500, 500),
            ('DR-tea-unknown', 'tea', '茶饮', None, None, 500, 300),
            ('DR-water', 'water', '饮用水', '演示甲', None, 550, 200),
        ]:
            if db.get(CatalogProduct, sku) is None:
                metadata = {'type_label':label, 'pack_count':1, 'packaging':'bottle'}
                if flavor is not None:
                    metadata['flavor'] = flavor
                db.add(CatalogProduct(sku_id=sku, name=sku, name_zh=sku, category_id='beverage', brand=brand, product_type=kind, spec_quantity=volume, spec_unit='ml', metadata_json=json.dumps(metadata)))
                db.flush()
                db.add(Offer(store_id='pi-store', sku_id=sku, price_fen=price, available_qty=5))
        db.commit()


def drink_hook(body):
    outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
    if len(outputs) < 2:
        name, args = ('guide_request', {'kind':'continue'}) if not outputs else ('explore_products', {'category_id':'beverage'})
        return {'role':'assistant','tool_calls':[{'index':0,'id':f'drink-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
    return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'exploration','exploration_ref':outputs[-1].get('exploration_ref', 'missing')})}, 'stop'


def test_drink_type_then_factual_flavor_filter_preserves_constraints_and_requires_cart_consent(pi_client):
    client, requests = pi_client
    seed_drinks(requests)
    command(client, 'new_goal', goal='喝点东西', conditions={'budget_fen':2000, 'quantity':1})
    requests.answer_hook = drink_hook
    question = turn(client, '喝点东西', 'DR-first')[-1]['payload']['active_question']
    assert question['kind'] == 'category'
    assert {o['label'] for o in question['options']} == {'茶饮', '饮用水'}
    tea = next(o for o in question['options'] if o['value'] == 'tea')
    typed = answer_question(client, question, [tea['option_id']], 'DR-type')
    assert typed.status_code == 200, typed.text
    products = typed.json()['active_question']
    assert products['kind'] == 'products'
    filters = products['filter_options']
    assert {o['value'] for o in filters if o['attribute'] == 'flavor'} == {'桃味', '柠檬味'}
    assert all(o['value'] not in ('未知', '') for o in filters)
    peach = next(o for o in filters if o['attribute'] == 'flavor' and o['value'] == '桃味')
    calls_before = len(requests)
    filtered = answer_question(client, products, [peach['option_id']], 'DR-flavor')
    assert filtered.status_code == 200, filtered.text
    state = filtered.json()
    assert state['conditions']['budget_fen'] == 2000 and state['conditions']['quantity'] == 1
    assert state['conditions']['flavor'] == '桃味'
    current = state['active_question']
    assert {o['value'] for o in current['options']} == {'DR-tea-peach-small', 'DR-tea-peach-large'}
    client.get('/api/v1/cart')
    assert client.get(BASE).json()['active_question']['question_id'] == current['question_id']
    assert state['question_history'][-2]['status'] == 'answered'
    ids = [o['option_id'] for o in current['options']]
    prepared = answer_question(client, current, ids, 'DR-products', {oid:1 for oid in ids})
    assert prepared.status_code == 200, prepared.text
    state = prepared.json()
    assert state['plan']['selected_total_fen'] == 1000
    assert len(requests) == calls_before
    assert client.get('/api/v1/cart').json()['items'] == []
    body = {'plan_id':state['plan']['plan_id'], 'plan_version':state['plan']['plan_version'],
            'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'],
            'selected_items':[{'sku_id':r['sku_id'],'quantity':r['quantity']} for r in state['plan']['items']]}
    confirmed = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm', json=body, headers={'Idempotency-Key':'DR-confirm'})
    assert confirmed.status_code == 200, confirmed.text
    assert sorted((r['sku_id'],r['quantity']) for r in client.get('/api/v1/cart').json()['items']) == [('DR-tea-peach-large',1),('DR-tea-peach-small',1)]


def test_changed_drink_flavor_after_plan_is_rechecked_before_confirmation(pi_client):
    client, requests = pi_client
    seed_drinks(requests)
    command(client, 'new_goal', goal='桃味茶', conditions={'product_type':'tea', 'flavor':'桃味'})
    requests.answer_hook = drink_hook
    question = turn(client, '桃味茶', 'DR-change-first')[-1]['payload']['active_question']
    assert question['kind'] == 'products'
    option = question['options'][0]
    state = answer_question(client, question, [option['option_id']], 'DR-change-select', {option['option_id']:1}).json()
    from app.models.catalog import CatalogProduct
    with Session(requests.engine) as db:
        product = db.get(CatalogProduct, option['value'])
        metadata = json.loads(product.metadata_json)
        metadata['flavor'] = '柠檬味'
        product.metadata_json = json.dumps(metadata)
        db.commit()
    body = {'plan_id':state['plan']['plan_id'], 'plan_version':state['plan']['plan_version'],
            'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'],
            'selected_items':[{'sku_id':r['sku_id'],'quantity':r['quantity']} for r in state['plan']['items']]}
    response = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm', json=body, headers={'Idempotency-Key':'DR-changed-confirm'})
    assert response.status_code == 409, response.text
    assert 'PRODUCT_FILTER_CONFLICT' in response.text
    assert client.get('/api/v1/cart').json()['items'] == []


def test_released_drink_fixture_supports_types_flavor_packages_and_preserves_mutable_offer(pi_client):
    client, requests = pi_client
    from app.services.seed_service import seed_catalog
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    from sqlalchemy import select
    with Session(requests.engine) as db:
        seed_catalog(db)
        p = db.get(CatalogProduct, 'demo:cn-coke-original-330ml-can')
        p.product_type = None
        metadata = json.loads(p.metadata_json)
        metadata.pop('type_label', None); metadata.pop('flavor', None)
        p.metadata_json = json.dumps(metadata)
        offer = db.scalar(select(Offer).where(Offer.sku_id == p.sku_id))
        offer.available_qty, offer.price_fen, offer.offer_version = 2, 375, 9
        db.commit()
        seed_catalog(db)
        db.commit()
    before = client.get(BASE).json()
    switched = client.post(BASE+'/supply-context', json={'request_id':'DR-fixture-store', 'store_id':'store-demo-01', 'delivery_zone_id':'zone-default', 'expected_session_version':before['session_version']})
    assert switched.status_code == 200, switched.text
    command(client, 'new_goal', goal='饮品', conditions={'budget_fen':5000})
    requests.answer_hook = drink_hook
    question = turn(client, '喝点东西', 'DR-fixture-first')[-1]['payload']['active_question']
    assert question['kind'] == 'category'
    assert {'可乐','饮用水','茶饮','果汁饮料','苏打水','果汁'} == {o['label'] for o in question['options']}
    cola = next(o for o in question['options'] if o['value'] == 'cola')
    response = answer_question(client, question, [cola['option_id']], 'DR-fixture-cola')
    assert response.status_code == 200, response.text
    products = response.json()['active_question']
    assert {'原味','柠檬味'} == {o['value'] for o in products['filter_options'] if o['attribute'] == 'flavor'}
    original = next(o['product'] for o in products['options'] if o['value'] == 'demo:cn-coke-original-330ml-can')
    assert (original['available_qty'],original['price_fen'],original['offer_version']) == (2,375,9)
    lemon = next(o['product'] for o in products['options'] if o['value'] == 'DR:cola-lemon-330ml-can')
    assert lemon['price_fen'] == 450 and lemon['available_qty'] == 8
    assert lemon['metadata']['attribute_evidence'] == {}
    assert client.get('/api/v1/cart').json()['items'] == []


def test_direct_drinks_filters_clear_text_revision_and_stock_changes_preserve_identity(pi_client):
    client, requests = pi_client
    seed_drinks(requests)
    command(client, 'new_goal', goal='茶饮', conditions={'product_type':'tea','budget_fen':2000,'quantity':1})
    requests.answer_hook = drink_hook
    q = turn(client, '茶饮', 'DR-direct')[-1]['payload']['active_question']
    assert q['kind'] == 'products' and len(q['options']) == 4
    spec = next(o for o in q['filter_options'] if o['attribute']=='spec' and o['value']=={'quantity':500,'unit':'ml'})
    mixed = answer_question(client, q, [spec['option_id'],q['options'][0]['option_id']], 'DR-mixed')
    assert mixed.status_code == 422
    assert client.get(BASE).json()['active_question']['question_id'] == q['question_id']
    q = answer_question(client,q,[spec['option_id']],'DR-spec').json()['active_question']
    assert len(q['options']) == 3 and all(o['product']['spec_quantity']==500 for o in q['options'])
    brand = next(o for o in q['filter_options'] if o['attribute']=='brand' and o['value']=='演示甲')
    q = answer_question(client,q,[brand['option_id']],'DR-brand').json()['active_question']
    assert [o['value'] for o in q['options']] == ['DR-tea-peach-large']
    clear = next(o for o in q['filter_options'] if o['attribute']=='brand' and o['value'] is None)
    previous=q
    q = answer_question(client,q,[clear['option_id']],'DR-clear').json()['active_question']
    assert len(q['options']) == 3
    assert answer_question(client,previous,[clear['option_id']],'DR-old-clear').status_code == 409
    def revise_hook(body):
        outputs=[json.loads(m['content']) for m in body['messages'] if m['role']=='tool']
        if not outputs:
            return {'role':'assistant','tool_calls':[{'index':0,'id':'DR-amend','type':'function','function':{'name':'guide_request','arguments':json.dumps({'kind':'amend','conditions':{'flavor':'不存在的口味'}})}}]}, 'tool_calls'
        return drink_hook(body)
    requests.answer_hook=revise_hook
    events=turn(client,'只看不存在的口味，其他条件不变','DR-revise')
    assert events[-1]['type']=='turn.completed', events
    state=client.get(BASE).json()
    assert state['conditions']['budget_fen']==2000 and state['conditions']['quantity']==1
    assert state['conditions']['spec']=={'quantity':500,'unit':'ml'}
    empty=state['active_question']
    assert empty['options']==[] and '原条件已保留' in empty['question']
    assert not any(o['value']=='不存在的口味' for o in empty['filter_options'])
    clear=next(o for o in empty['filter_options'] if o['attribute']=='flavor' and o['value'] is None)
    q=answer_question(client,empty,[clear['option_id']],'DR-clear-missing').json()['active_question']
    from app.models.store import Offer
    from sqlalchemy import select
    with Session(requests.engine) as db:
        offer=db.scalar(select(Offer).where(Offer.sku_id=='DR-tea-peach-large'))
        offer.available_qty=0;offer.offer_version+=1
        db.commit()
    assert client.get(BASE).json()['active_question'] is None
    spec_clear=next(o for o in q['filter_options'] if o['attribute']=='spec' and o['value'] is None)
    assert answer_question(client,q,[spec_clear['option_id']],'DR-stale-stock').status_code==409
    assert client.get('/api/v1/cart').json()['items']==[]


def test_unknown_drink_attributes_do_not_satisfy_hard_safety_or_low_budget(pi_client):
    client, requests=pi_client
    seed_drinks(requests)
    command(client,'new_goal',goal='饮品',conditions={'excluded_allergens':['peanut'],'budget_fen':1000,'quantity':2})
    requests.answer_hook=drink_hook
    events=turn(client,'饮品，避开花生','DR-safety')
    assert events[-1]['type']=='turn.completed', events
    state=client.get(BASE).json()
    assert state['active_question']['options']==[]
    assert '过敏原信息未知' in state['active_question']['question']
    assert not any(o['attribute'] in ('excluded_allergens','dietary_requirements') for o in state['active_question']['filter_options'])
    assert state['conditions']['excluded_allergens']==['peanut']
    command(client,'new_goal',goal='茶饮',conditions={'product_type':'tea','budget_fen':100,'quantity':2})
    events=turn(client,'茶饮预算一元','DR-budget')
    assert events[-1]['type']=='turn.completed', events
    state=client.get(BASE).json()
    assert state['active_question']['options']==[]
    assert state['conditions']['budget_fen']==100 and state['conditions']['quantity']==2
    assert client.get('/api/v1/cart').json()['items']==[]

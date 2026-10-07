"""T02 deterministic public shopping outcomes; no real retailer/provider claims."""
import json
import pytest
from sqlalchemy.orm import Session
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_next_drinks_public import drink_hook
from test_foundation_http import web


def seed_case_water(requests):
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer, Store
    with Session(requests.engine) as db:
        db.get(Store, 'pi-store').delivery_reachable = True
        db.add(CatalogProduct(sku_id='T02-case-water', name='Controlled case water',
            name_zh='合成演示箱装水', category_id='beverage', product_type='water',
            spec_quantity=6600, spec_unit='ml', metadata_json=json.dumps({
                'type_label':'饮用水', 'packaging':'bottle', 'pack_count':12,
                'item_quantity':550, 'item_unit':'ml', 'selling_unit':'case',
                'selling_unit_source':'T02 controlled synthetic specification'})))
        db.flush()
        db.add(Offer(store_id='pi-store', sku_id='T02-case-water', price_fen=2500, available_qty=2))
        db.commit()


def test_literal_chinese_case_constraints_find_verified_water_without_cart_mutation(pi_client):
    client, requests = pi_client
    seed_case_water(requests)
    conditions = {'product_type':'饮用水', 'packaging':'箱', 'quantity':2, 'budget_fen':6000}
    assert command(client, 'new_goal', goal='两箱饮用水，六十元以内', conditions=conditions).status_code == 200
    requests.answer_hook = drink_hook
    events = turn(client, '按原条件选箱装水', 'T02-literal-case')
    assert events[-1]['type'] == 'turn.completed', events
    state = client.get(BASE).json()
    assert [option['value'] for option in state['active_question']['options']] == ['T02-case-water']
    assert state['conditions'] == conditions
    assert state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def shopping_hook(tool):
    def hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            name, arguments = ('guide_request', {'kind':'continue'}) if not outputs else (tool, {'category_id':'beverage'})
            return {'role':'assistant', 'tool_calls':[{'index':0, 'id':f'T02-{len(outputs)}', 'type':'function',
                'function':{'name':name, 'arguments':json.dumps(arguments)}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed',
            'answer_kind':'comparison' if tool == 'compare_products' else 'products',
            'product_refs':[p['ref'] for p in outputs[-1]['products']]})}, 'stop'
    return hook


def test_comparison_rejects_unbuyable_candidates_at_full_requested_quantity(pi_client):
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    client, requests = pi_client
    seed_case_water(requests)
    with Session(requests.engine) as db:
        for sku, price, stock, sellable in [('T02-over-budget',3500,5,True),
                ('T02-short-stock',2000,1,True), ('T02-not-selling',2000,5,False)]:
            db.add(CatalogProduct(sku_id=sku, name=sku, category_id='beverage', product_type='water',
                metadata_json=json.dumps({'type_label':'饮用水','packaging':'bottle','pack_count':12})))
            db.flush()
            db.add(Offer(store_id='pi-store',sku_id=sku,price_fen=price,available_qty=stock,sellable=sellable))
        db.commit()
    conditions = {'product_type':'water','quantity':2,'budget_fen':6000}
    command(client, 'new_goal', goal='两件水六十元内', conditions=conditions)
    requests.answer_hook = shopping_hook('compare_products')
    events = turn(client, '比较符合条件的水', 'T02-buyable-comparison')
    assert events[-1]['type'] == 'turn.completed', events
    state = client.get(BASE).json()
    assert [card['sku_id'] for card in state['product_cards']] == ['T02-case-water']
    assert state['conditions'] == conditions and state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_retrieval_keeps_21st_buyable_candidate_after_quantity_budget_filter(pi_client, controlled_product_source):
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    client, requests = pi_client
    ranking = [f'T02-ranked-{i:02}' for i in range(21)]
    with Session(requests.engine) as db:
        for index, sku in enumerate(ranking):
            db.add(CatalogProduct(sku_id=sku,name=sku,category_id='beverage',product_type='water'))
            db.flush()
            db.add(Offer(store_id='pi-store',sku_id=sku,price_fen=200 if index == 20 else 400,available_qty=5))
            controlled_product_source['documents'][sku] = {'id':sku,'namespace':'product','title':sku,
                'text':'合成检索排序文档','source':{'file':'controlled-products','record_id':sku}}
        db.commit()
    controlled_product_source['ranking'] = ranking
    conditions = {'query':'夏日补水', 'product_type':'water', 'quantity':2, 'budget_fen':500}
    command(client,'new_goal',goal='五元内买两件补水饮品',conditions=conditions)
    requests.answer_hook = shopping_hook('search_products')
    events = turn(client,'找符合原条件的饮品','T02-ranked-recall')
    assert events[-1]['type'] == 'turn.completed', events
    assert [p['sku_id'] for p in events[-1]['payload']['product_evidence']] == ['T02-ranked-20']
    state = client.get(BASE).json()
    assert state['conditions'] == conditions and state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_catalog_recall_rechecks_current_category_review_and_offer(web, controlled_product_source):
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    from sqlalchemy import select
    client, sessions = web
    kept = 'demo:cn-nongfu-water-550ml-bottle'
    moved = 'demo:cn-cestbon-water-555ml-bottle'
    revoked = 'demo:cn-nongfu-water-550ml-12bottle'
    controlled_product_source['ranking'] = [kept, moved, revoked]
    controlled_product_source['extra_hits'] = [{'id':'unknown-index-sku'}]
    def change_current_facts():
        with sessions() as db:
            db.get(CatalogProduct, moved).category_id = 'snack'
            db.get(CatalogProduct, revoked).review_status = 'pending'
            offer = db.scalar(select(Offer).where(Offer.sku_id == kept))
            offer.price_fen, offer.available_qty, offer.offer_version = 987, 0, 7
            db.commit()
    controlled_product_source['on_search'] = change_current_facts
    response = client.get('/api/v1/products', params={'q':'饮用水', 'category_id':'beverage'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['total'] == 1
    assert [(p['sku_id'],p['price_fen'],p['available_qty'],p['offer_version']) for p in data['items']] == [(kept,987,0,7)]
    call = controlled_product_source['calls'][-1]
    assert call['deadline'] is not None
    assert 'demo:flour-all-purpose-500g' not in call['allowed_ids']
    assert call['limit'] == len(call['allowed_ids'])


@pytest.mark.parametrize('conditions, expected_sku, original_sku', [
    ({'product_type':'drinking_water','packaging':'箱','quantity':2,'budget_fen':6000},
     'demo:synthetic-case-water-12x550ml', 'demo:cn-nongfu-water-550ml-12bottle'),
    ({'product_type':'tea','dietary_requirements':['sugar_free'],'quantity':2,'budget_fen':1000},
     'demo:synthetic-sugar-free-tea-500ml', 'demo:green-tea-500ml'),
])
def test_seeded_demo_evidence_positive_and_original_negative_require_explicit_cart_confirmation(
        pi_client, conditions, expected_sku, original_sku):
    from app.models.store import Offer, Store
    from app.services.seed_service import seed_catalog
    from sqlalchemy import select
    from test_next_snack_public import answer_question
    client, requests = pi_client
    ids = ['demo:synthetic-case-water-12x550ml', 'demo:synthetic-sugar-free-tea-500ml',
           'demo:cn-nongfu-water-550ml-12bottle', 'demo:green-tea-500ml']
    with Session(requests.engine) as db:
        seed_catalog(db)
        db.get(Store, 'pi-store').delivery_reachable = True
        for offer in db.scalars(select(Offer).where(Offer.store_id == 'store-demo-01', Offer.sku_id.in_(ids))).all():
            db.add(Offer(store_id='pi-store', sku_id=offer.sku_id, price_fen=offer.price_fen,
                         available_qty=offer.available_qty, sellable=offer.sellable))
        db.commit()
    original = client.get('/api/v1/products/' + original_sku).json()
    assert original['metadata'].get('selling_unit') is None
    assert original['metadata'].get('attribute_evidence', {}).get('sugar_free') is None
    command(client, 'new_goal', goal='按明确的模拟商品属性选购', conditions=conditions)
    requests.answer_hook = drink_hook
    events = turn(client, '保留原条件查看商品', 'T02-demo-evidence')
    assert events[-1]['type'] == 'turn.completed', events
    state = client.get(BASE).json()
    question = state['active_question']
    assert [o['value'] for o in question['options']] == [expected_sku]
    assert state['conditions'] == conditions and state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    option_id = question['options'][0]['option_id']
    selected = answer_question(client, question, [option_id], 'T02-demo-select', {option_id:2})
    assert selected.status_code == 200, selected.text
    state = selected.json()
    assert state['conditions'] == conditions
    assert state['plan']['selected_total_fen'] == (5000 if conditions['product_type'] == 'drinking_water' else 800)
    assert client.get('/api/v1/cart').json()['items'] == []
    body = {'plan_id':state['plan']['plan_id'], 'plan_version':state['plan']['plan_version'],
            'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'],
            'selected_items':[{'sku_id':expected_sku,'quantity':2}]}
    confirmed = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm', json=body,
                            headers={'Idempotency-Key':'T02-demo-confirm'})
    assert confirmed.status_code == 200, confirmed.text
    assert [(row['sku_id'],row['quantity']) for row in client.get('/api/v1/cart').json()['items']] == [(expected_sku,2)]


def test_explore_preserves_canonical_category_against_tool_argument(pi_client):
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer, Store
    client, requests = pi_client
    with Session(requests.engine) as db:
        db.get(Store, 'pi-store').delivery_reachable = True
        db.add(CatalogProduct(sku_id='T02-snack', name='Controlled snack', category_id='snack',
                              product_type='crackers', metadata_json=json.dumps({'type_label':'饼干'})))
        db.flush()
        db.add(Offer(store_id='pi-store',sku_id='T02-snack',price_fen=300,available_qty=5))
        db.commit()
    conditions = {'category_id':'snack','quantity':1}
    command(client,'new_goal',goal='只选零食',conditions=conditions)
    requests.answer_hook = drink_hook  # Tool asks beverage; canonical task remains snack.
    events = turn(client,'按原品类查商品','T02-canonical-category')
    assert events[-1]['type'] == 'turn.completed', events
    state = client.get(BASE).json()
    assert [o['value'] for o in state['active_question']['options']] == ['T02-snack']
    assert state['conditions'] == conditions
    assert client.get('/api/v1/cart').json()['items'] == []


def test_confirm_rechecks_canonical_category_after_plan(pi_client):
    from app.models.catalog import CatalogProduct
    from test_next_snack_public import answer_question
    client, requests = pi_client
    seed_case_water(requests)
    command(client,'new_goal',goal='两箱饮用水',conditions={
        'category_id':'beverage','product_type':'water','packaging':'箱','quantity':2})
    requests.answer_hook = drink_hook
    events = turn(client,'展示箱装水','T02-category-before-plan')
    question = events[-1]['payload']['active_question']
    option_id = question['options'][0]['option_id']
    selected = answer_question(client,question,[option_id],'T02-category-select',{option_id:2})
    assert selected.status_code == 200, selected.text
    state = selected.json()
    with Session(requests.engine) as db:
        db.get(CatalogProduct,'T02-case-water').category_id = 'snack'
        db.commit()
    body = {'plan_id':state['plan']['plan_id'],'plan_version':state['plan']['plan_version'],
            'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
            'selected_items':[{'sku_id':'T02-case-water','quantity':2}]}
    result = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=body,
                         headers={'Idempotency-Key':'T02-category-changed'})
    assert result.status_code == 409, result.text
    assert client.get('/api/v1/cart').json()['items'] == []


def test_confirm_rechecks_pack_count_mode_after_plan(pi_client):
    from app.models.catalog import CatalogProduct
    from test_next_snack_public import answer_question
    client, requests = pi_client
    seed_case_water(requests)
    conditions = {'category_id':'beverage','product_type':'water','pack_count_mode':'multi','quantity':2}
    command(client,'new_goal',goal='两件多瓶装饮用水',conditions=conditions)
    requests.answer_hook = drink_hook
    events = turn(client,'查看多瓶装饮用水','T02-pack-before-plan')
    question = events[-1]['payload']['active_question']
    option_id = question['options'][0]['option_id']
    selected = answer_question(client,question,[option_id],'T02-pack-select',{option_id:2})
    assert selected.status_code == 200, selected.text
    state = selected.json()
    with Session(requests.engine) as db:
        product = db.get(CatalogProduct,'T02-case-water')
        metadata = json.loads(product.metadata_json)
        metadata['pack_count'] = 1
        product.metadata_json = json.dumps(metadata)
        db.commit()
    body = {'plan_id':state['plan']['plan_id'],'plan_version':state['plan']['plan_version'],
            'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
            'selected_items':[{'sku_id':'T02-case-water','quantity':2}]}
    result = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=body,
                         headers={'Idempotency-Key':'T02-pack-changed'})
    assert result.status_code == 409, result.text
    assert client.get(BASE).json()['conditions'] == conditions
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('changed_attribute', ['product_type', 'brand', 'packaging'])
def test_confirm_preserves_existing_nonbeverage_candidate_constraints(pi_client, changed_attribute):
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer, Store
    from test_next_snack_public import answer_question
    client, requests = pi_client
    with Session(requests.engine) as db:
        db.get(Store,'pi-store').delivery_reachable = True
        db.add(CatalogProduct(sku_id='T02-scoped-snack',name='Controlled crackers',category_id='snack',
            product_type='crackers',brand='演示甲',metadata_json=json.dumps({
                'type_label':'饼干','packaging':'bag','pack_count':6})))
        db.flush()
        db.add(Offer(store_id='pi-store',sku_id='T02-scoped-snack',price_fen=600,available_qty=5))
        db.commit()
    conditions = {'category_id':'snack','product_type':'crackers','brand':'演示甲',
                  'packaging':'bag','pack_count_mode':'multi','quantity':2}
    assert command(client,'new_goal',goal='按指定品牌包装买饼干',conditions=conditions).status_code == 200
    requests.answer_hook = drink_hook  # Canonical snack scope takes precedence.
    events = turn(client,'查看符合原条件的饼干','T02-snack-constraints')
    assert events[-1]['type'] == 'turn.completed', events
    question = events[-1]['payload']['active_question']
    assert [o['value'] for o in question['options']] == ['T02-scoped-snack']
    option_id = question['options'][0]['option_id']
    selected = answer_question(client,question,[option_id],'T02-snack-select',{option_id:2})
    assert selected.status_code == 200, selected.text
    state = selected.json()
    with Session(requests.engine) as db:
        product = db.get(CatalogProduct,'T02-scoped-snack')
        if changed_attribute == 'packaging':
            metadata = json.loads(product.metadata_json)
            metadata['packaging'] = 'box'
            product.metadata_json = json.dumps(metadata)
        else:
            setattr(product,changed_attribute,'chips' if changed_attribute == 'product_type' else '演示乙')
        db.commit()
    body = {'plan_id':state['plan']['plan_id'],'plan_version':state['plan']['plan_version'],
            'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
            'selected_items':[{'sku_id':'T02-scoped-snack','quantity':2}]}
    result = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=body,
                         headers={'Idempotency-Key':'T02-snack-changed'})
    assert result.status_code == 409, result.text
    assert client.get(BASE).json()['conditions'] == conditions
    assert client.get('/api/v1/cart').json()['items'] == []

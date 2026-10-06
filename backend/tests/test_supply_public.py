"""TASK07 supply decisions through the public Pi/HTTP purchase contract."""
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.models.store import Offer
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_dish_public import dish_seed, prepare_dish
from test_multidish_public import confirm_body


def test_chosen_spec_shortage_is_preview_and_never_confirmation(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id == 'egg-6').values(available_qty=0))
        db.commit()
    command(client, 'new_goal', goal='番茄炒蛋，鸡蛋选六枚装')
    state = prepare_dish(client, requests, selections={'egg':'egg-6'})
    plan = state['plan']
    assert plan['plan_kind'] == 'supply_preview'
    assert plan['can_confirm'] is False
    egg = next(row for row in plan['items'] if row['ingredient_id'] == 'egg')
    assert egg['sku_id'] == 'egg-6'
    gap = next(gap for gap in plan['gaps'] if gap['ingredient_id'] == 'egg')
    assert (gap['kind'],gap['requested_packs'],gap['available_packs'],gap['shortfall_packs']) == ('unavailable',1,0,1)
    assert gap['requirement'] == {'quantity':3,'unit':'pc'}
    assert gap['group_ids'] == [plan['groups'][0]['group_id']]
    alternative = next(option for option in gap['alternatives'] if option['items'] == [{'sku_id':'egg-10','quantity':1}])
    assert (alternative['total_price_fen'],alternative['leftover_quantity']) == (1300,7)
    url = '/api/v1/guide/tasks/' + state['task_id']
    response = client.post(url+'/confirm',json=confirm_body(state),headers={'Idempotency-Key':'preview-not-consent'})
    assert response.status_code == 409
    assert response.json()['error']['code'] == 'SUPPLY_SELECTION_REQUIRED'
    assert client.get('/api/v1/cart').json()['items'] == []


def supply_revision(client,state,key,intent,**extra):
    return client.post('/api/v1/guide/tasks/'+state['task_id']+'/plan-revisions',json={
        'request_id':key,'base_plan_id':state['plan']['plan_id'],'base_plan_version':state['plan']['plan_version'],
        'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
        'coverage_intent':intent,'items':[],**extra})


def test_partial_purchase_is_explicit_then_independently_confirmed_and_idempotent(pi_client):
    client,requests = pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=0))
        db.commit()
    command(client,'new_goal',goal='番茄炒蛋')
    preview = prepare_dish(client,requests)
    url = '/api/v1/guide/tasks/'+preview['task_id']
    legacy = supply_revision(client,preview,'legacy-default','partial_ok')
    assert legacy.status_code == 422
    chosen = supply_revision(client,preview,'explicit-partial','choose_partial')
    assert chosen.status_code == 200,chosen.text
    assert chosen.json()['plan_kind'] == 'partial_purchase'
    assert chosen.json()['gaps'] == preview['plan']['gaps']
    assert chosen.json()['can_confirm'] is True
    assert client.get('/api/v1/cart').json()['items'] == []
    assert supply_revision(client,preview,'explicit-partial','choose_partial').json() == chosen.json()
    state = client.get(BASE).json()
    assert [r['sku_id'] for r in state['plan']['items'] if r['selected']] == ['tomato-500']
    assert state['plan']['groups'] == preview['plan']['groups']
    body = confirm_body(state)
    first = client.post(url+'/confirm',json=body,headers={'Idempotency-Key':'partial-confirm'})
    assert first.status_code == 200,first.text
    assert client.post(url+'/confirm',json=body,headers={'Idempotency-Key':'partial-confirm'}).json() == first.json()
    assert client.post(url+'/confirm',json=body,headers={'Idempotency-Key':'second-partial-confirm'}).status_code == 409
    assert {r['sku_id']:r['quantity'] for r in client.get('/api/v1/cart').json()['items']} == {'tomato-500':1}


def test_missing_ingredient_and_unknown_offer_remain_distinct_supply_gaps(pi_client):
    from sqlalchemy import delete
    from app.models.catalog import CatalogProduct
    client,requests = pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(delete(Offer).where(Offer.sku_id.in_(['egg-6','egg-10','tomato-500'])))
        db.execute(delete(CatalogProduct).where(CatalogProduct.sku_id.in_(['egg-6','egg-10'])))
        db.commit()
    command(client,'new_goal',goal='番茄炒蛋')
    state = prepare_dish(client,requests)
    assert state['plan']['plan_kind'] == 'supply_preview'
    gaps = {gap['ingredient_id']:gap for gap in state['plan']['gaps']}
    assert gaps['egg']['kind'] == 'ingredient_missing'
    assert gaps['egg']['requirement'] == {'quantity':3,'unit':'pc'}
    assert gaps['egg']['sku_id'] is None
    assert gaps['egg']['requested_packs'] is None
    assert gaps['tomato']['kind'] == 'availability_unknown'
    assert gaps['tomato']['available_packs'] is None
    assert gaps['tomato']['unknown_attribute'] == 'offer'
    assert state['plan']['can_confirm'] is False
    assert client.get('/api/v1/cart').json()['items'] == []


def test_whole_demand_mixed_packs_require_explicit_alternative_choice(pi_client):
    client,requests = pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=1))
        db.commit()
    command(client,'new_goal',goal='八人份番茄炒蛋，鸡蛋六枚装')
    state = prepare_dish(client,requests,people=8,selections={'egg':'egg-6'})
    gap = next(g for g in state['plan']['gaps'] if g['ingredient_id']=='egg')
    assert (gap['kind'],gap['requested_packs'],gap['available_packs'],gap['shortfall_packs']) == ('shortage',2,1,1)
    mixed = next(option for option in gap['alternatives'] if len(option['items']) == 2)
    assert sorted(mixed['items'],key=lambda row:row['sku_id']) == [{'sku_id':'egg-10','quantity':1},{'sku_id':'egg-6','quantity':1}]
    assert (mixed['total_price_fen'],mixed['leftover_quantity']) == (2200,4)
    assert client.get('/api/v1/cart').json()['items'] == []
    chosen = supply_revision(client,state,'choose-mixed','choose_alternative',gap_id=gap['gap_id'],alternative_index=gap['alternatives'].index(mixed))
    assert chosen.status_code == 200,chosen.text
    assert chosen.json()['plan_kind'] == 'full_plan'
    assert chosen.json()['gaps'] == []
    assert chosen.json()['groups'] == state['plan']['groups']
    assert client.get('/api/v1/cart').json()['items'] == []
    current = client.get(BASE).json()
    result = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=confirm_body(current),headers={'Idempotency-Key':'mixed-confirm'})
    assert result.status_code == 200,result.text
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']} == {'tomato-500':3,'egg-6':1,'egg-10':1}


def test_alternative_selection_retains_spec_after_people_revision(pi_client):
    from test_dish_public import revise_dish
    client,requests = pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='egg-6').values(available_qty=0))
        db.commit()
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests)
    gap=next(g for g in state['plan']['gaps'] if g['ingredient_id']=='egg')
    chosen=supply_revision(client,state,'choose-ten','choose_alternative',gap_id=gap['gap_id'],alternative_index=0)
    assert chosen.status_code==200,chosen.text
    current=client.get(BASE).json()
    changed=revise_dish(client,current,'five-after-alternative',people=5)
    assert changed.status_code==200,changed.text
    egg=next(row for row in changed.json()['items'] if row['ingredient_id']=='egg')
    assert egg['sku_id']=='egg-10'
    assert (egg['quantity'],egg['coverage_quantity'],egg['leftover_quantity'])==(1,8,2)
    assert changed.json()['plan_kind']=='full_plan'
    assert client.get('/api/v1/cart').json()['items']==[]


def test_mixed_alternative_specs_survive_people_change_without_silent_replacement(pi_client):
    from test_dish_public import revise_dish
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=1))
        db.commit()
    command(client,'new_goal',goal='八人份番茄炒蛋')
    state=prepare_dish(client,requests,people=8)
    gap=next(g for g in state['plan']['gaps'] if g['ingredient_id']=='egg')
    index=next(i for i,option in enumerate(gap['alternatives']) if len(option['items'])==2)
    chosen=supply_revision(client,state,'retain-mixed','choose_alternative',gap_id=gap['gap_id'],alternative_index=index)
    assert chosen.status_code==200,chosen.text
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=5))
        db.commit()
    current=client.get(BASE).json()
    changed=revise_dish(client,current,'mixed-people-ten',people=10)
    assert changed.status_code==200,changed.text
    eggs=[row for row in changed.json()['items'] if row['ingredient_id']=='egg']
    assert {row['sku_id'] for row in eggs}=={'egg-6','egg-10'}
    assert sum(row['requirement']['quantity'] for row in eggs)==15
    assert sum(c['requirement']['quantity'] for row in eggs for c in row['contributions'])==15
    assert client.get('/api/v1/cart').json()['items']==[]

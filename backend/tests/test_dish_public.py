"""TASK05 public single-dish facts through actual Pi and isolated HTTP state."""
import json
from sqlalchemy import update
from sqlalchemy.orm import Session
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn


def dish_seed(requests):
    from app.models.catalog import CatalogProduct
    from app.models.store import Store, Offer
    with Session(requests.engine) as db:
        db.execute(update(Store).values(delivery_reachable=True))
        for sku, ingredient, quantity, unit, price in [
            ('tomato-500', 'tomato', 500, 'g', 600),
            ('egg-6', 'egg', 6, 'pc', 900), ('egg-10', 'egg', 10, 'pc', 1300),
            ('oil-500', 'oil', 500, 'ml', 1000), ('salt-500', 'salt', 500, 'g', 300),
            ('sugar-500', 'sugar', 500, 'g', 500),
        ]:
            db.add(CatalogProduct(sku_id=sku, name=sku, category_id='food', ingredient_ids=json.dumps([ingredient]), spec_quantity=quantity, spec_unit=unit))
            db.flush()
            db.add(Offer(store_id='pi-store', sku_id=sku, price_fen=price, available_qty=30))
        db.commit()


def dish_hook(people=None, selections=None):
    def hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        def call(name, args):
            return {'role':'assistant', 'tool_calls':[{'index':0, 'id':f'dish-{len(outputs)}', 'type':'function', 'function':{'name':name, 'arguments':json.dumps(args)}}]}, 'tool_calls'
        if not outputs:
            return call('guide_request', {'kind':'continue'})
        if len(outputs) == 1:
            return call('search_dishes', {'query':'番茄炒蛋'})
        if len(outputs) == 2:
            args = {'dish_ref':outputs[-1]['dishes'][0]['ref']}
            if people is not None:
                args['people'] = people
            if selections:
                args['selections'] = selections
            return call('propose_dish', args)
        return {'role':'assistant', 'content':json.dumps({'status':'completed', 'answer_kind':'purchase_plan', 'proposal_ref':outputs[-1]['proposal_ref']})}, 'stop'
    return hook


def prepare_dish(client, requests, people=None, selections=None, request_id='dish'):
    requests.answer_hook = dish_hook(people, selections)
    events = turn(client, '番茄炒蛋，先给采购清单', request_id)
    assert events[-1]['type'] == 'turn.completed', events
    state = client.get(BASE).json()
    assert state['plan'] is not None, events
    return state


def test_single_dish_baseline_is_not_explicit_people_and_pantry_amount_is_unknown(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client, 'new_goal', goal='番茄炒蛋')
    state = prepare_dish(client, requests)
    plan = state['plan']
    assert plan['dish']['people'] == 2
    assert plan['dish']['people_source'] == 'default'
    by_ingredient = {row['ingredient_id']:row for row in plan['items']}
    assert by_ingredient['tomato']['requirement']['quantity'] == 300
    assert by_ingredient['egg']['requirement']['quantity'] == 3
    assert by_ingredient['tomato']['quantity'] == 1
    assert by_ingredient['egg']['quantity'] == 1
    for ingredient in ('oil', 'salt', 'sugar'):
        row = by_ingredient[ingredient]
        assert row['selected'] is False
        assert row['role'] == 'pantry'
        assert row['requirement']['quantity'] is None
    assert plan['selected_total_fen'] == 1500
    assert client.get('/api/v1/cart').json()['items'] == []


def revise_dish(client, state, request_id, **changes):
    return client.post('/api/v1/guide/tasks/' + state['task_id'] + '/plan-revisions', json={
        'request_id':request_id, 'base_plan_id':state['plan']['plan_id'], 'base_plan_version':state['plan']['plan_version'],
        'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'],
        'coverage_intent':'dish_update', 'items':[], **changes})


def test_people_revision_retains_selected_egg_spec_and_requires_new_confirmation(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client, 'new_goal', goal='三人份番茄炒蛋，鸡蛋选十枚装')
    state = prepare_dish(client, requests, people=3, selections={'egg':'egg-10'})
    plan = state['plan']
    egg = next(row for row in plan['items'] if row['ingredient_id'] == 'egg')
    assert plan['dish']['people_source'] == 'explicit'
    assert egg['requirement']['quantity'] == 4.5
    assert egg['coverage_quantity'] == 5
    assert egg['quantity'] == 1
    assert egg['leftover_quantity'] == 5
    old_body = {'plan_id':plan['plan_id'], 'plan_version':plan['plan_version'], 'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'], 'selected_items':[{'sku_id':row['sku_id'],'quantity':row['remaining_quantity']} for row in plan['items'] if row['selected']]}
    revised = revise_dish(client, state, 'five-people', people=5)
    assert revised.status_code == 200, revised.text
    plan = revised.json()
    egg = next(row for row in plan['items'] if row['ingredient_id'] == 'egg')
    tomato = next(row for row in plan['items'] if row['ingredient_id'] == 'tomato')
    assert egg['sku_id'] == 'egg-10'
    assert egg['requirement']['quantity'] == 7.5
    assert egg['coverage_quantity'] == 8
    assert egg['quantity'] == 1
    assert egg['leftover_quantity'] == 2
    assert tomato['quantity'] == 2
    assert tomato['requirement']['quantity'] == 750
    assert tomato['leftover_quantity'] == 250
    assert client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=old_body,headers={'Idempotency-Key':'old-dish'}).status_code == 409
    assert client.get('/api/v1/cart').json()['items'] == []


def test_pantry_selection_and_added_ledger_survive_people_revision_without_rebuying(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client, 'new_goal', goal='番茄炒蛋')
    state = prepare_dish(client, requests)
    plan = state['plan']
    url = '/api/v1/guide/tasks/'+state['task_id']
    selected = client.post(url+'/plan-revisions',json={'request_id':'choose-salt','base_plan_id':plan['plan_id'],'base_plan_version':plan['plan_version'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],'coverage_intent':'selection_only','items':[{'sku_id':row['sku_id'],'quantity':row['quantity'],'selected':row['selected'] or row['ingredient_id']=='salt'} for row in plan['items']]})
    assert selected.status_code == 200, selected.text
    state = client.get(BASE).json()
    plan = state['plan']
    salt = next(row for row in plan['items'] if row['ingredient_id']=='salt')
    assert salt['requirement']['quantity'] is None
    body={'plan_id':plan['plan_id'],'plan_version':plan['plan_version'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],'selected_items':[{'sku_id':'tomato-500','quantity':1}]}
    added=client.post(url+'/items/tomato-500/add',json=body,headers={'Idempotency-Key':'tomato-row'})
    assert added.status_code==200, added.text
    state=client.get(BASE).json()
    revised=revise_dish(client,state,'increase-after-add',people=5)
    assert revised.status_code==200,revised.text
    plan=revised.json()
    tomato=next(row for row in plan['items'] if row['ingredient_id']=='tomato')
    salt=next(row for row in plan['items'] if row['ingredient_id']=='salt')
    assert (tomato['quantity'],tomato['added_quantity'],tomato['remaining_quantity'])==(2,1,1)
    assert salt['selected'] is True
    assert salt['requirement']['quantity'] is None
    state=client.get(BASE).json()
    body={'plan_id':plan['plan_id'],'plan_version':plan['plan_version'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],'selected_items':[{'sku_id':row['sku_id'],'quantity':row['remaining_quantity']} for row in plan['items'] if row['selected'] and row['remaining_quantity']]}
    confirmed=client.post(url+'/confirm',json=body,headers={'Idempotency-Key':'dish-confirm'})
    assert confirmed.status_code==200,confirmed.text
    cart={row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']}
    assert cart=={'tomato-500':2,'egg-6':2,'salt-500':1}
    state=client.get(BASE).json()
    reduced=revise_dish(client,state,'reduce-after-purchase',people=1)
    assert reduced.status_code==200,reduced.text
    tomato=next(row for row in reduced.json()['items'] if row['ingredient_id']=='tomato')
    assert tomato['remaining_quantity']==0
    assert tomato['leftover_quantity']==850
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']}==cart


def test_unselected_pantry_exclusion_does_not_block_recipe_but_selecting_it_does(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋，不买盐',conditions={'exclusions':['salt']})
    state=prepare_dish(client,requests)
    assert next(row for row in state['plan']['items'] if row['ingredient_id']=='salt')['selected'] is False
    plan=state['plan']
    response=client.post('/api/v1/guide/tasks/'+state['task_id']+'/plan-revisions',json={'request_id':'excluded-salt','base_plan_id':plan['plan_id'],'base_plan_version':plan['plan_version'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],'coverage_intent':'selection_only','items':[{'sku_id':row['sku_id'],'quantity':row['quantity'],'selected':True} for row in plan['items']]})
    assert response.status_code==409,response.text
    assert response.json()['error']['code']=='EXCLUSION_CONFLICT'
    assert client.get('/api/v1/cart').json()['items']==[]


def test_budget_acceptance_and_chat_people_change_preserve_spec_without_cart_write(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋',conditions={'budget_fen':1900})
    state=prepare_dish(client,requests,people=3,selections={'egg':'egg-10'})
    response=revise_dish(client,state,'over-budget',people=5)
    assert response.status_code==200,response.text
    assert response.json()['budget_quote']=={'budget_fen':1900,'total_fen':2500}
    assert response.json()['can_confirm'] is False
    assert client.get(BASE).json()['conditions']['budget_fen']==1900
    assert client.get('/api/v1/cart').json()['items']==[]
    command(client,'amend',conditions={'budget_fen':2500})
    state=prepare_dish(client,requests,people=5,request_id='accept-price-recompute')
    egg=next(row for row in state['plan']['items'] if row['ingredient_id']=='egg')
    assert egg['sku_id']=='egg-10'
    assert state['plan']['selected_total_fen']==2500
    assert client.get('/api/v1/cart').json()['items']==[]


def test_incompatible_selected_spec_is_not_converted_and_quantity_revision_keeps_recipe_facts(pi_client):
    client, requests=pi_client
    dish_seed(requests)
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    with Session(requests.engine) as db:
        db.add(CatalogProduct(sku_id='egg-grams',name='鸡蛋克装',category_id='food',ingredient_ids='["egg"]',spec_quantity=500,spec_unit='g'))
        db.flush();db.add(Offer(store_id='pi-store',sku_id='egg-grams',price_fen=1000,available_qty=10));db.commit()
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests)
    incompatible=revise_dish(client,state,'bad-unit',selections={'egg':'egg-grams'})
    assert incompatible.status_code==409,incompatible.text
    assert incompatible.json()['error']['code']=='DISH_UNIT_UNKNOWN'
    plan=state['plan']
    revised=client.post('/api/v1/guide/tasks/'+state['task_id']+'/plan-revisions',json={'request_id':'extra-tomato','base_plan_id':plan['plan_id'],'base_plan_version':plan['plan_version'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],'coverage_intent':'selection_only','items':[{'sku_id':row['sku_id'],'quantity':2 if row['ingredient_id']=='tomato' else row['quantity'],'selected':row['selected']} for row in plan['items']]})
    assert revised.status_code==200,revised.text
    tomato=next(row for row in revised.json()['items'] if row['ingredient_id']=='tomato')
    assert tomato['quantity']==2
    assert tomato['requirement']['quantity']==300
    assert tomato['leftover_quantity']==700
    assert client.get('/api/v1/cart').json()['items']==[]


def test_dish_plan_exposes_compatible_specs_for_explicit_user_selection(pi_client):
    client, requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests)
    egg=next(row for row in state['plan']['items'] if row['ingredient_id']=='egg')
    assert {option['sku_id'] for option in egg['available_specs']}=={'egg-6','egg-10'}
    assert {option['spec_quantity'] for option in egg['available_specs']}=={6,10}
    revised=revise_dish(client,state,'choose-ten',selections={'egg':'egg-10'})
    assert revised.status_code==200,revised.text
    assert next(row for row in revised.json()['items'] if row['ingredient_id']=='egg')['sku_id']=='egg-10'


def test_single_dish_json_facts_survive_repeat_upgrade_and_hold(pi_client,monkeypatch):
    from app.core.database import init_db
    from app.core.config import get_settings
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests,people=3,selections={'egg':'egg-10'})
    init_db(requests.engine);init_db(requests.engine)
    assert client.get(BASE).json()['plan']==state['plan']
    monkeypatch.setenv('SHOPPING_WRITES_PAUSED','true');get_settings.cache_clear()
    plan=state['plan']
    body={'plan_id':plan['plan_id'],'plan_version':plan['plan_version'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],'selected_items':[{'sku_id':row['sku_id'],'quantity':row['remaining_quantity']} for row in plan['items'] if row['selected']]}
    response=client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=body,headers={'Idempotency-Key':'held-dish'})
    assert response.status_code==503,response.text
    assert client.get('/api/v1/cart').json()['items']==[]


def test_unselected_pantry_supply_changes_do_not_block_selected_confirmation(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests)
    from app.models.store import Offer
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='salt-500').values(sellable=False,available_qty=0,offer_version=2))
        db.commit()
    plan=state['plan']
    body={'plan_id':plan['plan_id'],'plan_version':plan['plan_version'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],'selected_items':[{'sku_id':row['sku_id'],'quantity':row['remaining_quantity']} for row in plan['items'] if row['selected']]}
    result=client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=body,headers={'Idempotency-Key':'without-salt'})
    assert result.status_code==200,result.text
    assert {row['sku_id'] for row in client.get('/api/v1/cart').json()['items']}=={'tomato-500','egg-6'}
    state=prepare_dish(client,requests,request_id='unavailable-pantry-recompute')
    salt=next(row for row in state['plan']['items'] if row['ingredient_id']=='salt')
    assert salt['selected'] is False
    assert salt['sellable'] is False
    assert salt['available_qty']==0

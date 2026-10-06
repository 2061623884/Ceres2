"""TASK06 public group demand; model fixture drives the actual Pi SDK tools."""
import json
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_dish_public import dish_seed, prepare_dish


def append_hook(query='番茄炒蛋', people=None, selections=None):
    def hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        def call(name, args):
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'multi-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
        if not outputs:
            return call('guide_request', {'kind':'continue'})
        if len(outputs) == 1:
            return call('search_dishes', {'query':query})
        if len(outputs) == 2:
            if not outputs[-1]['dishes']:
                return {'role':'assistant','content':json.dumps({'status':'waiting','clarification_slot':'target'})}, 'stop'
            return call('propose_dish', {'dish_ref':outputs[-1]['dishes'][0]['ref'], 'operation':'append', **({'people':people} if people else {}), **({'selections':selections} if selections else {})})
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'purchase_plan','proposal_ref':outputs[-1]['proposal_ref']})}, 'stop'
    return hook


def append_dish(client, requests, **kwargs):
    requests.answer_hook = append_hook(**kwargs)
    events = turn(client, '再追加一道' + kwargs.get('query','番茄炒蛋'), 'append-dish')
    assert events[-1]['type'] == 'turn.completed', events
    return client.get(BASE).json()


def test_explicit_append_keeps_groups_and_merges_before_package_rounding(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    original = prepare_dish(client, requests)
    state = append_dish(client, requests)
    groups = state['plan'].get('groups', [])
    assert len(groups) == 2, state['plan']
    assert groups[0]['group_id'] != groups[1]['group_id']
    assert groups[0]['group_id'] == original['plan']['groups'][0]['group_id']
    eggs = next(row for row in state['plan']['items'] if row['ingredient_id'] == 'egg')
    tomato = next(row for row in state['plan']['items'] if row['ingredient_id'] == 'tomato')
    assert (eggs['requirement']['quantity'], eggs['quantity']) == (6, 1)
    assert (tomato['requirement']['quantity'], tomato['quantity']) == (600, 2)
    assert [c['requirement']['quantity'] for c in eggs['contributions']] == [3, 3]
    assert {c['group_id'] for c in eggs['contributions']} == {g['group_id'] for g in groups}
    assert state['plan']['selected_total_fen'] == 2100
    assert client.get('/api/v1/cart').json()['items'] == []


def group_revision(client, state, request_id, intent, group_id, **changes):
    return client.post('/api/v1/guide/tasks/' + state['task_id'] + '/plan-revisions', json={
        'request_id':request_id, 'base_plan_id':state['plan']['plan_id'], 'base_plan_version':state['plan']['plan_version'],
        'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'],
        'coverage_intent':intent, 'group_id':group_id, 'items':[], **changes})


def confirm_body(state, items=None):
    plan = state['plan']
    return {'plan_id':plan['plan_id'],'plan_version':plan['plan_version'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
            'selected_items':items if items is not None else [{'sku_id':row['sku_id'],'quantity':row['remaining_quantity']} for row in plan['items'] if row['selected'] and row['remaining_quantity']]}


def test_group_people_and_remove_preserve_other_target_and_bought_shared_row(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    prepare_dish(client, requests)
    state = append_dish(client, requests)
    first, second = state['plan']['groups']
    url = '/api/v1/guide/tasks/' + state['task_id']
    response = client.post(url + '/items/egg-6/add', json=confirm_body(state,[{'sku_id':'egg-6','quantity':1}]),headers={'Idempotency-Key':'shared-eggs'})
    assert response.status_code == 200, response.text
    state = client.get(BASE).json()
    old_confirmation = confirm_body(state)
    response = group_revision(client,state,'six-people','group_update',first['group_id'],people=6)
    assert response.status_code == 200, response.text
    state = client.get(BASE).json()
    assert state['plan']['groups'][1] == second
    egg = next(row for row in state['plan']['items'] if row['ingredient_id'] == 'egg')
    assert (egg['requirement']['quantity'],egg['quantity'],egg['added_quantity'],egg['remaining_quantity']) == (12,2,1,1)
    assert client.post(url+'/confirm',json=old_confirmation,headers={'Idempotency-Key':'stale-before-group-update'}).status_code == 409
    response = group_revision(client,state,'remove-first','group_remove',first['group_id'])
    assert response.status_code == 200, response.text
    state = client.get(BASE).json()
    assert state['plan']['groups'] == [second]
    egg = next(row for row in state['plan']['items'] if row['ingredient_id'] == 'egg')
    assert (egg['quantity'],egg['added_quantity'],egg['remaining_quantity']) == (1,1,0)
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']} == {'egg-6':1}
    response = client.post(url+'/confirm',json=confirm_body(state),headers={'Idempotency-Key':'remaining-tomato'})
    assert response.status_code == 200, response.text
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']} == {'egg-6':1,'tomato-500':1}


def test_group_purchase_evidence_survives_removal_and_replay_without_double_count(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    prepare_dish(client,requests)
    state = append_dish(client,requests)
    original_groups = state['plan']['groups']
    url = '/api/v1/guide/tasks/' + state['task_id']
    body = confirm_body(state,[{'sku_id':'egg-6','quantity':1}])
    first = client.post(url+'/items/egg-6/add',json=body,headers={'Idempotency-Key':'group-ledger-eggs'})
    assert first.status_code == 200,first.text
    state = client.get(BASE).json()
    ledger = state['plan'].get('purchase_ledger',[])
    assert len(ledger) == 1, state['plan']
    assert ledger[0]['sku_id'] == 'egg-6'
    assert ledger[0]['added_quantity'] == 1
    assert ledger[0]['operation_id'] == first.json()['operation_id']
    assert ledger[0]['groups'] == original_groups
    assert [c['requirement']['quantity'] for c in ledger[0]['contributions']] == [3,3]
    replay = client.post(url+'/items/egg-6/add',json=body,headers={'Idempotency-Key':'group-ledger-eggs'})
    assert replay.json() == first.json()
    removed = group_revision(client,state,'remove-bought-source','group_remove',original_groups[0]['group_id'])
    assert removed.status_code == 200,removed.text
    state = client.get(BASE).json()
    assert state['plan']['purchase_ledger'] == ledger
    assert state['plan']['groups'] == [original_groups[1]]
    from app.core.database import init_db
    init_db(requests.engine);init_db(requests.engine)
    assert client.get(BASE).json()['plan']['purchase_ledger'] == ledger
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']} == {'egg-6':1}


def rice_seed(requests):
    from sqlalchemy.orm import Session
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    with Session(requests.engine) as db:
        for sku, ingredient, quantity, price in [('rice-500','rice',500,500),('scallion-200','scallion',200,300)]:
            db.add(CatalogProduct(sku_id=sku,name=sku,category_id='food',ingredient_ids=json.dumps([ingredient]),spec_quantity=quantity,spec_unit='g'))
            db.flush()
            db.add(Offer(store_id='pi-store',sku_id=sku,price_fen=price,available_qty=30))
        db.commit()


def test_selected_second_recipe_shares_five_eggs_and_retains_unknown_pantry_sources(pi_client):
    client,requests = pi_client
    dish_seed(requests);rice_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    original = prepare_dish(client,requests)
    state = append_dish(client,requests,query='蛋炒饭')
    assert [g['dish_id'] for g in state['plan']['groups']] == ['dish-fanqie-chao-dan','dish-dan-chao-fan']
    assert state['plan']['groups'][0] == original['plan']['groups'][0]
    egg = next(row for row in state['plan']['items'] if row['ingredient_id']=='egg')
    assert (egg['requirement']['quantity'],egg['coverage_quantity'],egg['quantity'],egg['leftover_quantity']) == (5,5,1,1)
    assert [c['requirement']['quantity'] for c in egg['contributions']] == [3,2]
    oil = next(row for row in state['plan']['items'] if row['ingredient_id']=='oil')
    assert oil['selected'] is False
    assert oil['requirement']['quantity'] is None
    assert len(oil['contributions']) == 2
    assert all(c['requirement']['quantity'] is None for c in oil['contributions'])
    assert state['plan']['selected_total_fen'] == 2000
    assert client.get('/api/v1/cart').json()['items'] == []


def test_generic_conditions_cannot_rewrite_host_owned_group_selection(pi_client):
    client,requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    state = prepare_dish(client,requests)
    for key in ('dish_groups','dish_selection'):
        response = command(client,'amend',conditions={key:[]})
        assert response.status_code == 422, response.text
        assert response.json()['error']['code'] == 'RESERVED_TASK_CONDITION'
        restored = client.get(BASE).json()
        assert restored['plan'] == state['plan']
        assert restored['state_version'] == state['state_version']
    assert client.get('/api/v1/cart').json()['items'] == []

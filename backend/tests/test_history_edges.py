"""TASK11 isolated owner, memory, reminder and recovery journeys."""
import json
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_dish_public import dish_seed, prepare_dish, revise_dish
from test_history_public import repurchase, history_hook
from test_multidish_public import confirm_body
from test_guide_semantics import turn


def make_history(client, requests):
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    old = prepare_dish(client,requests)
    command(client,'new_goal',goal='今晚番茄炒蛋')
    return old


def test_cart_coverage_suppresses_reminder_and_other_owner_cannot_access_source(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    old=prepare_dish(client,requests)
    # Shelf additions do not change the historical plan ledger.
    for sku in ('tomato-500','egg-6'):
        cart=client.get('/api/v1/cart').json()
        added=client.post('/api/v1/cart/items',json={'sku_id':sku,'quantity':1,'expected_cart_version':cart['version']})
        assert added.status_code == 200,added.text
    new=command(client,'new_goal',goal='今晚番茄炒蛋').json()
    assert new['history_reminder'] is None
    client.cookies.set('sg_owner_id','pi-owner-b')
    other='/api/v1/guide/sessions/pi-session-b'
    assert client.get(BASE+'/history').status_code==403
    assert client.get(other+'/history').json()['sources']==[]
    state=client.get(other).json()
    forbidden=client.post(other+'/history/repurchase',json={'request_id':'cross-owner','source_task_id':old['task_id'],'expected_task_id':None,'expected_state_version':0,'expected_session_version':state['session_version']})
    assert forbidden.status_code==403
    assert client.get(other).json()['task_id'] is None


def test_prior_ledger_and_approval_never_transfer_and_same_request_replays_after_upgrade(pi_client):
    from app.core.database import init_db
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    old=prepare_dish(client,requests)
    receipt=client.post('/api/v1/guide/tasks/'+old['task_id']+'/confirm',json=confirm_body(old),headers={'Idempotency-Key':'old-approval'})
    assert receipt.status_code==200,receipt.text
    source_plan=client.get(BASE).json()['plan']
    new=command(client,'new_goal',goal='再做番茄炒蛋').json()
    assert new['history_reminder'] is None
    body={'request_id':'once','source_task_id':old['task_id'],'expected_task_id':new['task_id'],'expected_state_version':new['state_version'],'expected_session_version':new['session_version']}
    response=client.post(BASE+'/history/repurchase',json=body)
    assert response.status_code==200,response.text
    plan=response.json()['plan']
    assert plan['purchase_ledger']==[]
    assert all(row['added_quantity']==0 for row in plan['items'])
    assert 'confirmation_result' not in plan
    init_db(requests.engine);init_db(requests.engine)
    assert client.post(BASE+'/history/repurchase',json=body).json()==response.json()
    assert client.post(BASE+'/history/repurchase',json={**body,'source_task_id':'different'}).status_code==409
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']}=={'tomato-500':1,'egg-6':1}
    assert next(row for row in client.get(BASE+'/history').json()['sources'] if row['task_id']==old['task_id'])['plan']==source_plan
    current=client.get(BASE).json()
    assert client.post('/api/v1/guide/tasks/'+current['task_id']+'/confirm',json=confirm_body(old),headers={'Idempotency-Key':'old-must-not-work'}).status_code==409


def test_current_explicit_constraints_override_prose_memory_and_exclusions_block_repurchase(pi_client):
    from test_memory_public import memory_turn
    client,requests=pi_client
    old=make_history(client,requests)
    memory_turn(client,requests,'请记住番茄炒蛋不买鸡蛋',{'action':'save','category':'user','domain':'shopping','key':'exclusions','content':'番茄炒蛋不买鸡蛋','source_quote':'请记住番茄炒蛋不买鸡蛋'},'remember-exclusion')
    requests.answer_hook=history_hook(old['task_id'],{'exclusions':['egg']})
    before=client.get(BASE).json()
    blocked=turn(client,'重新采购历史方案 '+old['task_id'],'excluded-history')
    assert blocked[-1]['type']=='error',blocked
    assert blocked[-1]['payload']['code']=='EXCLUSION_CONFLICT'
    assert client.get(BASE).json()['task_id']==before['task_id']
    assert client.get('/api/v1/cart').json()['items']==[]
    command(client,'amend',conditions={'exclusions':[],'people':3,'budget_fen':3000})
    requests.answer_hook=history_hook(old['task_id'])
    selected=turn(client,'重新采购历史方案 '+old['task_id'],'override-memory')
    assert selected[-1]['type']=='turn.completed',selected
    current=client.get(BASE).json()
    assert current['conditions']['exclusions']==[]
    assert current['plan']['dish']['people']==3
    assert client.get('/api/v1/cart').json()['items']==[]


def test_history_provenance_survives_people_revision(pi_client):
    client,requests=pi_client
    old=make_history(client,requests)
    assert repurchase(client,old['task_id']).status_code==200
    current=client.get(BASE).json()
    revised=revise_dish(client,current,'revise-history-people',people=5)
    assert revised.status_code==200,revised.text
    assert revised.json()['history_source']==current['plan']['history_source']
    assert revised.json()['history_changes']
    assert client.get('/api/v1/cart').json()['items']==[]


def test_cart_check_does_not_double_count_old_partial_ledger_as_remaining_coverage(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='六人份番茄炒蛋')
    old=prepare_dish(client,requests,people=6)
    # Tomato needs two packs. Buying one leaves one, not a fully covered task.
    result=client.post('/api/v1/guide/tasks/'+old['task_id']+'/items/tomato-500/add',json=confirm_body(old,[{'sku_id':'tomato-500','quantity':1}]),headers={'Idempotency-Key':'buy-one-tomato'})
    assert result.status_code==200,result.text
    state=client.get(BASE).json()
    eggs=next(row for row in state['plan']['items'] if row['sku_id']=='egg-6')
    result=client.post('/api/v1/guide/tasks/'+old['task_id']+'/items/egg-6/add',json=confirm_body(state,[{'sku_id':'egg-6','quantity':eggs['remaining_quantity']}]),headers={'Idempotency-Key':'all-eggs'})
    assert result.status_code==200,result.text
    fresh=command(client,'new_goal',goal='明天六人份番茄炒蛋').json()
    assert fresh['history_reminder']['source_task_id']==old['task_id']


def test_ambiguous_model_selection_cannot_silently_restore_a_source(pi_client):
    client,requests=pi_client
    old=make_history(client,requests)
    before=client.get(BASE).json()
    requests.answer_hook=history_hook(old['task_id'])
    result=turn(client,'还是按上次的','ambiguous-restore')
    assert result[-1]['type']=='error',result
    assert result[-1]['payload']['code']=='HISTORY_SELECTION_REQUIRED'
    after=client.get(BASE).json()
    assert after['task_id']==before['task_id'] and after['plan'] is None
    assert after['history_reminder'] is None
    assert client.get('/api/v1/cart').json()['items']==[]


def test_unresolved_missing_ingredient_remains_incomplete_when_known_rows_are_in_cart(pi_client):
    from sqlalchemy import delete
    from sqlalchemy.orm import Session
    from app.models.store import Offer
    from app.models.catalog import CatalogProduct
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(delete(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])))
        db.execute(delete(CatalogProduct).where(CatalogProduct.sku_id.in_(['egg-6','egg-10'])))
        db.commit()
    command(client,'new_goal',goal='番茄炒蛋')
    old=prepare_dish(client,requests)
    cart=client.get('/api/v1/cart').json()
    assert client.post('/api/v1/cart/items',json={'sku_id':'tomato-500','quantity':1,'expected_cart_version':cart['version']}).status_code==200
    fresh=command(client,'new_goal',goal='今晚番茄炒蛋').json()
    assert fresh['history_reminder']['source_task_id']==old['task_id']


def test_direct_product_history_uses_current_stock_preview_before_partial_confirmation(pi_client):
    from sqlalchemy import update
    from sqlalchemy.orm import Session
    from app.models.store import Offer
    from test_purchase_public import prepare
    from test_supply_public import supply_revision
    client,requests=pi_client
    old=prepare(client,requests)
    command(client,'new_goal',goal='再买可乐')
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='pi-cola').values(price_fen=400,available_qty=1,offer_version=2))
        db.commit()
    selected=repurchase(client,old['task_id'])
    assert selected.status_code==200,selected.text
    current=client.get(BASE).json()
    assert current['plan']['plan_kind']=='supply_preview'
    assert current['plan']['items'][0]['unit_price_fen']==400
    assert current['plan']['gaps'][0]['shortfall_packs']==1
    chosen=supply_revision(client,current,'direct-history-partial','choose_partial')
    assert chosen.status_code==200,chosen.text
    assert client.get('/api/v1/cart').json()['items']==[]
    state=client.get(BASE).json()
    added=client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=confirm_body(state),headers={'Idempotency-Key':'direct-current-confirm'})
    assert added.status_code==200,added.text
    assert client.get('/api/v1/cart').json()['items'][0]['quantity']==1


def test_deleted_remembered_default_does_not_become_an_explicit_condition_on_next_repurchase(pi_client):
    from test_memory_public import memory_turn
    client,requests=pi_client
    old=make_history(client,requests)
    saved=memory_turn(client,requests,'请记住番茄炒蛋做四人份',{'action':'save','category':'user','domain':'shopping','key':'people','content':'番茄炒蛋做四人份','source_quote':'请记住番茄炒蛋做四人份'},'remember-four')['records'][0]
    requests.answer_hook=history_hook(old['task_id'],{'people':4})
    assert turn(client,'重新采购历史方案 '+old['task_id'],'first-remembered')[-1]['type']=='turn.completed'
    memory_turn(client,requests,'删除这条人数记忆',{'action':'delete','memory_id':saved['memory_id'],'expected_revision':saved['revision'],'source_quote':'删除这条人数记忆'},'forget-four')
    requests.answer_hook=history_hook(old['task_id'])
    result=turn(client,'重新采购历史方案 '+old['task_id'],'after-forgetting')
    assert result[-1]['type']=='turn.completed',result
    assert client.get(BASE).json()['plan']['dish']['people']==2
    assert client.get(BASE).json()['plan']['history_memory']==[]
    assert client.get('/api/v1/cart').json()['items']==[]


def test_confirmed_partial_history_reminds_known_unavailable_gap_but_not_removed_target(pi_client):
    from sqlalchemy import update
    from sqlalchemy.orm import Session
    from app.models.store import Offer
    from test_supply_public import supply_revision
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=0))
        db.commit()
    command(client,'new_goal',goal='番茄炒蛋')
    old=prepare_dish(client,requests)
    chosen=supply_revision(client,old,'old-partial','choose_partial')
    assert chosen.status_code==200,chosen.text
    state=client.get(BASE).json()
    confirmed=client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=confirm_body(state),headers={'Idempotency-Key':'old-tomato-only'})
    assert confirmed.status_code==200,confirmed.text
    current=command(client,'new_goal',goal='今晚番茄炒蛋').json()
    assert current['history_reminder']['source_task_id']==old['task_id']


def test_current_explicit_people_revision_survives_selecting_same_history_again(pi_client):
    client,requests=pi_client
    old=make_history(client,requests)
    assert repurchase(client,old['task_id']).status_code==200
    state=client.get(BASE).json()
    assert revise_dish(client,state,'explicit-five-current',people=5).status_code==200
    again=repurchase(client,old['task_id'],key='same-source-current-five')
    assert again.status_code==200,again.text
    assert again.json()['plan']['dish']['people']==5
    assert client.get('/api/v1/cart').json()['items']==[]


def test_current_group_people_are_preserved_by_source_target_not_flattened(pi_client):
    from test_multidish_public import append_dish, group_revision
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='两道番茄炒蛋')
    prepare_dish(client,requests)
    old=append_dish(client,requests)
    command(client,'new_goal',goal='今晚两道番茄炒蛋')
    assert repurchase(client,old['task_id']).status_code==200
    current=client.get(BASE).json()
    first,second=current['plan']['groups']
    assert group_revision(client,current,'first-five','group_update',first['group_id'],people=5).status_code==200
    current=client.get(BASE).json()
    assert group_revision(client,current,'second-three','group_update',second['group_id'],people=3).status_code==200
    again=repurchase(client,old['task_id'],key='same-source-different-people')
    assert again.status_code==200,again.text
    assert [row['people'] for row in again.json()['plan']['groups']]==[5,3]
    assert client.get('/api/v1/cart').json()['items']==[]


def test_latest_explicit_task_people_override_supersedes_prior_group_people(pi_client):
    client,requests=pi_client
    old=make_history(client,requests)
    assert repurchase(client,old['task_id']).status_code==200
    current=client.get(BASE).json()
    assert revise_dish(client,current,'current-four',people=4).status_code==200
    assert command(client,'amend',conditions={'people':6}).status_code==200
    result=repurchase(client,old['task_id'],key='latest-global-six')
    assert result.status_code==200,result.text
    assert result.json()['plan']['dish']['people']==6
    assert client.get('/api/v1/cart').json()['items']==[]


def test_abandoned_source_is_only_available_for_deliberate_selection_not_reminded(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    old=prepare_dish(client,requests)
    assert command(client,'abandon').status_code==200
    current=command(client,'new_goal',goal='今晚番茄炒蛋').json()
    assert current['history_reminder'] is None
    assert old['task_id'] in [source['task_id'] for source in client.get(BASE+'/history').json()['sources']]
    deliberate=repurchase(client,old['task_id'])
    assert deliberate.status_code==200,deliberate.text
    assert client.get('/api/v1/cart').json()['items']==[]


def test_history_people_differences_follow_source_target_after_group_removal(pi_client):
    from test_multidish_public import append_dish, group_revision
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='两道不同人数番茄炒蛋')
    prepare_dish(client,requests,people=2)
    old=append_dish(client,requests,people=4)
    command(client,'new_goal',goal='今晚番茄炒蛋')
    assert repurchase(client,old['task_id']).status_code==200
    current=client.get(BASE).json()
    first,second=current['plan']['groups']
    assert group_revision(client,current,'second-restore-four','group_update',second['group_id'],people=4).status_code==200
    current=client.get(BASE).json()
    removed=group_revision(client,current,'remove-first-history','group_remove',first['group_id'])
    assert removed.status_code==200,removed.text
    assert not any('人数' in change for change in removed.json()['history_changes'])
    assert any('移除' in change for change in removed.json()['history_changes'])
    assert client.get('/api/v1/cart').json()['items']==[]


def test_history_preserves_selected_mixed_specs_but_recomputes_current_people_and_supply(pi_client):
    from sqlalchemy import update
    from sqlalchemy.orm import Session
    from app.models.store import Offer
    from test_supply_public import supply_revision
    client,requests=pi_client
    dish_seed(requests)
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=1))
        db.commit()
    command(client,'new_goal',goal='八人份番茄炒蛋，保留两种鸡蛋规格')
    old=prepare_dish(client,requests,people=8)
    gap=next(gap for gap in old['plan']['gaps'] if gap['ingredient_id']=='egg')
    index=next(i for i,option in enumerate(gap['alternatives']) if len(option['items'])==2)
    chosen=supply_revision(client,old,'historical-mixed','choose_alternative',gap_id=gap['gap_id'],alternative_index=index)
    assert chosen.status_code==200,chosen.text
    source_plan=client.get(BASE).json()['plan']
    command(client,'new_goal',goal='这次十人份番茄炒蛋',conditions={'people':10})
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id=='egg-10').values(available_qty=2,price_fen=1400,offer_version=2))
        db.commit()
    result=repurchase(client,old['task_id'])
    assert result.status_code==200,result.text
    plan=result.json()['plan']
    eggs=[row for row in plan['items'] if row['ingredient_id']=='egg']
    assert {row['sku_id']:row['quantity'] for row in eggs}=={'egg-6':1,'egg-10':2}
    assert sum(row['requirement']['quantity'] for row in eggs)==15
    assert next(row for row in eggs if row['sku_id']=='egg-10')['unit_price_fen']==1400
    assert all(row['added_quantity']==0 for row in plan['items'])
    assert plan['plan_kind']=='full_plan'
    assert client.get('/api/v1/cart').json()['items']==[]
    state=client.get(BASE).json()
    confirmed=client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=confirm_body(state),headers={'Idempotency-Key':'mixed-history-new-approval'})
    assert confirmed.status_code==200,confirmed.text
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']}=={'egg-6':1,'egg-10':2,'tomato-500':3}
    assert next(source for source in client.get(BASE+'/history').json()['sources'] if source['task_id']==old['task_id'])['plan']==source_plan

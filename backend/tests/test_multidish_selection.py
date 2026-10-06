"""Independent Spec review regression: preserve mixed group selection provenance."""
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_dish_public import dish_seed, prepare_dish
from test_multidish_public import append_dish, rice_seed, group_revision, confirm_body


def toggle(client,state,request_id,sku_id):
    plan=state['plan']
    result=client.post('/api/v1/guide/tasks/'+state['task_id']+'/plan-revisions',json={
        'request_id':request_id,'base_plan_id':plan['plan_id'],'base_plan_version':plan['plan_version'],
        'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
        'coverage_intent':'selection_only','items':[{'sku_id':row['sku_id'],'quantity':row['quantity'],'selected':not row['selected'] if row['sku_id']==sku_id else row['selected']} for row in plan['items']]})
    assert result.status_code==200,result.text
    return client.get(BASE).json()


def mixed_selection(client,requests):
    dish_seed(requests);rice_seed(requests)
    command(client,'new_goal',goal='六人番茄炒蛋')
    state=prepare_dish(client,requests,people=6)
    toggle(client,state,'exclude-first-eggs','egg-6')
    return append_dish(client,requests,query='蛋炒饭')


def test_unrelated_checkbox_keeps_excluded_group_demand_and_receipt_sources(pi_client):
    client,requests=pi_client
    state=mixed_selection(client,requests)
    first,second=state['plan']['groups']
    state=toggle(client,state,'unrelated-tomato','tomato-500')
    egg=next(row for row in state['plan']['items'] if row['sku_id']=='egg-6')
    assert [c['selected'] for c in egg['contributions']]==[False,True]
    assert (egg['requirement']['quantity'],egg['quantity'])==(2,1)
    revised=group_revision(client,state,'first-eight','group_update',first['group_id'],people=8)
    assert revised.status_code==200,revised.text
    state=client.get(BASE).json()
    egg=next(row for row in state['plan']['items'] if row['sku_id']=='egg-6')
    assert [c['selected'] for c in egg['contributions']]==[False,True]
    assert (egg['requirement']['quantity'],egg['quantity'])==(2,1)
    result=client.post('/api/v1/guide/tasks/'+state['task_id']+'/items/egg-6/add',json=confirm_body(state,[{'sku_id':'egg-6','quantity':1}]),headers={'Idempotency-Key':'only-second-eggs'})
    assert result.status_code==200,result.text
    record=client.get(BASE).json()['plan']['purchase_ledger'][0]
    assert [group['group_id'] for group in record['groups']]==[second['group_id']]
    assert [c['group_id'] for c in record['contributions']]==[second['group_id']]


def test_deliberate_shared_row_toggle_recomputes_all_group_demand_before_reconfirmation(pi_client):
    client,requests=pi_client
    state=mixed_selection(client,requests)
    state=toggle(client,state,'turn-off-shared-eggs','egg-6')
    state=toggle(client,state,'turn-on-shared-eggs','egg-6')
    egg=next(row for row in state['plan']['items'] if row['sku_id']=='egg-6')
    assert [c['selected'] for c in egg['contributions']]==[True,True]
    assert (egg['requirement']['quantity'],egg['coverage_quantity'],egg['quantity'])==(11,11,2)
    assert egg['leftover_quantity']==1
    assert client.get('/api/v1/cart').json()['items']==[]


def test_shared_toggle_preserves_a_separately_chosen_package_quantity(pi_client):
    client,requests=pi_client
    state=mixed_selection(client,requests)
    state=toggle(client,state,'off-before-explicit-quantity','egg-6')
    plan=state['plan']
    response=client.post('/api/v1/guide/tasks/'+state['task_id']+'/plan-revisions',json={
        'request_id':'explicit-three-packs','base_plan_id':plan['plan_id'],'base_plan_version':plan['plan_version'],
        'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
        'coverage_intent':'selection_only','items':[{'sku_id':row['sku_id'],'quantity':3 if row['sku_id']=='egg-6' else row['quantity'],'selected':row['selected']} for row in plan['items']]})
    assert response.status_code==200,response.text
    state=toggle(client,client.get(BASE).json(),'on-after-explicit-quantity','egg-6')
    egg=next(row for row in state['plan']['items'] if row['sku_id']=='egg-6')
    assert (egg['requirement']['quantity'],egg['quantity'],egg['leftover_quantity'])==(11,3,7)
    assert client.get('/api/v1/cart').json()['items']==[]


def test_shared_toggle_rechecks_budget_after_recomputed_demand(pi_client):
    client,requests=pi_client
    dish_seed(requests);rice_seed(requests)
    command(client,'new_goal',goal='六人番茄炒蛋',conditions={'budget_fen':3100})
    state=prepare_dish(client,requests,people=6)
    toggle(client,state,'budget-exclude-first-eggs','egg-6')
    state=append_dish(client,requests,query='蛋炒饭')
    state=toggle(client,state,'budget-off-shared-eggs','egg-6')
    plan=state['plan']
    response=client.post('/api/v1/guide/tasks/'+state['task_id']+'/plan-revisions',json={
        'request_id':'budget-on-shared-eggs','base_plan_id':plan['plan_id'],'base_plan_version':plan['plan_version'],
        'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
        'coverage_intent':'selection_only','items':[{'sku_id':row['sku_id'],'quantity':row['quantity'],'selected':True if row['sku_id']=='egg-6' else row['selected']} for row in plan['items']]})
    assert response.status_code==200,response.text
    assert response.json()['budget_quote']['budget_fen']==3100
    assert response.json()['budget_quote']['total_fen'] > 3100
    assert response.json()['can_confirm'] is False
    assert client.get(BASE).json()['conditions']['budget_fen']==3100
    assert client.get('/api/v1/cart').json()['items']==[]

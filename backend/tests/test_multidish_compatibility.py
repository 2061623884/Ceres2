"""Shared-budget reconstruction and synthetic TASK05 JSON migration evidence."""
import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_dish_public import dish_seed, prepare_dish, revise_dish
from test_multidish_public import append_dish, rice_seed, confirm_body


def test_budget_amend_reconstructs_all_groups_and_selected_specs_without_cart_approval(pi_client):
    client,requests=pi_client
    dish_seed(requests);rice_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋',conditions={'budget_fen':3300})
    prepare_dish(client,requests)
    state=append_dish(client,requests,query='蛋炒饭',selections={'egg':'egg-10'})
    original_groups=state['plan']['groups']
    stale=confirm_body(state)
    response=command(client,'amend',conditions={'budget_fen':4000})
    assert response.status_code==200,response.text
    assert client.get(BASE).json()['plan'] is None
    state=prepare_dish(client,requests,people=4,request_id='budget-recompute')
    assert [group['group_id'] for group in state['plan']['groups']]==[group['group_id'] for group in original_groups]
    assert state['plan']['groups'][1]==original_groups[1]
    eggs={row['sku_id']:row for row in state['plan']['items'] if row['ingredient_id']=='egg'}
    assert set(eggs)=={'egg-6','egg-10'}
    assert eggs['egg-6']['requirement']['quantity']==6
    assert eggs['egg-10']['requirement']['quantity']==2
    assert state['plan']['selected_total_fen']==3900
    assert client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=stale,headers={'Idempotency-Key':'pre-budget-confirm'}).status_code==409
    assert client.get('/api/v1/cart').json()['items']==[]


def test_synthetic_single_dish_json_upgrades_without_inventing_old_group_purchase_facts(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests)
    url='/api/v1/guide/tasks/'+state['task_id']
    body=confirm_body(state,[{'sku_id':'egg-6','quantity':1}])
    purchased=client.post(url+'/items/egg-6/add',json=body,headers={'Idempotency-Key':'legacy-egg'})
    assert purchased.status_code==200,purchased.text
    cart=client.get('/api/v1/cart').json()['items']
    # Construct isolated old-version JSON, never an archived or active database.
    from app.models.guide import GuideTask
    from app.models.purchase import PurchaseConfirmation
    with Session(requests.engine) as db:
        task=db.get(GuideTask,state['task_id'])
        conditions=json.loads(task.conditions_json)
        conditions.pop('dish_groups')
        task.conditions_json=json.dumps(conditions)
        plan=json.loads(task.plan_json)
        for field in ('groups','targets','purchase_ledger'):
            plan.pop(field)
        for row in plan['items']:
            row.pop('contributions')
        plan['confirmation_result'].pop('group_purchases')
        task.plan_json=json.dumps(plan)
        receipt=db.scalar(select(PurchaseConfirmation).where(PurchaseConfirmation.request_key=='legacy-egg'))
        result=json.loads(receipt.result_json)
        result.pop('group_purchases')
        receipt.result_json=json.dumps(result)
        db.commit()
    from app.core.database import init_db
    init_db(requests.engine);init_db(requests.engine)
    state=client.get(BASE).json()
    assert state['plan']==plan
    assert client.get('/api/v1/cart').json()['items']==cart
    updated=revise_dish(client,state,'legacy-people-five',people=5)
    assert updated.status_code==200,updated.text
    current=client.get(BASE).json()
    assert len(current['plan']['groups'])==1
    egg=next(row for row in current['plan']['items'] if row['ingredient_id']=='egg')
    assert (egg['quantity'],egg['added_quantity'],egg['remaining_quantity'])==(2,1,1)
    assert current['plan']['purchase_ledger']==[]
    assert client.post(url+'/items/egg-6/add',json=body,headers={'Idempotency-Key':'legacy-egg'}).json()==result
    assert client.get('/api/v1/cart').json()['items']==cart

"""TASK06 regression edges through public guide/plan/cart contracts."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_dish_public import dish_seed, prepare_dish
from test_multidish_public import append_dish, append_hook, rice_seed, group_revision, confirm_body


def test_fractional_source_demands_are_summed_before_rounding_and_pantry_stays_unknown(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='一人番茄炒蛋')
    prepare_dish(client,requests,people=1)
    state=append_dish(client,requests,people=1)
    tomato=next(row for row in state['plan']['items'] if row['ingredient_id']=='tomato')
    egg=next(row for row in state['plan']['items'] if row['ingredient_id']=='egg')
    assert (tomato['requirement']['quantity'],tomato['quantity'])==(300,1)
    assert (egg['requirement']['quantity'],egg['coverage_quantity'],egg['quantity'])==(3,3,1)
    assert [c['requirement']['quantity'] for c in egg['contributions']]==[1.5,1.5]
    assert all(row['requirement']['quantity'] is None for row in state['plan']['items'] if row['role']=='pantry')


def test_explicit_different_specs_remain_separate_and_survive_group_people_change(pi_client):
    client,requests=pi_client
    dish_seed(requests);rice_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    original=prepare_dish(client,requests,selections={'egg':'egg-6'})
    state=append_dish(client,requests,query='蛋炒饭',selections={'egg':'egg-10'})
    eggs=[row for row in state['plan']['items'] if row['ingredient_id']=='egg']
    assert {row['sku_id'] for row in eggs}=={'egg-6','egg-10'}
    assert [row['requirement']['quantity'] for row in eggs]==[3,2]
    second=state['plan']['groups'][1]
    response=group_revision(client,state,'rice-four','group_update',second['group_id'],people=4)
    assert response.status_code==200,response.text
    state=client.get(BASE).json()
    assert state['plan']['groups'][0]==original['plan']['groups'][0]
    eggs={row['sku_id']:row for row in state['plan']['items'] if row['ingredient_id']=='egg'}
    assert (eggs['egg-6']['requirement']['quantity'],eggs['egg-10']['requirement']['quantity'])==(3,4)
    assert all(len(row['contributions'])==1 for row in eggs.values())
    assert client.get('/api/v1/cart').json()['items']==[]


@pytest.mark.parametrize('conditions,code',[({'budget_fen':1900},'BUDGET_EXCEEDED'),({'exclusions':['rice']},'EXCLUSION_CONFLICT')])
def test_second_group_obeys_shared_budget_and_exclusions_without_partial_mutation(pi_client,conditions,code):
    client,requests=pi_client
    dish_seed(requests);rice_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋',conditions=conditions)
    original=prepare_dish(client,requests)
    requests.answer_hook=append_hook(query='蛋炒饭')
    events=turn(client,'明确再加一道蛋炒饭','blocked-addition')
    current=client.get(BASE).json()
    if code == 'BUDGET_EXCEEDED':
        assert events[-1]['type']=='turn.completed',events
        assert current['plan']['budget_quote']['budget_fen']==1900
        assert current['plan']['budget_quote']['total_fen'] > 1900
        assert current['plan']['can_confirm'] is False
        assert current['conditions']['budget_fen']==1900
        assert len(current['plan']['groups'])==2
    else:
        assert events[-1]['type']=='error',events
        assert events[-1]['payload']['code']==code,events
        assert current['plan']==original['plan']
        assert current['conditions']['dish_groups']==original['conditions']['dish_groups']
    assert client.get('/api/v1/cart').json()['items']==[]


def test_searching_an_unselected_second_recipe_does_not_add_a_target(pi_client):
    client,requests=pi_client
    dish_seed(requests);rice_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    state=prepare_dish(client,requests)
    def suggestion(body):
        outputs=[json.loads(m['content']) for m in body['messages'] if m['role']=='tool']
        if len(outputs)<2:
            name,args=('guide_request',{'kind':'continue'}) if not outputs else ('search_dishes',{'query':'蛋炒饭'})
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'suggest-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]},'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'waiting','clarification_slot':'target'})},'stop'
    requests.answer_hook=suggestion
    events=turn(client,'还有什么菜可以考虑？先别选','only-suggestion')
    assert events[-1]['type']=='turn.completed',events
    assert client.get(BASE).json()['plan']==state['plan']
    assert client.get('/api/v1/cart').json()['items']==[]


def test_group_selection_and_receipts_remain_owner_scoped(pi_client):
    client,requests=pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    prepare_dish(client,requests)
    state=append_dish(client,requests)
    client.cookies.set('sg_owner_id','pi-owner-b')
    assert group_revision(client,state,'foreign-group','group_remove',state['plan']['groups'][0]['group_id']).status_code==403
    assert client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=confirm_body(state),headers={'Idempotency-Key':'foreign-group-confirm'}).status_code==403
    client.cookies.set('sg_owner_id','pi-owner-a')
    assert client.get(BASE).json()['plan']==state['plan']
    assert client.get('/api/v1/cart').json()['items']==[]

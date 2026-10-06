"""TASK11 public historical source selection; isolated current supply, actual Pi."""
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.models.store import Offer
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_dish_public import dish_seed, prepare_dish
from test_multidish_public import append_dish, confirm_body
from test_supply_public import supply_revision


def repurchase(client, source_id, key='repurchase'):
    state = client.get(BASE).json()
    return client.post(BASE + '/history/repurchase', json={
        'request_id':key, 'source_task_id':source_id,
        'expected_task_id':state['task_id'], 'expected_state_version':state['state_version'],
        'expected_session_version':state['session_version']})


def test_history_rebuilds_current_multidish_supply_then_requires_new_confirmation(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client, 'new_goal', goal='两道番茄炒蛋')
    prepare_dish(client, requests)
    old = append_dish(client, requests)
    command(client, 'new_goal', goal='这次还是做番茄炒蛋', conditions={'people':4, 'budget_fen':10000})
    sources = client.get(BASE + '/history')
    assert sources.status_code == 200, sources.text
    source = next(row for row in sources.json()['sources'] if row['task_id'] == old['task_id'])
    assert source['plan'] == old['plan']
    with Session(requests.engine) as db:
        db.execute(update(Offer).where(Offer.sku_id == 'tomato-500').values(price_fen=700, offer_version=2))
        db.execute(update(Offer).where(Offer.sku_id.in_(['egg-6','egg-10'])).values(available_qty=0))
        db.commit()
    rebuilt = repurchase(client, source['task_id'])
    assert rebuilt.status_code == 200, rebuilt.text
    current = client.get(BASE).json()
    plan = current['plan']
    assert current['task_id'] not in (old['task_id'], source['task_id'])
    assert plan['plan_id'] != old['plan']['plan_id']
    assert plan['history_source']['task_id'] == old['task_id']
    assert plan['plan_kind'] == 'supply_preview'
    assert [group['people'] for group in plan['groups']] == [4,4]
    tomato = next(row for row in plan['items'] if row['sku_id'] == 'tomato-500')
    assert (tomato['quantity'], tomato['unit_price_fen'], tomato['added_quantity']) == (3,700,0)
    assert plan['history_changes']
    assert client.get('/api/v1/cart').json()['items'] == []
    selected = supply_revision(client,current,'history-partial','choose_partial')
    assert selected.status_code == 200, selected.text
    assert client.get('/api/v1/cart').json()['items'] == []
    current = client.get(BASE).json()
    body = confirm_body(current)
    url = '/api/v1/guide/tasks/' + current['task_id'] + '/confirm'
    confirmed = client.post(url,json=body,headers={'Idempotency-Key':'fresh-history-confirm'})
    assert confirmed.status_code == 200, confirmed.text
    assert client.post(url,json=body,headers={'Idempotency-Key':'fresh-history-confirm'}).json() == confirmed.json()
    assert {row['sku_id']:row['quantity'] for row in client.get('/api/v1/cart').json()['items']} == {'tomato-500':3}
    assert next(row for row in client.get(BASE+'/history').json()['sources'] if row['task_id']==old['task_id'])['plan'] == old['plan']


def test_related_reminder_is_once_only_checks_cart_and_ignoring_never_restores(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    old = prepare_dish(client,requests)
    fresh = command(client,'new_goal',goal='今晚番茄炒蛋').json()
    assert fresh['history_reminder']['source_task_id'] == old['task_id']
    assert fresh['task_id'] != old['task_id'] and fresh['plan'] is None
    ignored = client.post(BASE+'/history/reminder',json={'task_id':fresh['task_id'],'decision':'ignore'})
    assert ignored.status_code == 200, ignored.text
    assert client.get(BASE).json()['history_reminder'] is None
    again = command(client,'new_goal',goal='明天番茄炒蛋').json()
    assert again['history_reminder'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def history_hook(source_id=None, memory_defaults=None):
    import json
    def respond(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role']=='tool']
        def call(args):
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'history-{len(outputs)}','type':'function','function':{'name':'history_command','arguments':json.dumps(args)}}]}, 'tool_calls'
        if not outputs:
            return call({'action':'list'})
        if source_id and len(outputs)==1:
            source = next(row for row in outputs[0]['sources'] if row['task_id']==source_id)
            return call({'action':'select','source_task_id':source_id,'memory_defaults':memory_defaults or {},'memory_refs':[{'memory_id':row['memory_id'],'revision':row['revision']} for row in source['memory']['records'] if row['domain']=='shopping' and row['category'] != 'reference']})
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'history_result','history_ref':outputs[-1]['history_ref']})}, 'stop'
    return respond


def test_pi_lists_ambiguous_history_then_applies_prose_memory_to_selected_source(pi_client):
    from test_guide_semantics import turn
    from test_memory_public import memory_turn
    client, requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='番茄炒蛋')
    old = prepare_dish(client,requests)
    command(client,'new_goal',goal='另一次番茄炒蛋')
    prepare_dish(client,requests,request_id='second-old')
    command(client,'new_goal',goal='今晚番茄炒蛋')
    memory_turn(client,requests,'请记住番茄炒蛋通常做四人份',{'action':'save','category':'user','domain':'shopping','key':'people','content':'番茄炒蛋通常做四人份','source_quote':'请记住番茄炒蛋通常做四人份'},'remember-people')
    requests.answer_hook = history_hook()
    listed = turn(client,'按上次的采购','history-list')
    assert listed[-1]['type']=='turn.completed',listed
    assert len(listed[-1]['payload']['history_sources']) == 2
    assert client.get(BASE).json()['plan'] is None
    requests.answer_hook = history_hook(old['task_id'],{'people':4})
    selected = turn(client,'重新采购历史方案 '+old['task_id'],'history-select')
    assert selected[-1]['type']=='turn.completed',selected
    plan = client.get(BASE).json()['plan']
    assert plan['dish']['people'] == 4
    assert next(row for row in plan['items'] if row['sku_id']=='tomato-500')['quantity'] == 2
    assert plan['history_memory'][0]['content']=='番茄炒蛋通常做四人份'
    assert client.get('/api/v1/cart').json()['items']==[]

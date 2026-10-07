"""Public host contracts for native Pi text/tools and reference completion."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn
from test_guide_lifecycle import BASE

CANDIDATE = '我先核对一下当前处理状态，再把结果告诉你。'


def install_native_model(requests, *, approved=True, final_refs=False, mixed_final=False):
    def answer(body):
        messages = body['messages']
        users = [str(message['content']) for message in messages if message['role']=='user']
        if any(CANDIDATE in content for content in users):
            return {'role':'assistant','content':json.dumps({'merchant_claims':not approved,'execution_claims':False})}, 'stop'
        if not any(message['role']=='tool' for message in messages):
            args, name, content = {'kind':'progress'}, 'guide_request', CANDIDATE
        else:
            args = {'status':'completed','answer_kind':'products','product_refs':['never-issued']} if final_refs else {'status':'completed','answer_kind':'status'}
            name, content = 'finish_response', '已经加购，价格999元。'  # Completion prose is never surfaced.
        calls = [{'index':0,'id':name,'type':'function','function':{'name':name,'arguments':json.dumps(args)}}]
        if mixed_final and name=='finish_response':
            calls.append({'index':1,'id':'extra','type':'function','function':{'name':'search_products','arguments':json.dumps({'query':'可乐'})}})
        return {'role':'assistant','content':content,'tool_calls':calls}, 'tool_calls'
    requests.answer_hook = answer


@pytest.mark.parametrize('approved',[True,False])
def test_native_prose_is_audited_and_completion_needs_no_extra_generation(pi_client, approved):
    client, requests = pi_client
    install_native_model(requests, approved=approved)
    events = turn(client, '查看当前处理进度', 'native-interim')
    assert events[-1]['type']=='turn.completed', events
    published = [event for event in events if event['type']=='message.interim']
    assert len(published)==int(approved)
    if approved:
        assert published[0]['payload']['content']==CANDIDATE
        assert published[0]['sequence']<events[-1]['sequence']
    history = client.get(BASE+'/messages').json()['messages']
    assert sum(message['kind']=='interim' for message in history)==int(approved)
    assert all('999' not in message['content'] and '已经加购' not in message['content'] for message in history)
    assert len(requests)==3  # main + audit + main with finish_response, no summarization call
    for request in (requests[0],requests[-1]):
        assert request['tool_choice']=='auto' and 'response_format' not in request
    assert client.get('/api/v1/cart').json()['items']==[]


def test_native_completion_cannot_introduce_unqueried_product_references(pi_client):
    client, requests = pi_client
    install_native_model(requests, final_refs=True)
    events = turn(client, '查看当前处理进度', 'native-unknown-ref')
    assert events[-1]['type']=='error' and events[-1]['payload']['code']=='PI_UNKNOWN_REFERENCE'
    assert client.get('/api/v1/cart').json()['items']==[]


def test_completion_must_be_the_only_tool_in_its_iteration(pi_client):
    client, requests = pi_client
    install_native_model(requests, mixed_final=True)
    events = turn(client, '查看当前处理进度', 'native-mixed-final')
    assert events[-1]['type']=='error' and events[-1]['payload']['code']=='PI_TOOL_INVALID'
    assert client.get('/api/v1/cart').json()['items']==[]


@pytest.mark.parametrize('forged',[False,True])
def test_recipe_facts_show_source_quantities_and_fresh_offer_without_purchase(pi_client, forged):
    from sqlalchemy.orm import Session
    from sqlalchemy import select
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    client, requests = pi_client
    with Session(requests.engine) as db, db.begin():
        db.add(CatalogProduct(sku_id='fact-egg-10pc',name='Fact eggs',name_zh='事实鸡蛋10个',
            category_id='dairy',brand='受控事实',source='controlled-demo',review_status='approved',
            spec_quantity=10,spec_unit='pc',ingredient_ids=json.dumps(['egg'])))
        db.add(Offer(store_id='pi-store',sku_id='fact-egg-10pc',price_fen=500,available_qty=10,
            sellable=True,offer_version=1,is_demo=True))
    def answer(body):
        outputs = [json.loads(message['content']) for message in body['messages'] if message['role']=='tool']
        if not outputs:
            name, arguments = 'guide_request', {'kind':'question'}
        elif len(outputs)==1:
            name, arguments = 'search_dishes', {'query':'蛋'}
        else:
            refs = [row['ref'] for row in outputs[-1]['dishes'] if row['dish_id'] in ('dish-fanqie-chao-dan','dish-dan-chao-fan')]
            with Session(requests.engine) as db, db.begin():
                offer = db.scalar(select(Offer).where(Offer.sku_id=='fact-egg-10pc'))
                offer.price_fen,offer.available_qty,offer.offer_version = 777,2,2
            name, arguments = 'finish_response', {'status':'completed','answer_kind':'recipe_facts',
                'dish_refs':refs,'ingredient_ids':['unrecorded-ingredient' if forged else 'egg']}
        return {'role':'assistant','tool_calls':[{'index':0,'id':name,'type':'function',
            'function':{'name':name,'arguments':json.dumps(arguments)}}]}, 'tool_calls'
    requests.answer_hook = answer
    events = turn(client,'查番茄炒蛋和蛋炒饭的用量、共用食材以及鸡蛋价格，不准备采购','native-recipe-facts')
    if forged:
        assert events[-1]['type']=='error' and events[-1]['payload']['code']=='PI_UNKNOWN_REFERENCE'
    else:
        assert events[-1]['type']=='turn.completed', events
        text = events[-1]['payload']['message']
        assert all(fragment in text for fragment in ('番茄 300g','鸡蛋 3pc','鸡蛋 2pc','共用必需食材：鸡蛋',
            '事实鸡蛋10个','10pc','¥7.77','库存 2','recipes.json/dish-fanqie-chao-dan'))
        assert '¥5.00' not in text and '请选一道' not in text
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items']==[]

"""Native completion retains cloud evidence at actual Pi and Guide SSE seams."""
import json
import pytest

from test_runtime_pi_product_query import pi_client
from test_judge_policy_prefetch_public import policy_transport, prefetched
from test_guide_clarification_context import call
from test_guide_semantics import turn
from test_guide_lifecycle import BASE


def test_native_waiting_preserves_multiple_policy_scopes_and_role_boundary(pi_client, policy_transport):
    client, requests = pi_client

    def respond(body):
        outputs = [json.loads(message['content']) for message in body['messages'] if message['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'question'})
        if len(outputs) == 1:
            return call(body, 'search_after_sales_policy', {'query': '配送进度规则', 'category': 'delivery'})
        return call(body, 'finish_response', {
            'status': 'waiting', 'clarification_slot': 'target',
            'policy_ref': prefetched(body)['policy_ref'],
            'policy_refs': [outputs[-1]['policy_ref']], 'role_boundary': True,
        })

    requests.answer_hook = respond
    events = turn(client, '退货政策；配送进度规则；我的订单退货问题另处理，购物目标还不明确', 'native-mixed-waiting')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['runtime_status'] == 'waiting'
    assert len(result['messages']) == 3
    text = '\n'.join(message['content'] for message in result['messages'])
    assert all(fragment in text for fragment in ('哪种商品', '配送进度规则', '具体订单', '墨墨'))
    assert result['navigation_action']['request']['target_role'] == 'momo'
    assert prefetched(requests[0])['policy_ref']
    assert len(requests) == 3  # Native finish needs no extra main generation.
    assert all(request['tool_choice'] == 'auto' and 'response_format' not in request for request in requests)
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


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


@pytest.mark.parametrize('invalid', ['unknown_policy', 'unknown_product', 'mixed_finish', 'missing_route'])
def test_native_completion_rejects_unvalidated_references_and_illegal_turns(pi_client, policy_transport, invalid):
    client, requests = pi_client
    def respond(body):
        outputs = [json.loads(message['content']) for message in body['messages'] if message['role']=='tool']
        if not outputs and invalid != 'missing_route':
            return call(body, 'guide_request', {'kind':'question'})
        args = {'status':'waiting','clarification_slot':'target','policy_ref':prefetched(body)['policy_ref']}
        if invalid == 'unknown_policy':
            args['policy_refs'] = ['foreign-policy-reference']
        elif invalid == 'unknown_product':
            args = {'status':'completed','answer_kind':'products','product_refs':['never-issued']}
        result = call(body, 'finish_response', args)
        if invalid == 'mixed_finish':
            result[0]['tool_calls'].append({'index':1,'id':'extra-read','type':'function',
                'function':{'name':'search_products','arguments':json.dumps({'query':'可乐'})}})
        return result
    requests.answer_hook = respond
    events = turn(client, '退货条件', 'native-invalid-'+invalid)
    assert events[-1]['type']=='error', events
    assert events[-1]['payload']['code'] == ('PI_UNKNOWN_REFERENCE' if invalid in ('unknown_policy','unknown_product') else 'PI_TOOL_INVALID')
    assert not any(event['type']=='answer.delta' for event in events)
    assert client.get(BASE+'/messages').json()['messages']==[]
    assert client.get('/api/v1/cart').json()['items']==[]


@pytest.mark.parametrize('optional,forged', [(True,False),(False,False),(True,True)])
def test_recipe_optional_facts_preserve_unknown_amount_without_procurement(pi_client, tmp_path, monkeypatch, optional, forged):
    from types import SimpleNamespace
    from app.services import dish_service
    client, requests = pi_client
    source = dish_service.get_settings().root_dir / 'data/fixtures/recipes.json'
    corpus = json.loads(source.read_text())
    selected = next(dish for dish in corpus['dishes'] if dish['dish_id']=='dish-fanqie-chao-dan')
    selected['optional_items'] = [{'ingredient_id':'scallion','quantity_g':5}, {'ingredient_id':'green_pea'}] if optional else []
    fixtures = tmp_path / 'optional-source/data/fixtures'
    fixtures.mkdir(parents=True)
    (fixtures/'recipes.json').write_text(json.dumps(corpus, ensure_ascii=False))
    monkeypatch.setattr(dish_service, 'get_settings', lambda:SimpleNamespace(root_dir=fixtures.parent.parent))
    def respond(body):
        outputs = [json.loads(message['content']) for message in body['messages'] if message['role']=='tool']
        if not outputs:
            return call(body, 'guide_request', {'kind':'question'})
        if len(outputs)==1:
            return call(body, 'search_dishes', {'query':'番茄炒蛋'})
        result = {'status':'completed','answer_kind':'recipe_facts','dish_refs':[outputs[-1]['dishes'][0]['ref']]}
        if optional:
            result['ingredient_ids'] = ['scallion']
        if forged:
            result['ingredient_ids'] = ['not-a-source-ingredient']
        return call(body, 'finish_response', result)
    requests.answer_hook = respond
    events = turn(client, '只查番茄炒蛋的必需和可选食材及用量，不采购', 'recipe-optional')
    if forged:
        assert events[-1]['type']=='error' and events[-1]['payload']['code']=='PI_UNKNOWN_REFERENCE'
    else:
        assert events[-1]['type']=='turn.completed', events
        text = events[-1]['payload']['message']
        if optional:
            assert '可选食材：葱 5g、豌豆（用量未记录）' in text
        else:
            assert '可选食材：来源未记录可选项' in text
        assert '必需食材 番茄 300g、鸡蛋 3pc' in text
        assert 'recipes.json/dish-fanqie-chao-dan' in text
    state = client.get(BASE).json()
    assert state['task_id'] is None and state['plan'] is None
    assert client.get('/api/v1/cart').json()['items']==[]


@pytest.mark.parametrize('kind,extra', [('waiting',{'product_refs':['foreign-product']}),
    ('status',{'dish_refs':['foreign-dish']}), ('policy_result',{'general_ref':'unaudited-general'})])
def test_native_finish_rejects_references_inapplicable_to_primary_result(pi_client, policy_transport, kind, extra):
    client, requests = pi_client
    def respond(body):
        outputs = [json.loads(message['content']) for message in body['messages'] if message['role']=='tool']
        if not outputs:
            return call(body, 'guide_request', {'kind':'progress' if kind=='status' else 'question'})
        result = {'status':'waiting','clarification_slot':'target'} if kind=='waiting' else {'status':'completed','answer_kind':kind}
        result.update(policy_ref=prefetched(body)['policy_ref'], role_boundary=True, **extra)
        return call(body, 'finish_response', result)
    requests.answer_hook = respond
    events = turn(client, '退货条件', 'native-unrelated-'+kind)
    assert events[-1]['type']=='error' and events[-1]['payload']['code']=='PI_UNKNOWN_REFERENCE', events
    assert not any(event['type']=='answer.delta' for event in events)
    assert client.get(BASE+'/messages').json()['messages']==[]
    assert client.get('/api/v1/cart').json()['items']==[]

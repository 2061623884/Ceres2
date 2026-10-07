"""Category comparison through the actual Pi worker and public SSE/session boundary."""
import json
from sqlalchemy.orm import Session
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn


def comparison_hook(body):
    outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
    def call(name, args):
        return {'role':'assistant','tool_calls':[{'index':0,'id':f'comparison-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
    if not outputs:
        return call('guide_request', {'kind':'continue'})
    if len(outputs) == 1:
        return call('compare_products', {'category_id':'beverage'})
    return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'comparison','product_refs':[p['ref'] for p in outputs[-1]['products']]})}, 'stop'


def seed_multipack(requests):
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer, Store
    with Session(requests.engine) as db:
        db.get(Store, 'pi-store').delivery_reachable = True
        db.add(CatalogProduct(sku_id='pi-cola-six', name='Six cola cans', name_zh='测试六罐可乐', category_id='beverage', brand='真实品牌', spec_quantity=1980, spec_unit='ml', metadata_json=json.dumps({'pack_count':6,'packaging':'can','item_quantity':330,'item_unit':'ml'})))
        db.flush()
        db.add(Offer(store_id='pi-store',sku_id='pi-cola-six',price_fen=1800,available_qty=8))
        db.commit()


def test_comparison_projects_real_multipack_and_unknown_metadata_without_plan_or_cart(pi_client):
    client, requests = pi_client
    seed_multipack(requests)
    command(client,'new_goal',goal='比较饮料')
    requests.answer_hook = comparison_hook
    events = turn(client,'比较当前饮料品牌、包装和每升价格','comparison-first')
    assert events[-1]['type'] == 'turn.completed', events
    cards = events[-1]['payload']['product_cards']
    assert len(cards) == 2
    known = next(c for c in cards if c['sku_id'] == 'pi-cola-six')
    assert (known['brand'],known['packaging'],known['pack_count']) == ('真实品牌','can',6)
    assert known['item_volume_ml'] == 330
    assert known['total_volume_ml'] == 1980
    assert abs(known['price_per_litre_yuan'] - 9.09090909) < 0.000001
    unknown = next(c for c in cards if c['sku_id'] == 'pi-cola')
    assert unknown['brand'] is None and unknown['packaging'] is None
    assert unknown['pack_count'] is None and unknown['item_volume_ml'] is None
    state = client.get(BASE).json()
    assert state['product_cards'] == cards
    assert state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def posted_turn(client, message, request_id, displayed_refs=(), view_context=None):
    state = client.get(BASE).json()
    response = client.post(BASE + '/turns/stream', json={
        'message':message,'request_id':request_id,
        'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],
        'expected_session_version':state['session_version'],
        'displayed_candidate_refs':list(displayed_refs),'view_context':view_context,
    })
    assert response.status_code == 200, response.text
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]


def select_hook(ref):
    def hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            name, args = ('guide_request',{'kind':'continue'}) if not outputs else ('propose_purchase',{'ref':ref,'quantity':1})
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'select-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'purchase_plan','proposal_ref':outputs[-1]['proposal_ref']})}, 'stop'
    return hook


def test_displayed_current_candidate_selected_in_later_pi_turn_prepares_then_confirms(pi_client):
    client, requests = pi_client
    seed_multipack(requests)
    command(client,'new_goal',goal='比较后选一款可乐')
    requests.answer_hook = comparison_hook
    events = turn(client,'比较饮料','selection-compare')
    cards = events[-1]['payload']['product_cards']
    selected = next(c for c in cards if c['sku_id'] == 'pi-cola-six')
    requests.answer_hook = select_hook(selected['ref'])
    first_request = len(requests)
    events = posted_turn(client,f"选候选 {selected['ref']} 一包，生成清单",'selection-choose',[c['ref'] for c in cards])
    assert events[-1]['type'] == 'turn.completed', events
    from test_guide_clarification_context import context
    assert context(requests[first_request])['comparison_candidates'] == cards
    state = client.get(BASE).json()
    assert [r['sku_id'] for r in state['plan']['items']] == ['pi-cola-six']
    assert state['plan']['items'][0]['quantity'] == 1
    assert client.get('/api/v1/cart').json()['items'] == []
    body = {'plan_id':state['plan']['plan_id'],'plan_version':state['plan']['plan_version'],
            'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
            'selected_items':[{'sku_id':'pi-cola-six','quantity':1}]}
    confirmed = client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=body,headers={'Idempotency-Key':'comparison-confirm'})
    assert confirmed.status_code == 200, confirmed.text
    assert [(r['sku_id'],r['quantity']) for r in client.get('/api/v1/cart').json()['items']] == [('pi-cola-six',1)]


def test_task_filters_and_page_category_are_preserved_and_empty_retires_refs(pi_client):
    client, requests = pi_client
    seed_multipack(requests)
    command(client,'new_goal',goal='比较当前品类',conditions={'brand':'真实品牌','packaging':'can','pack_count_mode':'multi','budget_fen':2000})
    def page_hook(body):
        delta, reason = comparison_hook(body)
        if delta.get('tool_calls') and delta['tool_calls'][0]['function']['name'] == 'compare_products':
            delta['tool_calls'][0]['function']['arguments'] = json.dumps({'query':'测试'})
        return delta, reason
    requests.answer_hook = page_hook
    page = {'page':'category','category_id':'beverage'}
    events = posted_turn(client,'按原筛选比较当前品类','filter-first',view_context=page)
    assert events[-1]['type'] == 'turn.completed', events
    cards = events[-1]['payload']['product_cards']
    assert [c['sku_id'] for c in cards] == ['pi-cola-six']
    conditions = client.get(BASE).json()['conditions']
    assert conditions == {'brand':'真实品牌','packaging':'can','pack_count_mode':'multi','budget_fen':2000}
    command(client,'amend',conditions={'budget_fen':1000})
    events = posted_turn(client,'保留品牌包装，只看预算内','filter-empty',view_context=page)
    assert events[-1]['type'] == 'turn.completed', events
    assert events[-1]['payload']['product_cards'] == []
    state = client.get(BASE).json()
    assert state['product_cards'] == [] and state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    requests.answer_hook = select_hook(cards[0]['ref'])
    events = posted_turn(client,'选择旧候选','filter-old-ref',[cards[0]['ref']],page)
    assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'COMPARISON_STALE'


def test_comparison_exploration_cannot_turn_unselected_recommendation_into_plan(pi_client):
    client, requests = pi_client
    seed_multipack(requests)
    command(client,'new_goal',goal='只比较饮料，不选定')
    def unsolicited(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            return comparison_hook(body)
        if len(outputs) == 2:
            return {'role':'assistant','tool_calls':[{'index':0,'id':'unsolicited-plan','type':'function','function':{'name':'propose_purchase','arguments':json.dumps({'ref':outputs[-1]['products'][0]['ref'],'quantity':1})}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'purchase_plan','proposal_ref':outputs[-1]['proposal_ref']})}, 'stop'
    requests.answer_hook = unsolicited
    events = turn(client,'只比较，别替我选','unsolicited-comparison')
    assert events[-1]['type'] == 'error', events
    assert events[-1]['payload']['code'] == 'COMPARISON_SELECTION_REQUIRED'
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_finite_candidates_honor_exclusions_and_do_not_compare_mass_as_volume(pi_client):
    client, requests = pi_client
    seed_multipack(requests)
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    with Session(requests.engine) as db:
        db.get(CatalogProduct,'pi-cola').spec_unit = 'g'
        for index in range(6):
            sku = f'pi-extra-{index}'
            db.add(CatalogProduct(sku_id=sku,name=f'Extra drink {index}',name_zh=f'额外饮料 {index}',category_id='beverage',spec_quantity=500,spec_unit='ml'))
            db.flush()
            db.add(Offer(store_id='pi-store',sku_id=sku,price_fen=500,available_qty=10))
        db.commit()
    command(client,'new_goal',goal='比较饮料',conditions={'exclusions':['pi-cola-six']})
    requests.answer_hook = comparison_hook
    events = turn(client,'比较五个候选，保留排除条件','bounded-comparison')
    assert events[-1]['type'] == 'turn.completed', events
    cards = events[-1]['payload']['product_cards']
    assert len(cards) == 5
    assert 'pi-cola-six' not in [card['sku_id'] for card in cards]
    nonvolume = next(card for card in cards if card['sku_id'] == 'pi-cola')
    assert (nonvolume['spec_quantity'],nonvolume['spec_unit']) == (330,'g')
    assert nonvolume['total_volume_ml'] is None and nonvolume['price_per_litre_yuan'] is None
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []

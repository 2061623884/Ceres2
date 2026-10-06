"""Current conditions apply to ordinary Pi search and comparison recommendations."""
import json
import pytest
from sqlalchemy.orm import Session
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_next_drinks_public import seed_drinks


@pytest.mark.parametrize('tool', ['compare_products', 'search_products'])
@pytest.mark.parametrize('conditions', [
    {'excluded_allergens':['milk']},
    {'dietary_requirements':['vegan']},
    {'flavor':'桃味', 'spec':{'quantity':330, 'unit':'ml'}, 'product_type':'tea'},
])
def test_current_conditions_survive_ordinary_recommendation_tools(pi_client, tool, conditions):
    client, requests = pi_client
    seed_drinks(requests)
    from app.models.catalog import CatalogProduct
    with Session(requests.engine) as db:
        allowed = db.get(CatalogProduct, 'DR-tea-peach-small')
        metadata = json.loads(allowed.metadata_json)
        metadata['attribute_evidence'] = {'allergens':{'value':[], 'source':'controlled label'}, 'vegan':{'value':True, 'source':'controlled label'}}
        allowed.metadata_json = json.dumps(metadata)
        db.commit()
    assert command(client, 'new_goal', goal='按当前条件选饮品', conditions=conditions).status_code == 200
    def hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            name, args = ('guide_request', {'kind':'continue'}) if not outputs else (tool, {'category_id':'beverage'})
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'condition-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'comparison' if tool == 'compare_products' else 'products','product_refs':[p['ref'] for p in outputs[-1]['products']]})}, 'stop'
    requests.answer_hook = hook
    events = turn(client, '按当前条件比较饮品', 'current-conditions')
    assert events[-1]['type'] == 'turn.completed', events
    assert {p['sku_id'] for p in events[-1]['payload']['product_evidence']} == {'DR-tea-peach-small'}
    assert client.get(BASE).json()['conditions'] == conditions
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('tool', ['compare_products', 'search_products'])
def test_unknown_dietary_evidence_is_a_supported_empty_result(pi_client, tool):
    client, requests = pi_client
    seed_drinks(requests)
    command(client, 'new_goal', goal='只看有证据的饮品', conditions={'dietary_requirements':['vegan']})
    def hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            name, args = ('guide_request', {'kind':'continue'}) if not outputs else (tool, {'category_id':'beverage'})
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'empty-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'comparison' if tool == 'compare_products' else 'products','product_refs':[p['ref'] for p in outputs[-1]['products']]})}, 'stop'
    requests.answer_hook = hook
    events = turn(client, '按当前饮食条件查询', 'empty-dietary')
    assert events[-1]['type'] == 'turn.completed', events
    assert events[-1]['payload']['no_matches'] is True
    assert events[-1]['payload']['product_evidence'] == []
    assert client.get(BASE).json()['conditions'] == {'dietary_requirements':['vegan']}
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('explicit_category', [False, True])
@pytest.mark.parametrize('diet_evidenced', [False, True])
def test_explicit_raw_product_search_leaves_shelf_scope_but_keeps_dietary_constraint(pi_client, explicit_category, diet_evidenced):
    from app.models.catalog import CatalogProduct
    from test_comparison_public import posted_turn
    client, requests = pi_client
    if diet_evidenced:
        with Session(requests.engine) as db:
            cola = db.get(CatalogProduct, 'pi-cola')
            cola.metadata_json = json.dumps({'attribute_evidence':{'vegan':{'value':True,'source':'controlled label'}}})
            db.commit()
    def hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            name, args = 'guide_request', {'kind':'new_goal','goal':'查可乐','conditions':{'dietary_requirements':['vegan'], 'category_id':'beverage'}}
        elif len(outputs) == 1:
            name, args = 'search_products', {'category_id':'beverage'} if explicit_category else {'query':'可乐'}
        else:
            return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'products','product_refs':[p['ref'] for p in outputs[-1]['products']]})}, 'stop'
        return {'role':'assistant','tool_calls':[{'index':0,'id':f'cross-shelf-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
    requests.answer_hook = hook
    events = posted_turn(client, '换个目标，查符合纯素条件的可乐', 'cross-shelf-search', view_context={'page':'category','category_id':'fruit'})
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert {p['sku_id'] for p in result['product_evidence']} == ({'pi-cola'} if diet_evidenced else set())
    assert result['no_matches'] is not diet_evidenced
    assert client.get(BASE).json()['conditions'] == {'dietary_requirements':['vegan'], 'category_id':'beverage'}
    assert result['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []

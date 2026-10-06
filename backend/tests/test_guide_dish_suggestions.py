"""Grounded meal suggestions do not select a dish or authorize cart writes."""
import json
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_guide_clarification_context import answer, call, context
from test_dish_public import dish_seed


def suggestions(body):
    outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
    if not outputs:
        return call(body,'guide_request',{'kind':'continue'})
    if len(outputs) == 1:
        return call(body,'search_dishes',{'query':'蛋'})
    return answer({'status':'completed','answer_kind':'dish_candidates','dish_refs':[d['ref'] for d in outputs[-1]['dishes']]})


def test_suggestions_then_first_choice_requeries_recipe_and_waits_for_confirmation(pi_client):
    client, requests = pi_client
    dish_seed(requests)
    command(client,'new_goal',goal='今晚做一道菜，帮我推荐')
    requests.answer_hook = suggestions
    events = turn(client,'推荐几道鸡蛋菜，先别选','dish-options')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert '1. 番茄炒蛋' in result['message']
    assert '2. 蛋炒饭' in result['message']
    assert result['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    observed = []
    def choose(body):
        facts = context(body)
        observed.append(facts)
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return call(body,'guide_request',{'kind':'continue'})
        if len(outputs) == 1:
            candidates = facts.get('dish_candidates', [])
            if not candidates:
                return answer({'status':'waiting','clarification_slot':'target'})
            return call(body,'search_dishes',{'query':candidates[0]['name']})
        if len(outputs) == 2:
            return call(body,'propose_dish',{'dish_ref':outputs[-1]['dishes'][0]['ref']})
        return answer({'status':'completed','answer_kind':'purchase_plan','proposal_ref':outputs[-1]['proposal_ref']})
    requests.answer_hook = choose
    chosen = turn(client,'第一道，给我清单','dish-choice')[-1]
    assert chosen['type'] == 'turn.completed', chosen
    assert chosen['payload']['plan']['dish']['dish_id'] == 'dish-fanqie-chao-dan'
    assert observed[0]['dish_candidates'][0]['name'] == '番茄炒蛋'
    assert client.get(BASE + '/turns/dish-choice').json()['status'] == 'waiting_confirmation'
    assert client.get('/api/v1/cart').json()['items'] == []


def test_forged_dish_reference_is_not_rendered(pi_client):
    client, requests = pi_client
    requests.answer_hook = lambda body: answer({'status':'completed','answer_kind':'dish_candidates','dish_refs':['forged']})
    events = turn(client,'推荐菜品','forged-dish')
    assert events[-1]['type'] == 'error', events


def test_product_search_cannot_ground_empty_recipe_claim(pi_client):
    client, requests = pi_client
    def invalid(body):
        if not any(m['role'] == 'tool' for m in body['messages']):
            return call(body,'search_products',{'query':'可乐'})
        return answer({'status':'completed','answer_kind':'dish_candidates','dish_refs':[]})
    requests.answer_hook = invalid
    events = turn(client,'查询商品不等于查过菜谱','unqueried-dishes')
    assert events[-1]['type'] == 'error', events


def test_omitting_found_dishes_does_not_claim_no_recipe_matches(pi_client):
    client, requests = pi_client
    def omit(body):
        if not any(m['role'] == 'tool' for m in body['messages']):
            return call(body,'search_dishes',{'query':'番茄炒蛋'})
        return answer({'status':'completed','answer_kind':'dish_candidates','dish_refs':[]})
    requests.answer_hook = omit
    events = turn(client,'查询菜品但未展示选择','omitted-dishes')
    assert events[-1]['type'] == 'turn.completed', events
    assert '没有查到' not in events[-1]['payload']['message']
    assert '没有选定展示' in events[-1]['payload']['message']

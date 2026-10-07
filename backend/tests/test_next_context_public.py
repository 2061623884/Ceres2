"""Same fixed public journeys using role-first, then Pi-understood context."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn, hook as conversation_hook
from test_guide_lifecycle import BASE, command
from test_next_snack_public import seed_snacks, exploration_hook
from test_next_shared_policy_public import policy_hook


@pytest.mark.parametrize('journey', ['exploration', 'purchase_modification', 'factual_qa', 'chat'])
def test_same_four_journeys_preserve_public_business_semantics(pi_client, controlled_kev_transport, journey):
    client, requests = pi_client
    controlled_kev_transport['choose'] = lambda state: 'no'
    if journey == 'exploration':
        seed_snacks(requests)
        command(client, 'new_goal', goal='零食', conditions={'budget_fen':1000})
        requests.answer_hook = exploration_hook
        message = '来点零食'
    elif journey == 'purchase_modification':
        command(client, 'new_goal', goal='可乐', conditions={'quantity':2})
        requests.answer_hook = conversation_hook
        message = '预算改成十元'
    elif journey == 'factual_qa':
        requests.answer_hook = policy_hook
        message = '先了解退货政策'
    else:
        requests.answer_hook = conversation_hook
        message = '为什么天空会出现彩虹？'
    before_cart = client.get('/api/v1/cart').json()
    events = turn(client, message, 'fixed-' + journey)
    assert events[-1]['type'] == 'turn.completed', events
    state = client.get(BASE).json()
    result = events[-1]['payload']
    if journey == 'exploration':
        assert {o['label'] for o in result['active_question']['options']} == {'薯片', '饼干'}
        assert state['conditions'] == {'budget_fen':1000}
    elif journey == 'purchase_modification':
        assert state['conditions'] == {'quantity':2, 'budget_fen':1000}
        assert result['product_evidence'][0]['price_fen'] == 350
    elif journey == 'factual_qa':
        assert 'P-RET-01' in result['message'] and '具体订单资格尚未核实' in result['message']
        assert state['task_id'] is None
    else:
        assert result['answer_kind'] == 'general_explanation'
        assert '彩虹' in result['message'] and state['task_id'] is None
    assert state['plan'] is None
    assert client.get('/api/v1/cart').json() == before_cart
    assert len(controlled_kev_transport['calls']) == 1


def test_chat_uses_relevant_context_while_preserving_pending_shopping(pi_client, controlled_kev_transport):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='零食', conditions={'budget_fen':1000})
    requests.answer_hook = exploration_hook
    shopping = turn(client, '来点零食', 'before-chat')[-1]['payload']
    question = shopping['active_question']
    controlled_kev_transport['choose'] = lambda state: 'no'
    requests.clear()
    requests.answer_hook = conversation_hook
    events = turn(client, '为什么天空会出现彩虹？', 'bounded-chat')
    assert events[-1]['type'] == 'turn.completed', events
    assert client.get(BASE).json()['active_question'] == question
    assert client.get(BASE).json()['conditions'] == {'budget_fen':1000}
    assert client.get('/api/v1/cart').json()['items'] == []
    first = requests[0]
    tools = {tool['function']['name'] for tool in first['tools']}
    assert 'validate_general_text' in tools and 'guide_request' in tools
    assert 'propose_dish' in tools, 'Initial understanding receives the full Coco role tooling'
    system = next(m['content'] for m in first['messages'] if m['role'] == 'system')
    assert question['question_id'] in system, 'Pi must understand the original message before narrowing context'
    next_tools = {tool['function']['name'] for tool in requests[1]['tools']}
    next_system = next(m['content'] for m in requests[1]['messages'] if m['role'] == 'system')
    assert 'propose_dish' not in next_tools and question['question_id'] not in next_system
    assert len(controlled_kev_transport['calls']) == 2


def test_role_first_context_preserves_mixed_request_and_shopping_after_pi_understanding(pi_client, controlled_kev_transport):
    client, requests = pi_client
    seed_snacks(requests)
    initial = command(client, 'new_goal', goal='买零食', conditions={'quantity':2, 'budget_fen':2000}).json()
    controlled_kev_transport['choose'] = lambda state: 'no'
    original = '谢谢，顺便把预算改成十元，还是两包零食，继续让我选类型，先别加购。'
    def mixed_hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            name, args = 'guide_request', {'kind':'amend', 'conditions':{'budget_fen':1000}}
        elif len(outputs) == 1:
            name, args = 'explore_products', {'category_id':'snack'}
        else:
            return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'exploration','exploration_ref':outputs[-1]['exploration_ref']})}, 'stop'
        return {'role':'assistant','tool_calls':[{'index':0,'id':f'mixed-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
    requests.answer_hook = mixed_hook
    events = turn(client, original, 'mixed-relevance')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    state = client.get(BASE).json()
    assert state['task_id'] == initial['task_id']
    assert state['conditions'] == {'quantity':2, 'budget_fen':1000}
    assert {o['value'] for o in result['active_question']['options']} == {'snack-chips-small'}
    first_tools = {t['function']['name'] for t in requests[0]['tools']}
    next_tools = {t['function']['name'] for t in requests[1]['tools']}
    assert 'explore_products' in first_tools and 'explore_products' in next_tools
    assert original in json.dumps(requests[0]['messages'], ensure_ascii=False)
    assert len(controlled_kev_transport['calls']) == 1
    assert state['plan'] is None and client.get('/api/v1/cart').json()['items'] == []


def test_factual_recipe_question_keeps_read_only_dish_facts_without_purchase_task(pi_client, controlled_kev_transport):
    client, requests = pi_client
    from test_dish_public import dish_seed
    dish_seed(requests)
    controlled_kev_transport['choose'] = lambda state: 'no'
    def recipe_hook(body):
        outputs = [json.loads(m['content']) if m['content'].startswith('{') else {'tool_error':m['content']} for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            name, args = 'guide_request', {'kind':'question'}
        elif len(outputs) == 1:
            name, args = 'search_dishes', {'query':'番茄炒蛋'}
        else:
            # A missing read-only tool must become a public assertion failure,
            # not a fixture exception that obscures the runtime regression.
            refs = [row['ref'] for row in outputs[-1].get('dishes', [])]
            return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'dish_candidates','dish_refs':refs})}, 'stop'
        return {'role':'assistant','tool_calls':[{'index':0,'id':f'recipe-fact-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
    requests.answer_hook = recipe_hook
    events = turn(client, '只看看番茄炒蛋的菜谱，不准备采购', 'recipe-fact')
    assert events[-1]['type'] == 'turn.completed', events
    assert [d['dish_id'] for d in events[-1]['payload']['dish_candidates']] == ['dish-fanqie-chao-dan']
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    assert len(controlled_kev_transport['calls']) == 1

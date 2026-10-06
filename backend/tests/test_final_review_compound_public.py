"""One Pi turn can deliver shopping choices and independently validated policy."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_next_snack_public import seed_snacks


@pytest.mark.parametrize('forged', [False, True])
def test_compound_shopping_policy_keeps_both_results_and_reference_fences(pi_client, controlled_kev_transport, forged):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='买零食', conditions={'quantity':2})
    def hook(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        calls = [('guide_request', {'kind':'continue'}), ('explore_products', {'category_id':'snack'}), ('search_after_sales_policy', {'query':'退货政策', 'category':'return'})]
        if len(outputs) < len(calls):
            name, args = calls[len(outputs)]
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'compound-{len(outputs)}','type':'function','function':{'name':name,'arguments':json.dumps(args)}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'exploration','exploration_ref':outputs[1]['exploration_ref'],'policy_ref':'foreign-policy' if forged else outputs[2]['policy_ref']})}, 'stop'
    requests.answer_hook = hook
    events = turn(client, '来点零食，也说明退货政策', 'compound-policy')
    if forged:
        assert events[-1]['type'] == 'error'
        assert events[-1]['payload']['code'] == 'PI_UNKNOWN_REFERENCE'
        assert client.get(BASE).json()['active_question'] is None
    else:
        assert events[-1]['type'] == 'turn.completed', events
        result = events[-1]['payload']
        question = result['active_question']
        assert question['kind'] == 'category'
        assert {o['label'] for o in question['options']} == {'薯片', '饼干'}
        assert len(result['messages']) == 2
        assert result['messages'][0]['message_id'] == question['question_id']
        policy = result['messages'][1]['content']
        assert all(text in policy for text in ['P-RET-01', '来源', '7 天', '具体订单资格尚未核实', '未提交任何申请'])
        restored = client.get(BASE, params={'include_messages':True}).json()
        assert restored['active_question'] == question
        assert any(message['content'] == policy for message in restored['messages'])
    assert len(controlled_kev_transport['calls']) == 1
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []

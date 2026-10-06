"""Public request contracts; scripted output is not a language-quality score."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_next_result_stream_public import _prepare_cards, _refund_result
from test_guide_lifecycle import BASE


@pytest.mark.parametrize('role', ['keke', 'momo'])
def test_two_role_expression_preserves_facts_and_receipts_with_relevant_brief_instructions(pi_client, role):
    if role == 'keke':
        client, requests = pi_client
        snapshot = _prepare_cards(client, requests)
        endpoint = BASE + '/result-introductions'
        body = {'source_kind':'question_answer', 'source_id':'intro-type'}
    else:
        client, requests, guide, case, receipt = _refund_result(pi_client)
        endpoint = case + '/result-introductions'
        body = {'source_id':receipt['receipt_id']}
    observed = []
    def expression(request):
        observed.append(request)
        assert not request.get('tools')
        checking = 'CERES_GENERAL_CLAIM_CHECK' in json.dumps(request['messages'])
        content = json.dumps({'merchant_claims':False, 'execution_claims':False}) if checking else json.dumps({'text':'按你的需要来就好。', 'fact_ref':'result'})+'\n'
        return {'role':'assistant', 'content':content}, 'stop'
    requests.answer_hook = expression
    admitted = client.post(endpoint, json=body)
    assert admitted.status_code == 202, admitted.text
    run = admitted.json()
    stream = client.get('/api/v1/guide/sessions/'+run['session_id']+'/runs/'+run['run_id']+'/stream')
    events = [json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['payload']['expression_status'] == 'completed', events
    assert len(observed) == 2
    generation = observed[0]['messages']
    system = '\n'.join(m['content'] for m in generation if m['role']=='system')
    user_content = next(m['content'] for m in generation if m['role']=='user')
    facts = json.loads(''.join(block['text'] for block in user_content if block['type']=='text'))['facts']
    visible = ''.join(e['payload']['delta'] for e in events if e['type']=='answer.delta')
    assert visible == facts['result'] + '按你的需要来就好。'
    if role == 'keke':
        assert '模拟数据' in visible
        assert client.get(BASE).json()['active_question'] == snapshot['active_question']
        assert client.get('/api/v1/cart').json()['items'] == []
    else:
        assert '模拟' in visible and '到账' in facts['next_step']
        assert client.get(case+'/aftersales').json()['receipts'] == [receipt]
    assert client.post(endpoint,json=body).json() == run
    assert len(observed) == 2
    print(json.dumps({'role':role, 'generation_messages':generation,
        'validation_messages':observed[1]['messages'], 'visible':visible,
        'metrics':[e['payload'] for e in events if e['type']=='expression.metric'],
        'observed_calls':len(observed)}, ensure_ascii=False))
    # Delivered instructions only; adherence and naturalness require real samples.
    assert '先结果' in system
    assert '不要重复当前问题' in system
    assert 'Do not add a generic shopping invitation to an application receipt' in system
    assert 'Start with the result reference' in system

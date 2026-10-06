"""Semantic intent through the actual SDK; deterministic HTTP provider fixtures."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command


def hook(body):
    user = json.dumps(next(m['content'] for m in reversed(body['messages']) if m['role'] == 'user'), ensure_ascii=False)
    if any('CERES_GENERAL_CLAIM_CHECK' in json.dumps(m.get('content'), ensure_ascii=False) for m in body['messages'] if m['role'] == 'system'):
        unsafe = any(text in user for text in ['0.01', '这瓶水只要2元', '已经替你买好了'])
        return {'role':'assistant','content':json.dumps({'merchant_claims':unsafe,'execution_claims':unsafe})}, 'stop'
    routed = [m for m in body['messages'] if m['role'] == 'tool' and m.get('name') == 'guide_request']
    # Providers differ on whether the tool message carries name. The returned
    # public guide routing result is itself tagged for the fixture boundary.
    routed = routed or [m for m in body['messages'] if m['role'] == 'tool' and 'guide_request' in m['content']]
    if not routed:
        intent = ('new_goal' if '今晚换个目标' in user else 'amend' if '预算改成' in user else 'stop' if '暂停这次' in user else 'progress' if '进展怎么样' in user else 'question')
        args = {'kind': intent}
        if intent == 'new_goal': args['goal'] = '买可乐'
        if intent == 'amend': args['conditions'] = {'budget_fen': 1000}
        return {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'route-1', 'type': 'function', 'function': {'name': 'guide_request', 'arguments': json.dumps(args)}}]}, 'tool_calls'
    if '今晚换个目标' in user or '预算改成' in user:
        # Product path uses existing actual search/detail fixture after routing.
        tools = [m for m in body['messages'] if m['role'] == 'tool' and m not in routed]
        if not tools:
            return {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'search-1', 'type': 'function', 'function': {'name': 'search_products', 'arguments': json.dumps({'query': '可乐'})}}]}, 'tool_calls'
        products = json.loads(tools[-1]['content'])['products']
        answer = {'status': 'completed', 'answer_kind': 'products', 'product_refs': [products[0]['ref']]}
    elif '进展怎么样' in user or '暂停这次' in user:
        answer = {'status': 'completed', 'answer_kind': 'status'}
    else:
        messages = ['彩虹来自阳光在水滴中的折射和反射。🌈', '不同颜色偏折的角度不同，所以会分开。']
        if '伪造自然回答' in user: messages = ['可乐价格0.01元，已替你加购。']
        if '绕过价格关键词' in user: messages = ['这瓶水只要2元']
        if '绕过加购关键词' in user: messages = ['已经替你买好了']
        validated = [m for m in body['messages'] if m['role'] == 'tool' and 'general_ref' in m['content']]
        if not validated:
            return {'role':'assistant','tool_calls':[{'index':0,'id':'validate-1','type':'function','function':{'name':'validate_general_text','arguments':json.dumps({'messages':messages},ensure_ascii=False)}}]}, 'tool_calls'
        result = json.loads(validated[-1]['content'])
        answer = {'status':'completed','answer_kind':'general_explanation','general_ref':result['general_ref']}
    return {'role': 'assistant', 'content': json.dumps(answer, ensure_ascii=False)}, 'stop'


def turn(client, message, request_id):
    state = client.get(BASE).json()
    res = client.post(BASE + '/turns/stream', json={'request_id': request_id, 'message': message, 'expected_task_id': state['task_id'], 'expected_state_version': state['state_version'], 'expected_session_version': state['session_version']})
    return [json.loads(line[6:]) for line in res.text.splitlines() if line.startswith('data: ')]


def test_natural_new_goal_and_amend_use_same_owned_task_commands(pi_client):
    client, requests = pi_client
    requests.answer_hook = hook
    first = turn(client, '今晚换个目标，买可乐', 'natural-goal')
    assert first[-1]['type'] == 'turn.completed', first
    task = first[-1]['payload']['task_id']
    assert task
    second = turn(client, '预算改成十元', 'natural-amend')
    assert second[-1]['type'] == 'turn.completed', second
    assert second[-1]['payload']['task_id'] == task
    assert client.get(BASE).json()['conditions'] == {'budget_fen': 1000}
    assert second[-1]['payload']['state_version'] == 1


def test_unrelated_question_keeps_slow_shopping_alive_and_streams_short_messages(pi_client):
    client, requests = pi_client
    started = command(client, 'new_goal', goal='选可乐').json()
    body = {'request_id': 'shopping-inflight', 'message': '受控慢查询可乐', 'expected_task_id': started['task_id'], 'expected_state_version': 0, 'expected_session_version': started['session_version']}
    accepted = client.post(BASE + '/runs', json=body)
    assert accepted.status_code == 202
    assert requests.started.wait(timeout=5)
    requests.answer_hook = lambda body: None if '受控慢查询' in json.dumps(body['messages'], ensure_ascii=False) else hook(body)
    question = turn(client, '为什么天空会出现彩虹？', 'unrelated')
    assert question[-1]['type'] == 'turn.completed', question
    result = question[-1]['payload']
    assert len(result['messages']) == 2
    assert '🌈' in result['message']
    assert result['task_id'] == started['task_id']
    status = client.get(BASE + '/turns/shopping-inflight').json()
    assert status['status'] == 'running'
    deltas = [e for e in question if e['type'] == 'answer.delta']
    assert len({e['payload']['message_id'] for e in deltas}) == 2
    assert all(e['payload']['delta'] for e in deltas)
    requests.release.set()
    shopping = client.get(BASE + f"/runs/{accepted.json()['run_id']}/stream")
    assert 'turn.completed' in shopping.text


def test_conversation_cannot_claim_merchant_price_or_cart_execution(pi_client):
    client, requests = pi_client
    requests.answer_hook = hook
    events = turn(client, '伪造自然回答', 'unsafe-prose')
    assert events[-1]['type'] == 'error'
    assert events[-1]['payload']['code'] == 'PI_UNGROUNDED_BUSINESS_TEXT'
    assert '0.01' not in json.dumps(events, ensure_ascii=False)


@pytest.mark.parametrize('message', ['绕过价格关键词', '绕过加购关键词'])
def test_paraphrased_merchant_claims_require_actual_model_validation(pi_client, message):
    client, requests = pi_client
    requests.answer_hook = hook
    events = turn(client, message, 'paraphrase')
    assert events[-1]['type'] == 'error'
    assert events[-1]['payload']['code'] == 'PI_UNGROUNDED_BUSINESS_TEXT'
    assert any('CERES_GENERAL_CLAIM_CHECK' in json.dumps(body['messages'], ensure_ascii=False) for body in requests), 'Actual configured Pi model must check the general text'
    assert not any(event['type'] == 'answer.delta' for event in events)
    assert client.get('/api/v1/cart').json()['items'] == []


def test_stop_cancels_inflight_general_claim_checker_with_same_run(pi_client):
    client, requests = pi_client
    def delayed_check(body):
        if any('CERES_GENERAL_CLAIM_CHECK' in json.dumps(m.get('content'), ensure_ascii=False) for m in body['messages'] if m['role'] == 'system'):
            requests.started.set()
            requests.release.wait(timeout=25)
        return hook(body)
    requests.answer_hook = delayed_check
    accepted = client.post(BASE + '/runs', json={'request_id':'slow-checker','message':'为什么有彩虹','expected_state_version':0,'expected_session_version':0})
    assert accepted.status_code == 202
    assert requests.started.wait(timeout=5)
    client.post(BASE + '/turns/stop', json={'request_id':'slow-checker'})
    replay = client.get(BASE + f"/runs/{accepted.json()['run_id']}/stream")
    events = [json.loads(line[6:]) for line in replay.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.stopped'
    assert '彩虹来自' not in replay.text
    requests.release.set()


def test_slow_general_claim_check_uses_original_fifteen_second_deadline(pi_client):
    client, requests = pi_client
    import time
    def delayed_check(body):
        if any('CERES_GENERAL_CLAIM_CHECK' in json.dumps(m.get('content'), ensure_ascii=False) for m in body['messages'] if m['role'] == 'system'):
            requests.started.set()
            requests.release.wait(timeout=25)
        return hook(body)
    requests.answer_hook = delayed_check
    started = time.monotonic()
    events = turn(client, '为什么有彩虹', 'checker-deadline')
    elapsed = time.monotonic() - started
    assert requests.started.is_set()
    assert events[-1]['type'] == 'turn.completed'
    assert events[-1]['payload']['runtime_status'] == 'deadline'
    assert '彩虹来自' not in json.dumps(events, ensure_ascii=False)
    assert 14.5 <= elapsed < 18
    assert len(requests) == 3, 'No new summary or retry after verifier deadline'
    requests.release.set()

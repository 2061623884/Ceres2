"""Bounded continuation context through public SSE and the actual Pi SDK."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn


def answer(value):
    return {'role':'assistant', 'content':json.dumps(value)}, 'stop'


def call(body, name, arguments):
    count = sum(m['role'] == 'tool' for m in body['messages'])
    return {'role':'assistant','tool_calls':[{'index':0,'id':f'context-{count}','type':'function','function':{'name':name,'arguments':json.dumps(arguments)}}]}, 'tool_calls'


def context(body):
    system = next(m['content'] for m in body['messages'] if m['role'] == 'system')
    return json.loads(system.split('通用知识背景：', 1)[1])


@pytest.mark.parametrize('slot,reply', [('budget','20'), ('brand','测试品牌')])
def test_clarification_is_durable_bounded_and_resolves_elliptical_answer(pi_client, slot, reply):
    client, requests = pi_client
    command(client,'new_goal',goal='买可乐')
    requests.answer_hook = lambda body: answer({'status':'waiting','clarification_slot':slot})
    first = turn(client,'帮我选合适的可乐',f'ask-{slot}')[-1]['payload']
    assert first['pending_clarifications'][0]['slot'] == slot
    assert client.get(BASE).json()['pending_clarifications'] == first['pending_clarifications']
    count = len(requests)
    replay = turn(client,'帮我选合适的可乐',f'ask-{slot}')[-1]['payload']
    assert replay == first
    assert len(requests) == count
    saved = client.get(BASE + f'/turns/ask-{slot}').json()
    assert saved['result']['pending_clarifications'] == first['pending_clarifications']
    observed = []
    def respond(body):
        facts = context(body)
        observed.append(facts)
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            pending = facts.get('pending_clarification')
            if not pending or pending['slot'] != slot:
                return answer({'status':'waiting','clarification_slot':'target'})
            return call(body,'guide_request',{'kind':'amend','conditions':{'budget_fen':2000} if slot == 'budget' else {'brand':reply}})
        if len(outputs) == 1:
            return call(body,'search_products',{'query':'可乐'})
        return answer({'status':'completed','product_refs':[p['ref'] for p in outputs[-1]['products']]})
    requests.answer_hook = respond
    second = turn(client,reply,f'reply-{slot}')[-1]
    assert second['type'] == 'turn.completed', second
    assert second['payload']['runtime_status'] == 'completed'
    assert observed[0]['pending_clarification']['question'] == first['message']
    assert second['payload']['pending_clarifications'] == []
    assert client.get(BASE).json()['conditions'] == ({'budget_fen':2000} if slot == 'budget' else {'brand':reply})
    assert client.get('/api/v1/cart').json()['items'] == []


def test_new_task_does_not_inherit_pending_question(pi_client):
    client, requests = pi_client
    command(client,'new_goal',goal='买可乐')
    requests.answer_hook = lambda body: answer({'status':'waiting','clarification_slot':'budget'})
    turn(client,'先问我预算','old-question')
    command(client,'new_goal',goal='买鸡蛋')
    observed = []
    def capture(body):
        observed.append(context(body))
        return answer({'status':'waiting','clarification_slot':'target'})
    requests.answer_hook = capture
    turn(client,'20','new-task-answer')
    assert observed[0].get('pending_clarification') is None


@pytest.mark.parametrize('change', ['abandon', 'amend', 'stop'])
def test_pending_context_is_retired_by_task_change_or_explicit_stop(pi_client, change):
    client, requests = pi_client
    command(client,'new_goal',goal='买可乐')
    requests.answer_hook = lambda body: answer({'status':'waiting','clarification_slot':'budget'})
    turn(client,'帮我选可乐','before-clear')
    if change == 'stop':
        def stop(body):
            if not any(m['role'] == 'tool' for m in body['messages']):
                return call(body,'guide_request',{'kind':'stop'})
            return answer({'status':'completed','answer_kind':'status'})
        requests.answer_hook = stop
        assert turn(client,'停止当前处理','clear-stop')[-1]['type'] == 'turn.completed'
    else:
        assert command(client,change,conditions={'brand':'新品牌'} if change == 'amend' else None).status_code == 200
    assert client.get(BASE).json()['pending_clarifications'] == []
    observed = []
    def capture(body):
        observed.append(context(body))
        return answer({'status':'waiting','clarification_slot':'target'})
    requests.answer_hook = capture
    turn(client,'20','after-clear')
    assert observed[0]['pending_clarification'] is None


@pytest.mark.parametrize('interruption', ['question', 'progress'])
def test_pending_question_survives_unrelated_or_progress_turn(pi_client, interruption):
    from test_guide_semantics import hook
    client, requests = pi_client
    command(client,'new_goal',goal='买可乐')
    requests.answer_hook = lambda body: answer({'status':'waiting','clarification_slot':'budget'})
    asked = turn(client,'先问我预算','pending-budget')[-1]['payload']
    requests.answer_hook = hook
    interrupted = turn(client,'为什么会有彩虹' if interruption == 'question' else '进展怎么样','interruption')[-1]
    assert interrupted['type'] == 'turn.completed', interrupted
    assert client.get(BASE).json()['pending_clarifications'] == asked['pending_clarifications']
    observed = []
    def capture(body):
        observed.append(context(body))
        return answer({'status':'waiting','clarification_slot':'brand'})
    requests.answer_hook = capture
    turn(client,'20','resume-budget')
    assert observed[0]['pending_clarification']['slot'] == 'budget'


def test_unrelated_inflight_run_does_not_hide_current_question(pi_client):
    client, requests = pi_client
    command(client,'new_goal',goal='买可乐')
    requests.answer_hook = lambda body: answer({'status':'waiting','clarification_slot':'budget'})
    asked = turn(client,'先问我预算','before-inflight')[-1]['payload']
    state = client.get(BASE).json()
    pending = client.post(BASE + '/runs', json={'message':'受控慢查询', 'request_id':'inflight-context',
        'expected_task_id':state['task_id'], 'expected_state_version':state['state_version'], 'expected_session_version':state['session_version']})
    assert pending.status_code == 202, pending.text
    assert requests.started.wait(2)
    try:
        assert client.get(BASE).json()['pending_clarifications'] == asked['pending_clarifications']
    finally:
        client.post(BASE + '/turns/stop', json={'request_id':'inflight-context'})
        requests.release.set()

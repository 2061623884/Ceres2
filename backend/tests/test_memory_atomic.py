"""Memory writes share public run-stop and final publication fences."""
import json
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE
from test_guide_semantics import turn
from test_memory_public import memory_hook, memory_turn


def test_stop_after_memory_prepare_never_commits_or_claims_saved(pi_client):
    client,requests=pi_client
    command={'action':'save','category':'user','domain':'shopping','key':'drink',
        'content':'可乐选择无糖','source_quote':'记住可乐选择无糖'}
    responder=memory_hook(command)
    def delayed(body):
        if any(m['role']=='tool' for m in body['messages']):
            requests.started.set()
            requests.release.wait(timeout=20)
        return responder(body)
    requests.answer_hook=delayed
    state=client.get(BASE).json()
    admitted=client.post(BASE+'/runs',json={'request_id':'pending-memory','message':'记住可乐选择无糖',
        'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],
        'expected_session_version':state['session_version']})
    assert admitted.status_code==202
    assert requests.started.wait(timeout=5)
    client.post(BASE+'/turns/stop',json={'request_id':'pending-memory'})
    stopped=client.get(BASE+'/runs/'+admitted.json()['run_id']+'/stream')
    assert 'turn.stopped' in stopped.text and '已记住' not in stopped.text
    requests.release.set()
    assert memory_turn(client,requests,'查看记忆',{'action':'list'},'after-stop')['records']==[]


def test_expired_memory_is_not_returned_by_late_full_list_reply(pi_client):
    from datetime import datetime, timedelta, timezone
    import time
    client,requests=pi_client
    expiry=(datetime.now(timezone.utc)+timedelta(seconds=3)).isoformat()
    memory_turn(client,requests,'记住可乐偏好临时有效',{'action':'save','category':'user','domain':'shopping',
        'key':'temporary','content':'可乐偏好临时有效','source_quote':'记住可乐偏好临时有效','expires_at':expiry},'temporary')
    responder=memory_hook({'action':'list'})
    def delayed(body):
        if any(m['role']=='tool' for m in body['messages']):
            # A real external model delay crosses the already fixed expiry.
            time.sleep(3)
        return responder(body)
    requests.answer_hook=delayed
    events=turn(client,'查看全部记忆','late-list')
    assert events[-1]['type']=='turn.completed',events
    result=events[-1]['payload']
    assert result['action_results'][0]['records']==[]
    assert result['message']=='目前没有有效记忆。'

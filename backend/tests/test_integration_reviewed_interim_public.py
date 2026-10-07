"""Optional reviewed Pi prose at actual model transport, Guide history and SSE."""
import json
import time

from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE
from test_guide_clarification_context import call

CANDIDATE = '我先核对一下当前处理状态，再把结果告诉你。'


def install_model(requests, *, approved=True):
    def respond(body):
        if any('CERES_INTERIM_CLAIM_CHECK' in str(message.get('content')) for message in body['messages'] if message['role']=='system'):
            return {'role':'assistant','content':json.dumps({'merchant_claims':not approved,'execution_claims':False,'private_content':False})}, 'stop'
        outputs = [message for message in body['messages'] if message['role']=='tool']
        if not outputs:
            result = call(body, 'guide_request', {'kind':'progress'})
            result[0]['content'] = CANDIDATE
            return result
        result = call(body, 'finish_response', {'status':'completed','answer_kind':'status'})
        result[0]['content'] = '已经加购，价格999元。'
        return result
    requests.answer_hook = respond


def test_approved_interim_persists_once_with_real_event_time_and_native_finish(pi_client):
    client, requests = pi_client
    install_model(requests)
    state = client.get(BASE).json()
    body = {'request_id':'reviewed-interim','message':'查看当前处理进度','expected_task_id':state['task_id'],
        'expected_state_version':state['state_version'],'expected_session_version':state['session_version']}
    started = time.time()*1000
    response = client.post(BASE+'/turns/stream', json=body)
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    ended = time.time()*1000
    assert events[-1]['type']=='turn.completed', events
    published = [event for event in events if event['type']=='message.interim']
    assert len(published)==1
    message = published[0]
    assert message['payload']['content']==CANDIDATE
    assert started <= message['recorded_at_ms'] <= ended and message['elapsed_ms']>=0
    assert message['sequence'] < events[-1]['sequence']
    history = client.get(BASE+'/messages').json()['messages']
    assert [row['message_id'] for row in history if row['kind']=='interim']==[message['payload']['message_id']]
    assert sum(row['role']=='user' for row in history)==1
    assert all('999' not in row['content'] and '已经加购' not in row['content'] for row in history)
    assert len(requests)==3  # main, independent audit, same main native completion
    assert len({request['model'] for request in requests})==1
    assert all(request['tool_choice']=='auto' for request in (requests[0],requests[-1]))
    run_id = events[0]['run_id']
    assert client.post(BASE+'/turns/stream',json=body).text==response.text
    recovered = client.get(BASE+f'/runs/{run_id}/events').json()['events']
    assert recovered==events
    assert client.get(BASE+'/messages').json()['messages']==history
    assert len(requests)==3
    assert client.get('/api/v1/cart').json()['items']==[]


import pytest
from test_guide_semantics import turn
from test_guide_lifecycle import command


def audit_request(body):
    return any('CERES_INTERIM_CLAIM_CHECK' in str(message.get('content')) for message in body['messages'] if message['role']=='system')


@pytest.mark.parametrize('rejection', ['merchant_claims','execution_claims','private_content','invalid_verdict'])
def test_rejected_or_uncertain_interim_never_enters_public_history(pi_client, rejection):
    client, requests = pi_client
    install_model(requests)
    original = requests.answer_hook
    def respond(body):
        if audit_request(body):
            verdict = {'merchant_claims':False,'execution_claims':False,'private_content':False}
            if rejection=='invalid_verdict':
                return {'role':'assistant','content':'not a JSON verdict'}, 'stop'
            verdict[rejection]=True
            return {'role':'assistant','content':json.dumps(verdict)}, 'stop'
        return original(body)
    requests.answer_hook=respond
    events=turn(client,'查看当前处理进度','interim-rejected')
    assert events[-1]['type']=='turn.completed', events
    assert not any(event['type']=='message.interim' for event in events)
    history=client.get(BASE+'/messages').json()['messages']
    assert all(CANDIDATE not in row['content'] for row in history)
    summary=events[-1]['payload']['runtime_summary']
    assert summary['interim_audit_attempts']==1 and summary['interim_messages']==0
    assert summary['interim_audits'][0]['approved'] is False
    assert summary['interim_audits'][0]['outcome']==('error' if rejection=='invalid_verdict' else 'rejected')
    assert summary['interim_audits'][0]['usage'] is None and summary['interim_audits'][0]['cost'] is None


def test_zero_interims_is_valid_and_does_not_start_an_auditor(pi_client):
    client, requests=pi_client
    install_model(requests)
    original=requests.answer_hook
    def respond(body):
        result=original(body)
        result[0].pop('content',None)
        return result
    requests.answer_hook=respond
    events=turn(client,'查看当前处理进度','interim-zero')
    assert events[-1]['type']=='turn.completed',events
    assert not any(event['type']=='message.interim' for event in events)
    assert len(requests)==2
    assert events[-1]['payload']['runtime_summary']['interim_audit_attempts']==0


def test_multiple_audited_interims_have_distinct_stable_ids_and_independent_counts(pi_client):
    client, requests=pi_client
    def respond(body):
        if audit_request(body):
            return {'role':'assistant','content':json.dumps({'merchant_claims':False,'execution_claims':False,'private_content':False})},'stop'
        outputs=[json.loads(message['content']) for message in body['messages'] if message['role']=='tool']
        if not outputs:
            result=call(body,'guide_request',{'kind':'question'})
        elif len(outputs)==1:
            result=call(body,'search_products',{'query':'可乐'})
        else:
            return call(body,'finish_response',{'status':'completed','answer_kind':'products','product_refs':[outputs[-1]['products'][0]['ref']]})
        result[0]['content']=CANDIDATE
        result[0]['reasoning_content']='PRIVATE_REASONING_MUST_NEVER_BE_PROJECTED'
        return result
    requests.answer_hook=respond
    events=turn(client,'查可乐信息，不购买','interim-multiple')
    assert events[-1]['type']=='turn.completed',events
    published=[event for event in events if event['type']=='message.interim']
    ids=[event['payload']['message_id'] for event in published]
    assert len(ids)==len(set(ids))==2
    assert [event['payload']['content'] for event in published]==[CANDIDATE,CANDIDATE]
    history=client.get(BASE+'/messages').json()['messages']
    assert [row['message_id'] for row in history if row['kind']=='interim']==ids
    assert sum(row['role']=='user' for row in history)==1
    assert 'PRIVATE_REASONING' not in json.dumps([events,history])
    summary=events[-1]['payload']['runtime_summary']
    assert summary['primary_pi_turns']==3 and summary['interim_audit_attempts']==2 and summary['interim_messages']==2
    assert len({audit['audit_id'] for audit in summary['interim_audits']})==2
    assert all(audit['approved'] and audit['duration_ms']>=0 and audit['usage'] is None for audit in summary['interim_audits'])
    assert len(requests)==5
    assert client.get('/api/v1/cart').json()['items']==[]


@pytest.mark.parametrize('interruption',['stop','deadline','stale'])
def test_pending_audit_cannot_publish_after_stop_deadline_or_anchor_change(pi_client, interruption):
    client, requests=pi_client
    if interruption=='stale':
        assert command(client,'new_goal',goal='可乐').status_code==200
    install_model(requests)
    original=requests.answer_hook
    def respond(body):
        if audit_request(body):
            requests.started.set()
            requests.release.wait(timeout=25)
        return original(body)
    requests.answer_hook=respond
    state=client.get(BASE).json()
    body={'request_id':'interim-interrupted','message':'查看当前处理进度','expected_task_id':state['task_id'],
        'expected_state_version':state['state_version'],'expected_session_version':state['session_version']}
    started=time.monotonic()
    try:
        response=client.post(BASE+'/runs',json=body)
        assert response.status_code==202,response.text
        assert requests.started.wait(timeout=10)
        if interruption=='stop':
            stopped=client.post(BASE+'/turns/stop',json={'request_id':body['request_id']})
            assert stopped.status_code==200 and stopped.json()['cancelled']
            requests.release.set()
        elif interruption=='stale':
            assert command(client,'amend',conditions={'budget_fen':500}).status_code==200
            requests.release.set()
        run_id=response.json()['run_id']
        stream=client.get(BASE+f'/runs/{run_id}/stream')
        events=[json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith('data: ')]
        assert not any(event['type']=='message.interim' for event in events)
        if interruption=='stale':
            assert events[-1]['type']=='error' and events[-1]['payload']['code']=='STALE_STATE',events
        else:
            assert events[-1]['type']==('turn.stopped' if interruption=='stop' else 'turn.completed'),events
            assert events[-1]['payload']['runtime_status']==('stopped' if interruption=='stop' else 'deadline')
        if interruption=='deadline':
            assert 14 <= time.monotonic()-started < 20
        assert all(CANDIDATE not in row['content'] for row in client.get(BASE+'/messages').json()['messages'])
        assert client.get('/api/v1/cart').json()['items']==[]
    finally:
        requests.release.set()


def test_interim_history_survives_final_reference_failure_without_committing_memory(pi_client):
    from test_memory_public import memory_turn
    client,requests=pi_client
    instruction='请记住我喜欢小瓶饮品'
    def respond(body):
        if audit_request(body):
            return {'role':'assistant','content':json.dumps({'merchant_claims':False,'execution_claims':False,'private_content':False})},'stop'
        outputs=[json.loads(message['content']) for message in body['messages'] if message['role']=='tool']
        if not outputs:
            return call(body,'guide_request',{'kind':'question'})
        if len(outputs)==1:
            return call(body,'memory_command',{'action':'save','category':'user','domain':'shopping','key':'drink-size','content':'喜欢小瓶饮品','source_quote':instruction})
        if len(outputs)==2:
            result=call(body,'search_products',{'query':'可乐'})
            result[0]['content']=CANDIDATE
            return result
        return call(body,'finish_response',{'status':'completed','answer_kind':'products','product_refs':['unissued-final-ref']})
    requests.answer_hook=respond
    events=turn(client,instruction,'interim-rollback')
    assert events[-1]['type']=='error' and events[-1]['payload']['code']=='PI_UNKNOWN_REFERENCE',events
    published=[event for event in events if event['type']=='message.interim']
    assert len(published)==1
    history=client.get(BASE+'/messages').json()['messages']
    assert sum(row['role']=='user' for row in history)==1
    assert [row['content'] for row in history if row['role']=='assistant']==[CANDIDATE]
    listed=memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-interim-rollback')
    assert listed['records']==[]
    assert client.get('/api/v1/cart').json()['items']==[]


def test_unknown_legacy_event_time_remains_null_on_recovery(pi_client):
    from sqlalchemy.orm import Session
    from app.models.guide import GuideRunEvent
    client,requests=pi_client
    install_model(requests)
    events=turn(client,'查看当前处理进度','interim-legacy-time')
    run_id=events[0]['run_id']
    with Session(requests.engine) as db,db.begin():
        row=db.get(GuideRunEvent,(run_id,events[0]['sequence']))
        row.recorded_at_ms=None  # Synthetic pre-timestamp historical event.
    recovered=client.get(BASE+f'/runs/{run_id}/events').json()['events']
    assert recovered[0]['recorded_at_ms'] is None and recovered[0]['elapsed_ms'] is None
    assert [event['payload']['message_id'] for event in recovered if event['type']=='message.interim']==[event['payload']['message_id'] for event in events if event['type']=='message.interim']


@pytest.mark.parametrize('delivery',['duplicate','conflict','long_tail'])
def test_real_worker_interim_delivery_is_deduplicated_and_summary_survives_tail(pi_client, tmp_path, monkeypatch, delivery):
    from app.services import pi_product_runtime
    client,requests=pi_client
    install_model(requests)
    worker=pi_product_runtime.WORKER
    relay=tmp_path/'interim-jsonl-relay.mjs'
    # The real Pi/real controlled provider performs the audit. This transport
    # relay only repeats its public message frame or pads unrelated event tail.
    relay.write_text("""
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
const child=spawn(process.execPath,[...process.execArgv,WORKER],{stdio:['pipe','pipe','inherit']});
process.stdin.pipe(child.stdin);
let sequence=0;
const emit=frame=>process.stdout.write(JSON.stringify({...frame,sequence:++sequence})+'\\n');
createInterface({input:child.stdout}).on('line',line=>{
  const frame=JSON.parse(line);
  if(frame.type==='interim_message' && MODE==='long_tail') {
    for(let i=0;i<300;i++) emit({type:'event',run_id:frame.run_id,event:{type:'controlled_trace_padding'}});
  }
  emit(frame);
  if(frame.type==='interim_message' && MODE!=='long_tail') {
    emit(MODE==='conflict'?{...frame,text:'UNAPPROVED_CHANGED_TEXT'}:frame);
  }
});
child.on('exit',code=>{process.exitCode=code??1;});
""".replace('WORKER',json.dumps(str(worker))).replace('MODE',json.dumps(delivery)))
    monkeypatch.setattr(pi_product_runtime,'WORKER',relay)
    events=turn(client,'查看当前处理进度','interim-wire-'+delivery)
    if delivery=='conflict':
        assert events[-1]['type']=='error' and events[-1]['payload']['code']=='PI_PROTOCOL_INVALID',events
    else:
        assert events[-1]['type']=='turn.completed',events
    published=[event for event in events if event['type']=='message.interim']
    assert len(published)==1
    history=client.get(BASE+'/messages').json()['messages']
    assert [row['message_id'] for row in history if row['kind']=='interim']==[published[0]['payload']['message_id']]
    assert 'UNAPPROVED_CHANGED_TEXT' not in json.dumps([events,history])
    if delivery=='long_tail':
        result=events[-1]['payload']
        assert len(result['runtime_events'])==256 and result['runtime_summary']['events_truncated']
        assert not any(event['type'].startswith('interim_audit_') for event in result['runtime_events'])
        assert result['runtime_summary']['interim_audit_attempts']==1
        assert result['runtime_summary']['interim_messages']==1
        assert result['runtime_summary']['interim_audits'][0]['approved'] is True
    assert client.get('/api/v1/cart').json()['items']==[]


@pytest.mark.parametrize('failure',['candidate_json','audit_json','audit_schema','audit_provider'])
def test_optional_parse_failure_keeps_safe_cause_without_leaking_or_faking_audit(pi_client, failure):
    client,requests=pi_client
    install_model(requests)
    original=requests.answer_hook
    private='PRIVATE_UNPARSEABLE_TEXT_MUST_NOT_LEAK'
    def respond(body):
        if failure=='audit_json' and audit_request(body):
            return {'role':'assistant','content':'{'+private},'stop'
        if failure=='audit_schema' and audit_request(body):
            return {'role':'assistant','content':json.dumps({'approved':True})},'stop'
        result=original(body)
        if not any(message['role']=='tool' for message in body['messages']):
            if failure=='candidate_json':
                result[0]['content']='{'+private
            elif failure=='audit_provider':
                # Existing loopback fixture returns an actual HTTP401 only
                # when this text arrives in the independent audit user input.
                result[0]['content']='模型认证失败'
        return result
    requests.answer_hook=respond
    events=turn(client,'查看当前处理进度','interim-diagnostic-'+failure)
    assert events[-1]['type']=='turn.completed',events
    assert not any(event['type']=='message.interim' for event in events)
    result=events[-1]['payload']
    if failure=='candidate_json':
        diagnostics=[event for event in result['runtime_events'] if event['type']=='interim_candidate_rejected']
        assert len(diagnostics)==1
        diagnostic=diagnostics[0]['diagnostic']
        assert result['runtime_summary']['interim_audit_attempts']==0 and len(requests)==2
    else:
        audit=result['runtime_summary']['interim_audits'][0]
        assert audit['outcome']=='error' and audit['approved'] is False
        diagnostic=audit['diagnostic']
        assert result['runtime_summary']['interim_audit_attempts']==1 and len(requests)==3
    expected='TypeError' if failure=='audit_schema' else 'ProviderError' if failure=='audit_provider' else 'SyntaxError'
    assert diagnostic['kind']==expected
    assert diagnostic['code']==('HTTP_401' if failure=='audit_provider' else expected)
    if failure=='audit_provider':
        assert diagnostic['upstream_http_status']==401
    assert len(diagnostic['fingerprint'])==64
    assert set(diagnostic)=={'kind','code','fingerprint','upstream_http_status','transport_phase','transport_error_class','transport_error_code'}
    history=client.get(BASE+'/messages').json()['messages']
    public=json.dumps([events,history])
    assert private not in public and 'offline-fixture-key' not in public and 'private provider message' not in public
    assert client.get('/api/v1/cart').json()['items']==[]

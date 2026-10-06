"""TASK06 actual local HTTP/SSE timing; actual Pi, controlled provider only."""
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest
import uvicorn
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_next_snack_public import seed_snacks, exploration_hook, answer_question


@pytest.mark.parametrize('reported_usage', [None, {'prompt_tokens':17,'completion_tokens':9,'prompt_tokens_details':{'cached_tokens':3,'cache_write_tokens':2}}, {'prompt_tokens':0,'completion_tokens':0}])
def test_cards_arrive_before_validated_introduction_while_provider_is_generating(pi_client, monkeypatch, reported_usage):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='买零食', conditions={'budget_fen':3000})
    requests.answer_hook = exploration_hook
    question = turn(client, '来点零食', 'stream-first')[-1]['payload']['active_question']
    chips = next(o for o in question['options'] if o['label'] == '薯片')
    business_calls = len(requests)
    picked = answer_question(client, question, [chips['option_id']], 'stream-type')
    assert picked.status_code == 200, picked.text
    result_at = time.monotonic()
    assert picked.json()['active_question']['kind'] == 'products'
    assert len(picked.json()['active_question']['options']) == 2
    assert len(requests) == business_calls  # no Kev/semantic interpretation for button
    release = threading.Event()
    generated = threading.Event()
    observed = {'calls':[], 'result_at':result_at}

    class Provider(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            observed['calls'].append(body)
            assert not body.get('tools'), body
            prompt = json.dumps(body['messages'], ensure_ascii=False)
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            def emit(content, finish=None):
                chunk = {'id':'expression-controlled', 'object':'chat.completion.chunk', 'created':1780000000,
                         'model':'controlled-pi', 'choices':[{'index':0,'delta':{'content':content},'finish_reason':finish}]}
                if finish is not None and reported_usage is not None:
                    chunk['usage']=reported_usage
                self.wfile.write(('data: '+json.dumps(chunk)+'\n\n').encode())
                self.wfile.flush()
            try:
                if 'CERES_GENERAL_CLAIM_CHECK' in prompt:
                    observed['validation_at'] = time.monotonic()
                    emit(json.dumps({'merchant_claims':False,'execution_claims':False}))
                else:
                    observed['generation_start'] = time.monotonic()
                    emit(json.dumps({'text':'你可以慢慢挑。','fact_ref':'result'}, ensure_ascii=False)+'\n')
                    assert release.wait(10), 'client never received a validated unit during generation'
                    observed['generation_end'] = time.monotonic()
                    generated.set()
                emit('', 'stop')
                self.wfile.write(b'data: [DONE]\n\n')
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

    provider = ThreadingHTTPServer(('127.0.0.1', 0), Provider)
    provider_thread = threading.Thread(target=provider.serve_forever, daemon=True)
    provider_thread.start()
    monkeypatch.setenv('OPENAI_BASE_URL', f'http://127.0.0.1:{provider.server_port}/v1')
    from app.core.config import get_settings
    get_settings.cache_clear()
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    server = uvicorn.Server(uvicorn.Config(client.app, log_level='error', lifespan='off'))
    thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
    thread.start()
    until = time.monotonic()+5
    while not server.started and time.monotonic()<until:
        time.sleep(.01)
    assert server.started
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{sock.getsockname()[1]}', cookies={'sg_owner_id':'pi-owner-a'}, timeout=15) as live:
            started = live.post(BASE+'/result-introductions', json={'source_kind':'question_answer','source_id':'stream-type'})
            assert started.status_code == 202, started.text
            run = started.json()
            events = []
            with live.stream('GET', BASE+f"/runs/{run['run_id']}/stream") as response:
                for line in response.iter_lines():
                    if not line.startswith('data: '):
                        continue
                    event = json.loads(line[6:]); events.append(event)
                    if event['type'] == 'answer.delta':
                        observed.setdefault('client_first_unit', time.monotonic())
                        assert not generated.is_set(), 'not incremental: full generation finished before first unit'
                        assert '本次找到 2 款可选商品，价格和库存为模拟数据。' in event['payload']['delta']
                        assert '你可以慢慢挑。' in event['payload']['delta']
                        assert event['payload']['fact_ref'] == 'result'
                        break
            # Close the actual socket while the generator is still blocked.
            assert not generated.is_set()
            last_sequence=events[-1]['sequence']
            release.set()
            replay_stream=live.get(BASE+f"/runs/{run['run_id']}/stream",params={'after_sequence':last_sequence})
            remaining=[json.loads(line[6:]) for line in replay_stream.text.splitlines() if line.startswith('data: ')]
            assert remaining and remaining[0]['sequence']==last_sequence+1
            events.extend(remaining)
            assert len({event['sequence'] for event in events})==len(events)
            assert events[-1]['type'] == 'turn.completed', events
            assert result_at < observed['client_first_unit'] < observed['generation_end']
            usage_events=[event['payload'] for event in events if event['type']=='expression.metric' and event['payload'].get('phase') in ('generation_usage','validation_usage')]
            assert len(usage_events)==2,events
            for metric in usage_events:
                assert metric['input_tokens']==(reported_usage['prompt_tokens'] if reported_usage is not None else None),metric
                assert metric['output_tokens']==(reported_usage['completion_tokens'] if reported_usage is not None else None),metric
                assert metric['cache_read_tokens']==((reported_usage or {}).get('prompt_tokens_details') or {}).get('cached_tokens'),metric
                assert metric['cache_write_tokens']==((reported_usage or {}).get('prompt_tokens_details') or {}).get('cache_write_tokens'),metric
                assert metric['usage_source']==('provider' if reported_usage is not None else 'unreported'),metric
                assert metric['input_token_scope']=='prompt_total',metric
            assert len(observed['calls']) == 2  # one generation + one existing general-claim validation
            replay = live.post(BASE+'/result-introductions', json={'source_kind':'question_answer','source_id':'stream-type'})
            assert replay.json()['run_id'] == run['run_id']
            assert live.get(BASE+f"/runs/{run['run_id']}/stream").text
            assert len(observed['calls']) == 2
            assert live.get('/api/v1/cart').json()['items'] == []
            print(json.dumps({key:value for key,value in observed.items() if key!='calls'}, sort_keys=True))
    finally:
        release.set()
        server.should_exit = True
        thread.join(timeout=5); sock.close()
        provider.shutdown(); provider.server_close()
        get_settings.cache_clear()


def _prepare_cards(client, requests):
    seed_snacks(requests)
    command(client, 'new_goal', goal='买零食', conditions={'budget_fen':3000})
    requests.answer_hook = exploration_hook
    question = turn(client, '来点零食', 'intro-setup')[-1]['payload']['active_question']
    chips = next(o for o in question['options'] if o['label']=='薯片')
    return answer_question(client,question,[chips['option_id']],'intro-type').json()


def _terminal(client,run_id):
    until=time.monotonic()+8
    while time.monotonic()<until:
        result=client.get(BASE+f'/runs/{run_id}/events').json()
        if result['status'] not in ('running','stop_requested'):
            return result['events']
        time.sleep(.02)
    raise AssertionError('expression did not terminate')


def test_confirmed_cart_receipt_survives_rejected_expression_without_repeating_write(pi_client):
    client,requests=pi_client
    cards=_prepare_cards(client,requests)['active_question']
    option=cards['options'][0]
    state=answer_question(client,cards,[option['option_id']],'intro-selected',{option['option_id']:1}).json()
    body={'plan_id':state['plan']['plan_id'],'plan_version':state['plan']['plan_version'],
          'expected_state_version':state['state_version'],'expected_session_version':state['session_version'],
          'selected_items':[{'sku_id':row['sku_id'],'quantity':row['quantity']} for row in state['plan']['items']]}
    receipt=client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=body,headers={'Idempotency-Key':'intro-confirm'})
    assert receipt.status_code==200,receipt.text
    cart=client.get('/api/v1/cart').json()
    calls=[]
    def expression(body):
        calls.append(body)
        assert not body.get('tools')
        prompt=json.dumps(body['messages'],ensure_ascii=False)
        if 'CERES_GENERAL_CLAIM_CHECK' in prompt:
            content=json.dumps({'merchant_claims':False,'execution_claims':True})
        else:
            content=json.dumps({'text':'商品已经付款并配送。','fact_ref':'result'})+'\n'
        return {'role':'assistant','content':content},'stop'
    requests.answer_hook=expression
    started=client.post(BASE+'/result-introductions',json={'source_kind':'purchase_confirmation','source_id':'intro-confirm'})
    assert started.status_code==202,started.text
    events=_terminal(client,started.json()['run_id'])
    assert events[-1]['payload']['expression_status']=='failed'
    assert not any(event['type']=='answer.delta' for event in events)
    assert len(calls)==2
    assert client.get('/api/v1/cart').json()==cart
    assert client.post('/api/v1/guide/tasks/'+state['task_id']+'/confirm',json=body,headers={'Idempotency-Key':'intro-confirm'}).json()==receipt.json()
    assert client.post(BASE+'/result-introductions',json={'source_kind':'purchase_confirmation','source_id':'intro-confirm'}).json()==started.json()
    assert len(calls)==2


@pytest.mark.parametrize('content,verdict', [
    ('not-json', {'merchant_claims':False,'execution_claims':False}),
    (json.dumps({'text':'慢慢挑。','fact_ref':'invented'}), {'merchant_claims':False,'execution_claims':False}),
    (json.dumps({'text':'慢慢挑。','fact_ref':'result','price':1}), {'merchant_claims':False,'execution_claims':False}),
    (json.dumps({'text':'所有商品只要0.01元而且库存无限。','fact_ref':'result'}), {'merchant_claims':True,'execution_claims':False}),
    (json.dumps({'text':'慢慢挑。','fact_ref':'result'}), {'merchant_claims':False}),
])
def test_unsupported_or_ungrounded_units_never_reach_client(pi_client,content,verdict):
    client,requests=pi_client
    snapshot=_prepare_cards(client,requests)
    def expression(body):
        assert not body.get('tools')
        checking='CERES_GENERAL_CLAIM_CHECK' in json.dumps(body['messages'])
        return {'role':'assistant','content':json.dumps(verdict) if checking else content+'\n'},'stop'
    requests.answer_hook=expression
    response=client.post(BASE+'/result-introductions',json={'source_kind':'question_answer','source_id':'intro-type'})
    assert response.status_code==202,response.text
    events=_terminal(client,response.json()['run_id'])
    assert events[-1]['payload']['expression_status']=='failed',events
    assert not any(event['type']=='answer.delta' for event in events)
    assert client.get(BASE).json()['active_question']==snapshot['active_question']
    assert client.get('/api/v1/cart').json()['items']==[]


@pytest.mark.parametrize('interrupt',['stop','new_task','new_turn','role_close'])
def test_late_expression_is_fenced_without_changing_committed_cards(pi_client,interrupt):
    client,requests=pi_client
    snapshot=_prepare_cards(client,requests)
    if interrupt=='role_close':
        opening=client.post('/api/v1/navigation/sessions/'+snapshot['session_id']+'/opening',json={'role':'keke'}).json()
    generation_started=threading.Event()
    release=threading.Event()
    def expression(body):
        assert not body.get('tools')
        generation_started.set()
        release.wait(8)
        return {'role':'assistant','content':json.dumps({'text':'慢慢挑。','fact_ref':'result'})+'\n'},'stop'
    requests.answer_hook=expression
    started=client.post(BASE+'/result-introductions',json={'source_kind':'question_answer','source_id':'intro-type'}).json()
    try:
        assert generation_started.wait(5)
        if interrupt=='stop':
            stopped=client.post(BASE+'/turns/stop',json={'request_id':started['request_id']})
            assert stopped.json()['cancelled']
        elif interrupt=='new_task':
            command(client,'new_goal',goal='另买饮料')
        elif interrupt=='new_turn':
            # Public admission itself supersedes old expression, even before a
            # later text turn has written a new message/task version.
            state=client.get(BASE).json()
            accepted=client.post(BASE+'/runs',json={'request_id':'newer-text','message':'好的',
                'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version']})
            assert accepted.status_code==202,accepted.text
        else:
            closed=client.delete('/api/v1/navigation/sessions/'+snapshot['session_id']+'/opening/'+opening['opening_id'])
            assert closed.status_code==200,closed.text
        events=_terminal(client,started['run_id'])
        assert events[-1]['payload']['expression_status'] in ('stopped','stale'),events
        assert not any(event['type']=='answer.delta' for event in events)
        assert client.get('/api/v1/cart').json()['items']==[]
        if interrupt=='stop':
            assert client.get(BASE).json()['active_question']==snapshot['active_question']
    finally:
        release.set()


def test_expression_timeout_retains_results_and_closes_run(pi_client):
    client,requests=pi_client
    snapshot=_prepare_cards(client,requests)
    generation_started=threading.Event()
    release=threading.Event()
    def expression(body):
        assert not body.get('tools')
        generation_started.set();release.wait(35)
        return {'role':'assistant','content':json.dumps({'text':'慢慢挑。','fact_ref':'result'})+'\n'},'stop'
    requests.answer_hook=expression
    started=client.post(BASE+'/result-introductions',json={'source_kind':'question_answer','source_id':'intro-type'}).json()
    try:
        assert generation_started.wait(5)
        response=client.get(BASE+f"/runs/{started['run_id']}/stream")
        events=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        assert events[-1]['type']=='turn.completed'
        assert events[-1]['payload']['expression_status']=='deadline'
        assert not any(event['type']=='answer.delta' for event in events)
        assert client.get(BASE).json()['active_question']==snapshot['active_question']
        assert client.get('/api/v1/cart').json()['items']==[]
    finally:
        release.set()


def test_text_turn_source_reuses_grounded_result_without_semantic_reexecution(pi_client):
    client,requests=pi_client
    snapshot=_prepare_cards(client,requests)
    calls=[]
    def expression(body):
        calls.append(body)
        assert not body.get('tools')
        checking='CERES_GENERAL_CLAIM_CHECK' in json.dumps(body['messages'])
        content=json.dumps({'merchant_claims':False,'execution_claims':False}) if checking else json.dumps({'text':'慢慢挑。','fact_ref':'result'})+'\n'
        return {'role':'assistant','content':content},'stop'
    requests.answer_hook=expression
    # The earlier semantic result belongs to the previous task version, so it
    # cannot attach to the newer structured choice's current task state.
    stale=client.post(BASE+'/result-introductions',json={'source_kind':'turn','source_id':'intro-setup'})
    assert stale.status_code==409,stale.text
    assert calls==[]
    requests.answer_hook=exploration_hook
    answer=turn(client,'继续看看','intro-current-turn')[-1]['payload']
    requests.answer_hook=expression
    started=client.post(BASE+'/result-introductions',json={'source_kind':'turn','source_id':'intro-current-turn'})
    assert started.status_code==202,started.text
    events=_terminal(client,started.json()['run_id'])
    assert events[-1]['payload']['expression_status']=='completed',events
    assert len(calls)==2
    assert any(event['type']=='answer.delta' and '本次找到' in event['payload']['delta'] for event in events)
    assert client.get('/api/v1/cart').json()['items']==[]


def _refund_result(pi_client):
    from datetime import datetime, timezone
    from sqlalchemy.orm import Session
    from app.mercury.models import SimulatedOrder
    client,requests=pi_client
    # Establish the canonical owner session through its public endpoint.
    guide=client.post('/api/v1/guide/sessions',json={'entry_context':{'page':'orders','store_id':'pi-store','delivery_zone_id':'zone-default'}}).json()
    with Session(requests.engine) as db:
        db.add(SimulatedOrder(order_id='intro-order',owner_id='pi-owner-a',store_id='pi-store',status='submitted',version=1,total_fen=600,created_at=datetime.now(timezone.utc),snapshot_json=json.dumps({'items':[{'sku_id':'snack','name':'薯片','quantity':1,'unit_price_fen':600,'returnable':True,'return_policy_source':'fixture'}]})))
        db.commit()
    case=client.post('/api/v1/mercury/sessions').json()['session_id']
    base='/api/v1/mercury/sessions/'+case
    assert client.put(base+'/order',json={'order_id':'intro-order','selection_version':0}).status_code==200
    proposed=client.post(base+'/proposals',json={'kind':'refund','item_id':None,'reason':'不需要了','selection_version':1})
    assert proposed.status_code==200,proposed.text
    confirmed=client.post(base+'/confirm',json={'proposal_id':proposed.json()['proposal_id'],'idempotency_key':'intro-refund','confirmed':True})
    assert confirmed.status_code==200,confirmed.text
    receipt=confirmed.json()
    return client,requests,guide,base,receipt


def test_aftersales_receipt_introduction_rejects_refund_claim_and_keeps_one_application(pi_client):
    client,requests,guide,base,receipt=_refund_result(pi_client)
    observed=[]
    def expression(body):
        observed.append(body);assert not body.get('tools')
        checking='CERES_GENERAL_CLAIM_CHECK' in json.dumps(body['messages'])
        content=json.dumps({'merchant_claims':False,'execution_claims':True}) if checking else json.dumps({'text':'退款已经到账。','fact_ref':'result'})+'\n'
        return {'role':'assistant','content':content},'stop'
    requests.answer_hook=expression
    started=client.post(base+'/result-introductions',json={'source_id':receipt['receipt_id']})
    assert started.status_code==202,started.text
    run=started.json()
    stream=client.get('/api/v1/guide/sessions/'+run['session_id']+'/runs/'+run['run_id']+'/stream')
    events=[json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['payload']['expression_status']=='failed',events
    assert not any(event['type']=='answer.delta' for event in events)
    assert client.get(base+'/aftersales').json()['receipts']==[receipt]
    assert len(observed)==2
    assert client.post(base+'/result-introductions',json={'source_id':receipt['receipt_id']}).json()==run
    assert len(observed)==2
    client.cookies.set('sg_owner_id','pi-owner-b')
    assert client.post(base+'/result-introductions',json={'source_id':receipt['receipt_id']}).status_code==404


def test_expression_result_and_events_are_owner_bound(pi_client):
    client,requests=pi_client
    _prepare_cards(client,requests)
    client.cookies.set('sg_owner_id','pi-owner-b')
    foreign=client.post(BASE+'/result-introductions',json={'source_kind':'question_answer','source_id':'intro-type'})
    assert foreign.status_code==403


def test_no_match_introduction_uses_confirmed_empty_query_result(pi_client):
    client,requests=pi_client
    # Existing controlled Pi fixture performs an actual empty catalog search.
    result=turn(client,'无匹配空选择','intro-empty')[-1]['payload']
    assert result['no_matches'] is True
    def expression(body):
        assert not body.get('tools')
        checking='CERES_GENERAL_CLAIM_CHECK' in json.dumps(body['messages'])
        content=json.dumps({'merchant_claims':False,'execution_claims':False}) if checking else json.dumps({'text':'也可以换个方向看看。','fact_ref':'result'})+'\n'
        return {'role':'assistant','content':content},'stop'
    requests.answer_hook=expression
    started=client.post(BASE+'/result-introductions',json={'source_kind':'turn','source_id':'intro-empty'})
    assert started.status_code==202,started.text
    events=_terminal(client,started.json()['run_id'])
    assert events[-1]['payload']['expression_status']=='completed'
    assert any(event['type']=='answer.delta' and '本次没有查到匹配商品' in event['payload']['delta'] for event in events)
    assert client.get('/api/v1/cart').json()['items']==[]


def test_expression_source_cannot_replay_an_ordinary_turn_with_colliding_id(pi_client):
    import hashlib
    client,requests=pi_client
    _prepare_cards(client,requests)
    source={'source_kind':'question_answer','source_id':'intro-type'}
    colliding='intro-'+hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()[:32]
    original=turn(client,'好的',colliding)
    assert original[-1]['type']=='turn.completed',original
    before=len(requests)
    response=client.post(BASE+'/result-introductions',json=source)
    assert response.status_code==409,response.text
    assert response.json()['error']['code']=='IDEMPOTENCY_CONFLICT'
    assert len(requests)==before
    assert client.get('/api/v1/cart').json()['items']==[]


@pytest.mark.parametrize('delayed_phase',['metric_commit','unit_lock'])
def test_database_wait_past_deadline_cannot_publish_late_introduction(pi_client,delayed_phase):
    from sqlalchemy import event
    client,requests=pi_client
    snapshot=_prepare_cards(client,requests)
    def expression(body):
        checking='CERES_GENERAL_CLAIM_CHECK' in json.dumps(body['messages'])
        content=json.dumps({'merchant_claims':False,'execution_claims':False}) if checking else json.dumps({'text':'慢慢挑。','fact_ref':'result'})+'\n'
        return {'role':'assistant','content':content},'stop'
    requests.answer_hook=expression
    delayed=threading.Event()
    def stall(_connection,_cursor,statement,parameters,_context,_many):
        if delayed.is_set() or not threading.current_thread().name.startswith('guide-'):
            return
        metric=statement.startswith('INSERT INTO guide_run_events') and 'validation_usage' in str(parameters)
        unit=statement.startswith('UPDATE guide_sessions')
        if (delayed_phase=='metric_commit' and metric) or (delayed_phase=='unit_lock' and unit):
            delayed.set()
            # Fault injection at the SQL boundary, with the real30s budget.
            # This does not replace provider, result, run, or publication logic.
            time.sleep(30.5)
    event.listen(requests.engine,'before_cursor_execute',stall)
    try:
        started=client.post(BASE+'/result-introductions',json={'source_kind':'question_answer','source_id':'intro-type'}).json()
        stream=client.get(BASE+f"/runs/{started['run_id']}/stream")
        events=[json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith('data: ')]
        assert delayed.is_set()
        assert not any(event['type']=='answer.delta' for event in events),events
        assert events[-1]['payload']['expression_status']=='deadline',events
        assert client.get(BASE).json()['active_question']==snapshot['active_question']
        assert client.get('/api/v1/cart').json()['items']==[]
    finally:
        event.remove(requests.engine,'before_cursor_execute',stall)


def test_pre_authorized_momo_query_completed_before_unit_fences_old_receipt_text(pi_client,monkeypatch,tmp_path,controlled_kev_transport):
    from types import SimpleNamespace
    from app.mercury.router import get_query_model
    from app.core.config import get_settings
    from app.services import result_introduction_service as service
    client,requests,guide,base,receipt=_refund_result(pi_client)
    monkeypatch.setattr(get_settings(),'mercury_checkpoint_path',tmp_path/'late-query.sqlite3')
    nav='/api/v1/navigation/sessions/'+guide['session_id']
    opening=client.post(nav+'/opening',json={'role':'momo'}).json()
    route_body={'request_id':'pre-authorized-later-query','message':'查看退款申请进度','role':'momo','opening_id':opening['opening_id'],'role_session_id':base.rsplit('/',1)[-1]}
    route=client.post(nav+'/routes',json=route_body)
    assert route.status_code==200 and route.json()['authorized_role']=='momo',route.text
    before_opening=client.get(nav+'/opening').json()
    class QueryModel:
        def chat(self,messages,tools=None):
            if messages[-1]['role']=='tool':
                return SimpleNamespace(content='查询完成',tool_calls=[])
            return SimpleNamespace(content='',tool_calls=[SimpleNamespace(id='status',function=SimpleNamespace(name='get_refund_status',arguments=json.dumps({'order_id':'intro-order'})))])
        def cancel(self):
            pass
    client.app.dependency_overrides[get_query_model]=QueryModel
    def expression(body):
        assert not body.get('tools')
        checking='CERES_GENERAL_CLAIM_CHECK' in json.dumps(body['messages'])
        content=json.dumps({'merchant_claims':False,'execution_claims':False}) if checking else json.dumps({'text':'可以稍后再看看。','fact_ref':'result'})+'\n'
        return {'role':'assistant','content':content},'stop'
    requests.answer_hook=expression
    real_generate=service.generate_introduction
    queried=[]
    def insert_completed_query(*args,on_unit,**kwargs):
        def before_publication(text,ref):
            response=client.post(base+'/turns/stream',json={'request_id':route_body['request_id'],'routing_request_id':route_body['request_id'],'message':route_body['message']})
            assert response.status_code==200 and 'turn.completed' in response.text,response.text
            queried.append(response.text)
            # Same-role preauthorization did not change opening metadata.
            assert client.get(nav+'/opening').json()==before_opening
            on_unit(text,ref)
        return real_generate(*args,on_unit=before_publication,**kwargs)
    monkeypatch.setattr(service,'generate_introduction',insert_completed_query)
    started=client.post(base+'/result-introductions',json={'source_id':receipt['receipt_id']})
    assert started.status_code==202,started.text
    run=started.json()
    stream=client.get('/api/v1/guide/sessions/'+run['session_id']+'/runs/'+run['run_id']+'/stream')
    events=[json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith('data: ')]
    assert len(queried)==1
    assert events[-1]['payload']['expression_status']=='stale',events
    assert not any(event['type']=='answer.delta' for event in events)
    assert client.get(base+'/aftersales').json()['receipts']==[receipt]

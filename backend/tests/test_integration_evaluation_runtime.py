"""Evaluation provenance and counters at real Pi/HTTP plus deterministic event seams."""
import json
from types import SimpleNamespace

from test_runtime_pi_product_query import pi_client
from test_integration_reviewed_interim_public import install_model
from test_guide_semantics import turn
from test_guide_lifecycle import BASE


def runtime():
    from app.services.pi_product_runtime import PiProductRuntime
    return PiProductRuntime(SimpleNamespace(), lambda:None, run_id='observed-run', policy_scope={},
        route_request=lambda x:x, context={}, memory_command=lambda x:x, product_search=lambda x:x,
        comparison_search=lambda x:x, candidate_resolve=lambda x:x, history_command=lambda x:x,
        explore_products=lambda x:x, select_question_products=lambda x:x, activity_active=lambda:False, publish_interim=lambda identity,text:True)


def test_provider_ids_usage_dedup_and_missing_survive_tail():
    observed = runtime()
    start = {'type':'provider_call_start','call_id':'observed-run:1','stage':'primary_pi','model':'controlled','provider_host':'localhost'}
    end = {'type':'provider_call_end','call_id':'observed-run:1','stage':'primary_pi','status':'success',
           'duration_ms':1,'usage':{'input':2,'output':3,'cacheRead':0,'cacheWrite':0,'totalTokens':5},'cost':None}
    for event in (start,start,end,end): observed._record_event(event)
    observed._record_event({**start,'call_id':'observed-run:2'})
    for _ in range(300): observed._record_event({'type':'turn_start'})
    counts = observed.runtime_summary['provider_calls']['primary_pi']
    assert counts['started']==2 and counts['completed']==1
    assert counts['usage_observed']==1 and counts['usage_missing']==1
    assert counts['observed_usage']['totalTokens']==5 and counts['usage_complete'] is False
    assert counts['cost'] is None
    assert observed.runtime_summary['primary_pi_turns']==300
    assert observed.runtime_summary['events_truncated'] is True and len(observed.events)==256


def test_real_pi_separates_auditor_and_provider_calls_and_persists_versions(pi_client):
    client, requests = pi_client
    install_model(requests)
    events = turn(client, '看看进展', 'evaluation-observed')
    assert events[-1]['type']=='turn.completed', events
    result = events[-1]['payload']
    summary = result['runtime_summary']
    assert summary['primary_pi_turns']==2 and summary['interim_audit_attempts']==1
    assert summary['provider_calls']['primary_pi']['started']==2
    assert summary['provider_calls']['interim_audit']['started']==1
    assert summary['provider_calls']['primary_pi']['observed_usage'] is None
    rows = summary['provider_call_records']
    assert len(rows)==3 and len({row['call_id'] for row in rows})==3
    assert all(row['usage'] is None and row['cost'] is None for row in rows)
    assert result['entry_judgment']['outcome']=='no'
    assert result['entry_judgment']['routing_request_id']=='evaluation-observed'
    version = result['runtime_version']
    assert version['source_revision'] and version['build_revision'] and version['prompt_revision']
    assert version['source_scope']=='disk_at_admission'
    assert version['build_scope']=='worker_disk_at_start'
    assert version['loaded_code_equivalence']=='unknown'
    persisted = client.get(BASE+'/turns/evaluation-observed').json()['result']
    assert persisted['runtime_version']==version and persisted['runtime_summary']==summary
    assert 'source_revision' not in json.dumps(requests)
    assert 'offline-fixture-key' not in json.dumps(result)


def test_provider_error_retains_known_calls_and_unknown_usage(pi_client):
    client, requests = pi_client
    events = turn(client, '模型认证失败', 'evaluation-failed')
    assert events[-1]['type']=='error'
    result = client.get(BASE+'/turns/evaluation-failed').json()['result']
    counts = result['runtime_summary']['provider_calls']['primary_pi']
    assert counts['started']>=1 and counts['completed']==counts['started']
    assert counts['usage_observed']==0 and counts['observed_usage'] is None
    assert result['runtime_version']['source_revision'] and result['runtime_version']['build_revision']
    assert result['entry_judgment']['routing_request_id']=='evaluation-failed'
    assert 'offline-fixture-key' not in json.dumps(result)


def test_export_projects_complete_graph_counts_without_tail_inference():
    from app.evaluation.export_runs import summary
    data = {'graph_tool_attempts':1,'graph_official_calls':1,'graph_provider_calls':70,
            'graph_embedding_calls':1, 'graph_queries':[{'attempt_id':'a','graph_query_id':'g',
                'calls_truncated':True, 'calls':[{'call_id':'g:70','kind':'completion','usage':None,'cost':None}],
                'graph_index_revision':'actual-index','query_revision':'actual-query','duration_ms':None}]}
    exported = summary(data)
    assert exported['graph_provider_calls']==70
    assert exported['graph_queries'][0]['calls_truncated'] is True
    assert exported['graph_queries'][0]['graph_index_revision']=='actual-index'


import pytest


@pytest.mark.parametrize('usage', [None, {'prompt_tokens':0,'completion_tokens':0,'total_tokens':0},
                                     {'prompt_tokens':2,'completion_tokens':3,'total_tokens':5}])
def test_real_wire_usage_distinguishes_absent_zero_and_partial(pi_client, monkeypatch, usage):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    from app.core.config import get_settings
    from test_guide_clarification_context import call
    client, _ = pi_client
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            outputs=[m for m in body['messages'] if m['role']=='tool']
            delta, reason=call(body,'finish_response',{'status':'completed','answer_kind':'status'}) if outputs else call(body,'guide_request',{'kind':'progress'})
            self.send_response(200); self.send_header('Content-Type','text/event-stream'); self.end_headers()
            for chunk in ({'choices':[{'index':0,'delta':delta,'finish_reason':None}]},
                          {'choices':[{'index':0,'delta':{},'finish_reason':reason}]},
                          {'choices':[], **({'usage':usage} if usage is not None else {})}):
                self.wfile.write(('data: '+json.dumps({'id':'usage-fixture','object':'chat.completion.chunk','model':'controlled-pi',**chunk})+'\n\n').encode())
            self.wfile.write(b'data: [DONE]\n\n')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    monkeypatch.setenv('OPENAI_BASE_URL',f'http://127.0.0.1:{server.server_port}/v1'); get_settings.cache_clear()
    try:
        events=turn(client,'查看进度','wire-usage')
        assert events[-1]['type']=='turn.completed',events
        counts=events[-1]['payload']['runtime_summary']['provider_calls']['primary_pi']
        assert counts['started']==2
        if usage is None:
            assert counts['observed_usage'] is None and counts['usage_missing']==2
        else:
            assert counts['observed_usage']['totalTokens']==2*usage['total_tokens']
            assert counts['observed_usage']['cacheRead'] is None and counts['observed_usage']['cacheWrite'] is None
            assert counts['usage_observed']==2 and counts['cost'] is None
    finally:
        server.shutdown(); server.server_close(); thread.join(); get_settings.cache_clear()


def test_graph_pending_counts_are_unknown_and_completed_counts_survive_tail():
    observed=runtime()
    observed._record_event({'type':'graph_query_start','attempt_id':'graph-a'})
    assert observed.runtime_summary['graph_provider_calls'] is None
    observed._record_event({'type':'graph_query_end','attempt_id':'graph-a','official_graph_calls':1,
        'provider_calls':70,'embedding_calls':1,'calls_truncated':True,'calls':[]})
    for _ in range(300): observed._record_event({'type':'turn_start'})
    assert observed.runtime_summary['graph_provider_calls']==70
    assert observed.runtime_summary['graph_queries'][0]['calls_truncated'] is True


def test_real_search_observation_scopes_threads_errors_and_cleanup(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from app.services.knowledge_service import KnowledgeService
    from app.services.runtime_observation import begin_retrieval_observation, end_retrieval_observation
    barrier=threading.Barrier(2)
    service=KnowledgeService()
    def query(request, **kwargs):
        assert kwargs['deadline']==123 and kwargs['should_stop'] is None
        barrier.wait(timeout=3)
        if request['query']=='fail': raise ValueError('controlled lookup error')
        return {'hits':[], 'manifest':{'corpus_revision':'source-v1'}}
    monkeypatch.setattr(service,'_query',query)
    def work(name):
        observed=[]
        token=begin_retrieval_observation(name,observed.append)
        try:
            if name=='fail':
                with pytest.raises(ValueError,match='controlled lookup error'):
                    service.search(name,'product',deadline=123)
            else:
                assert service.search(name,'product',deadline=123)['hits']==[]
        finally:
            end_retrieval_observation(token)
        return observed
    with ThreadPoolExecutor(max_workers=2) as pool:
        good,bad=list(pool.map(work,['owner-a-run','fail']))
    assert len(good)==len(bad)==2
    assert all(row['run_id']=='owner-a-run' for row in good)
    assert all(row['run_id']=='fail' for row in bad)
    assert good[-1]['outcome']=='empty' and bad[-1]['outcome']=='error'
    assert good[-1]['source_revision']=='source-v1' and good[-1]['index_revision']
    assert good[-1]['elapsed_ms']>=0 and bad[-1]['elapsed_ms']>=0
    assert good[0]['retrieval_id']!=bad[0]['retrieval_id']
    # Standalone read after scope exit must not attach to an earlier owner/run.
    monkeypatch.setattr(service,'_query',lambda *args,**kwargs:{'hits':[],'manifest':{}})
    service.search('standalone','product',deadline=123)
    assert len(good)==len(bad)==2


def test_policy_reuse_does_not_start_another_real_search(monkeypatch, controlled_policy_source):
    import time
    from app.services.knowledge_service import knowledge, KnowledgeService
    from app.services.runtime_observation import begin_retrieval_observation, end_retrieval_observation
    monkeypatch.setattr(knowledge,'search',KnowledgeService.search.__get__(knowledge,KnowledgeService))
    monkeypatch.setattr(knowledge,'_query',lambda *args,**kwargs:{'hits':[],'manifest':controlled_policy_source['manifest']})
    observed=runtime(); observed.policy_scope={'request_id':'request-a'}
    observed.policy_deadline=time.monotonic()+15; observed.policy_should_stop=lambda:False
    token=begin_retrieval_observation('observed-run',observed._record_event)
    try:
        first=observed._query_policy('same empty scope',None,origin='prefetch')
        for _ in range(48): assert observed._query_policy('same empty scope',None,origin='tool')==first
    finally:
        end_retrieval_observation(token)
    for _ in range(300): observed._record_event({'type':'turn_start'})
    assert observed.runtime_summary['policy_lookups']==1 and observed.runtime_summary['policy_reuses']==48
    assert observed.runtime_summary['retrieval_calls']['policy']=={'started':1,'completed':1,'success':0,'empty':1,'error':0}
    assert observed.runtime_summary['policy_sources'][0]['index_revision']==first['index_revision']


def test_usage_observer_forwards_early_wire_bytes_and_cancellation():
    from pathlib import Path
    import subprocess
    module=Path(__file__).resolve().parents[2]/'runtime/pi/dist/provider-observation.js'
    script=r'''
import http from 'node:http';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const {observeProviderUsage}=await import(pathToFileURL(process.argv[1]));
const first='data: {"choices":[{"delta":{"content":"first"}}]}\n\n';
const last='data: {"choices":[],"usage":{"prompt_tokens":0,"completion_tokens":1,"total_tokens":1}}\n\ndata: [DONE]\n\n';
let release;
let closed;
const stopped=new Promise(resolve=>{closed=resolve;});
const server=http.createServer((req,res)=>{
  res.writeHead(200,{'Content-Type':'text/event-stream'});
  res.write(first);
  release=()=>res.end(last);
  res.on('close',()=>closed());
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let timer;
const deadline=new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('First chunk blocked on usage tail')),2000);});
try {
  let usage=null;
  const response=observeProviderUsage(await fetch(`http://127.0.0.1:${server.address().port}`),value=>{usage=value;});
  const reader=response.body.getReader();
  const early=await Promise.race([reader.read(),deadline]);
  clearTimeout(timer);
  assert.equal(new TextDecoder().decode(early.value),first);
  assert.equal(usage,null);
  release();
  let bytes=Buffer.from(early.value);
  while(true) { const row=await reader.read(); if(row.done) break; bytes=Buffer.concat([bytes,Buffer.from(row.value)]); }
  assert.equal(bytes.toString(),first+last);
  assert.equal(usage.input,0); assert.equal(usage.totalTokens,1); assert.equal(usage.cacheRead,null);
  let cancelledUsage=null;
  const abort=new AbortController();
  const cancelled=observeProviderUsage(await fetch(`http://127.0.0.1:${server.address().port}`,{signal:abort.signal}),value=>{cancelledUsage=value;});
  const cancelReader=cancelled.body.getReader(); await cancelReader.read();
  abort.abort();
  await assert.rejects(cancelReader.read());
  assert.equal(cancelledUsage,null);
  console.log('early_bytes_equal; usage_unknown_until_tail; cancellation_preserved');
} finally {clearTimeout(timer);server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
'''
    result=subprocess.run(['node','--input-type=module','-e',script,str(module)],capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    assert 'early_bytes_equal; usage_unknown_until_tail; cancellation_preserved' in result.stdout


def test_entry_judgment_is_exact_request_and_owner_not_latest(pi_client, controlled_kev_transport):
    client,requests=pi_client
    install_model(requests)
    first=turn(client,'看看进展','entry-first')[-1]['payload']
    controlled_kev_transport['choose']=lambda state:'uncertain'
    second=turn(client,'再看看进展','entry-second')[-1]['payload']
    assert first['entry_judgment']['outcome']=='no' and second['entry_judgment']['outcome']=='uncertain'
    saved=client.get(BASE+'/turns/entry-first').json()['result']
    assert saved['entry_judgment']==first['entry_judgment']
    client.cookies.set('sg_owner_id','pi-owner-b')
    denied=client.get(BASE+'/turns/entry-first')
    assert denied.status_code==403


def test_export_real_observations_preserves_recorded_versions(pi_client, monkeypatch, tmp_path):
    from sqlalchemy.orm import sessionmaker
    from app.core import database
    from app.evaluation.export_runs import export_runs
    client,requests=pi_client
    install_model(requests)
    result=turn(client,'看看进展','export-observed')[-1]['payload']
    monkeypatch.setattr(database,'SessionLocal',sessionmaker(bind=requests.engine))
    output=tmp_path/'controlled-owner.jsonl'
    export_runs('pi-owner-a',output)
    row=json.loads(output.read_text().splitlines()[0])
    assert row['runtime_version']==result['runtime_version']
    assert row['entry_judgment']==result['entry_judgment']
    assert row['runtime_summary']['provider_calls']==result['runtime_summary']['provider_calls']
    assert row['runtime_summary']['provider_call_records']==result['runtime_summary']['provider_call_records']
    assert row['labels'] is None
    assert 'offline-fixture-key' not in output.read_text()


def test_failure_before_pi_construction_retains_admission_and_replays(pi_client, monkeypatch):
    from app.services.pi_product_turn_service import PiProductTurnService
    from app.core.errors import AppError
    client,requests=pi_client
    calls=[]
    def fail(*args,**kwargs):
        calls.append(kwargs['run_id'])
        raise AppError(503,'CONTROLLED_PRE_PI_FAILURE','Controlled pre-runtime failure')
    monkeypatch.setattr(PiProductTurnService,'process',fail)
    first=turn(client,'看看进展','pre-pi-failure')
    assert first[-1]['type']=='error' and first[-1]['payload']['code']=='CONTROLLED_PRE_PI_FAILURE'
    receipt=client.get(BASE+'/turns/pre-pi-failure').json()
    result=receipt['result']
    assert result['runtime_version']['source_revision']
    assert result['runtime_version']['build_revision'] is None
    assert result['runtime_version']['loaded_code_equivalence']=='unknown'
    assert result['entry_judgment']['routing_request_id']=='pre-pi-failure'
    assert result.get('runtime_summary') is None
    assert turn(client,'看看进展','pre-pi-failure')==first
    assert client.get(BASE+'/turns/pre-pi-failure').json()==receipt
    assert len(calls)==1 and not requests


@pytest.mark.parametrize('fail_initial',[False,True])
def test_initial_context_search_is_counted_through_final_projection_or_error(pi_client, monkeypatch, fail_initial):
    from app.services.product_question_service import ProductQuestionService
    from app.services.knowledge_service import knowledge, KnowledgeService
    client,requests=pi_client
    install_model(requests)
    state=client.get(BASE).json()
    body={'request_id':'initial-context-count','message':'看看进展','expected_task_id':state['task_id'],
          'expected_state_version':state['state_version'],'expected_session_version':state['session_version']}
    calls=[]
    monkeypatch.setattr(knowledge,'search',KnowledgeService.search.__get__(knowledge,KnowledgeService))
    def query(request,**kwargs):
        calls.append(request)
        return {'hits':[],'manifest':{'corpus_revision':'initial-context-source'}}
    monkeypatch.setattr(knowledge,'_query',query)
    original=ProductQuestionService.projection
    def projection(self,session_id,**kwargs):
        if self.deadline is not None:
            knowledge.search('initial or final context','product',deadline=self.deadline,should_stop=self.should_stop)
            if fail_initial:
                raise ValueError('Controlled initial projection failure')
        return original(self,session_id,**kwargs)
    monkeypatch.setattr(ProductQuestionService,'projection',projection)
    response=client.post(BASE+'/turns/stream',json=body)
    events=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    if fail_initial:
        assert events[-1]['type']=='error' and not requests
        assert len(calls)==1
    else:
        assert events[-1]['type']=='turn.completed',events
        assert len(calls)>=2  # Initial context and final public question projection.
    result=client.get(BASE+'/turns/initial-context-count').json()['result']
    counts=result['runtime_summary']['retrieval_calls']['product']
    assert counts['started']==counts['completed']==counts['empty']==len(calls)
    assert result['runtime_summary']['retrieval_sources'][0]['source_revision']=='initial-context-source'
    if fail_initial:
        assert result['runtime_summary'].get('provider_calls') is None
    from app.services.runtime_observation import retrieval_observer
    assert retrieval_observer() is None


def test_export_graph_method_preserves_local_global_and_unknown():
    from app.evaluation.export_runs import summary,diagnostic
    rows=[{'type':'graph_query_end','method':method,'graph_query_id':str(index)}
          for index,method in enumerate(['local','global',None])]
    assert [row['method'] for row in summary({'graph_queries':rows})['graph_queries']]==['local','global',None]
    assert [row['method'] for row in diagnostic(rows)]==['local','global',None]

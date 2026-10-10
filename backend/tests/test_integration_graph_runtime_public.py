"""Explicit graph integration through actual Pi transport and public Guide HTTP/SSE.

Graph retrieval is controlled here; official GraphRAG/model coverage is separate.
"""
import hashlib
import json
import time

import pytest

from test_runtime_pi_product_query import pi_client
from test_judge_policy_prefetch_public import policy_transport, prefetched
from test_guide_clarification_context import call
from test_guide_semantics import turn
from test_guide_lifecycle import BASE


@pytest.fixture
def controlled_graph(monkeypatch):
    from app.core.config import ROOT_DIR
    from app.knowledge.corpus import FIXTURE_NAMES
    from app.services.knowledge_service import knowledge
    from app.services.dish_service import recipes
    calls = []
    def graph(query, method='local', *, deadline, should_stop=None):
        assert 0 < deadline - time.monotonic() <= 15
        assert should_stop is not None
        calls.append({'query': query, 'method': method, 'deadline': deadline})
        dishes = recipes()[:2]
        identity = 'controlled-query-' + str(len(calls))
        return {'query': query, 'method': method, 'graph_query_id': identity,
            'graph_status': 'success', 'official_graph_calls': 1,
            'graph_index_revision': 'controlled-index', 'query_revision': 'controlled-query-v1',
            'manifest': {'graph_revision': 'controlled-graph-v1', 'files': {
                name: hashlib.sha256((ROOT_DIR/'data/fixtures'/name).read_bytes()).hexdigest() for name in FIXTURE_NAMES}},
            'selection': {'entity_numbers': [0]}, 'model_selected_entity_ids': ['recipe:'+dishes[0]['dish_id']],
            'canonical_scope': 'retrieved_communities' if method == 'global' else 'model_selection',
            'canonical_facts': [{'id': 'recipe:'+dish['dish_id'], 'type': 'RECIPE', 'title': dish['name'],
                                 'description': 'Do not use this generated amount: 9999kg'} for dish in dishes],
            'ingredient_recipes': {}, 'calls': [{'call_id': identity+'-call', 'graph_query_id': identity,
                'kind': 'completion', 'status': 'success', 'usage': None, 'cost': None}],
            'call_counts': {'completion': 1, 'embedding': 1}, 'calls_truncated': False, 'duration_ms': 1.5}
    monkeypatch.setattr(knowledge, 'graph', graph)
    return calls


@pytest.mark.parametrize('method', ['local','global'])
def test_explicit_graph_uses_native_recipe_refs_and_keeps_policy_role_boundary(pi_client, policy_transport, controlled_graph, method):
    client, requests = pi_client
    def respond(body):
        outputs = [json.loads(row['content']) for row in body['messages'] if row['role']=='tool']
        if not outputs:
            return call(body, 'guide_request', {'kind':'question'})
        if len(outputs)==1:
            assert 'search_recipe_relations' in {tool['function']['name'] for tool in body['tools']}
            return call(body, 'search_recipe_relations', {'query':'哪些菜共用鸡蛋', 'method':method})
        graph = outputs[-1]
        assert graph['outcome']=='success'
        assert graph['graph_evidence']['selection']=={'entity_numbers':[0]}
        return call(body, 'finish_response', {'status':'completed','answer_kind':'recipe_facts',
            'dish_refs':[row['ref'] for row in graph['dishes']],
            'policy_ref':prefetched(body)['policy_ref'],'role_boundary':True})
    requests.answer_hook = respond
    events = turn(client, '明确查菜谱图中的鸡蛋关系和基准用量；退货政策；具体订单退货另交墨墨，不采购', 'graph-mixed-'+method)
    assert events[-1]['type']=='turn.completed', events
    result = events[-1]['payload']
    public_text = '\n'.join(row['content'] for row in result['messages'])
    assert all(text in public_text for text in ('番茄 300g','鸡蛋 3pc','鸡蛋 2pc','共用必需食材：鸡蛋','墨墨'))
    assert '9999kg' not in public_text
    assert controlled_graph[0]['method']==method
    summary = result['runtime_summary']
    assert summary['graph_tool_attempts']==1 and summary['graph_official_calls']==1
    assert summary['graph_provider_calls']==1 and summary['graph_queries'][0]['selection']=={'entity_numbers':[0]}
    assert len(requests)==3
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items']==[]


@pytest.mark.parametrize('failed', [False,True])
def test_graph_empty_and_failure_remain_distinct_and_preserve_other_results(pi_client, policy_transport, controlled_graph, monkeypatch, failed):
    from app.services.knowledge_service import knowledge
    from app.core.errors import AppError
    original = knowledge.graph
    def query(*args, **kwargs):
        result = original(*args, **kwargs)
        if failed:
            result.update(error='GRAPH_INDEX_MISSING', graph_status='not_executed', official_graph_calls=0,
                          call_counts={'completion':0,'embedding':0},calls=[])
            raise AppError(503, 'GRAPH_INDEX_MISSING', 'Controlled missing index', graph_observation=result)
        result.update(canonical_facts=[],selection={'entity_numbers':[]},model_selected_entity_ids=[])
        return result
    monkeypatch.setattr(knowledge,'graph',query)
    client,requests=pi_client
    def respond(body):
        outputs=[json.loads(row['content']) for row in body['messages'] if row['role']=='tool']
        if not outputs:
            return call(body,'guide_request',{'kind':'question'})
        if len(outputs)==1:
            return call(body,'search_recipe_relations',{'query':'哪些菜共用鸡蛋'})
        assert outputs[-1]['outcome']==('error' if failed else 'empty')
        assert outputs[-1]['dishes']==[]
        return call(body,'finish_response',{'status':'completed','answer_kind':'recipe_facts','dish_refs':[],
                                           'policy_ref':prefetched(body)['policy_ref'],'role_boundary':True})
    requests.answer_hook=respond
    events=turn(client,'查菜谱图关系、退货政策和订单退货职责，不采购','graph-outcome-'+str(failed))
    assert events[-1]['type']=='turn.completed',events
    text='\n'.join(row['content'] for row in events[-1]['payload']['messages'])
    assert ('图查询未能完成' if failed else '图查询未取得可核对的相关菜谱') in text
    assert '不能据此判断不存在' in text and '墨墨' in text
    assert client.get('/api/v1/cart').json()['items']==[]


def test_graph_result_rejects_foreign_recipe_reference(pi_client, controlled_graph):
    client,requests=pi_client
    def respond(body):
        outputs=[json.loads(row['content']) for row in body['messages'] if row['role']=='tool']
        if not outputs:
            return call(body,'guide_request',{'kind':'question'})
        if len(outputs)==1:
            return call(body,'search_recipe_relations',{'query':'鸡蛋'})
        return call(body,'finish_response',{'status':'completed','answer_kind':'recipe_facts','dish_refs':['foreign-dish']})
    requests.answer_hook=respond
    events=turn(client,'明确查询鸡蛋图关系','graph-forged')
    assert events[-1]['type']=='error' and events[-1]['payload']['code']=='PI_UNKNOWN_REFERENCE',events
    assert client.get('/api/v1/cart').json()['items']==[]


def test_ordinary_recipe_facts_never_invoke_graph(pi_client, monkeypatch):
    from app.services.knowledge_service import knowledge
    monkeypatch.setattr(knowledge,'graph',lambda *a,**k:pytest.fail('Implicit graph call'))
    client,requests=pi_client
    def respond(body):
        outputs=[json.loads(row['content']) for row in body['messages'] if row['role']=='tool']
        if not outputs:
            return call(body,'guide_request',{'kind':'question'})
        if len(outputs)==1:
            return call(body,'search_dishes',{'query':'番茄炒蛋'})
        return call(body,'finish_response',{'status':'completed','answer_kind':'recipe_facts','dish_refs':[outputs[-1]['dishes'][0]['ref']]})
    requests.answer_hook=respond
    events=turn(client,'番茄炒蛋基准用量','ordinary-facts-no-graph')
    assert events[-1]['type']=='turn.completed',events
    assert events[-1]['payload']['runtime_summary']['graph_tool_attempts']==0


def test_graph_facts_reread_current_offer_and_audited_interim(pi_client, controlled_graph):
    from sqlalchemy.orm import Session
    from sqlalchemy import select
    from app.models.catalog import CatalogProduct
    from app.models.store import Offer
    from test_integration_reviewed_interim_public import audit_request, CANDIDATE
    client,requests=pi_client
    with Session(requests.engine) as db,db.begin():
        db.add(CatalogProduct(sku_id='graph-egg',name='Graph eggs',name_zh='图查询鸡蛋',category_id='dairy',
            brand='受控',source='controlled-demo',review_status='approved',spec_quantity=10,spec_unit='pc',ingredient_ids=json.dumps(['egg'])))
        db.add(Offer(store_id='pi-store',sku_id='graph-egg',price_fen=500,available_qty=10,sellable=True,offer_version=1,is_demo=True))
    def respond(body):
        if audit_request(body):
            return {'role':'assistant','content':json.dumps({'merchant_claims':False,'execution_claims':False,'private_content':False})},'stop'
        outputs=[json.loads(row['content']) for row in body['messages'] if row['role']=='tool']
        if not outputs:
            return call(body,'guide_request',{'kind':'question'})
        if len(outputs)==1:
            result=call(body,'search_recipe_relations',{'query':'鸡蛋菜谱关系'})
            result[0]['content']=CANDIDATE
            return result
        with Session(requests.engine) as db,db.begin():
            offer=db.scalar(select(Offer).where(Offer.sku_id=='graph-egg'))
            offer.price_fen,offer.available_qty,offer.offer_version=777,2,2
        return call(body,'finish_response',{'status':'completed','answer_kind':'recipe_facts',
            'dish_refs':[row['ref'] for row in outputs[-1]['dishes']],'ingredient_ids':['egg']})
    requests.answer_hook=respond
    events=turn(client,'明确查鸡蛋菜谱图关系、基准用量和当前鸡蛋价格，不采购','graph-current-offer-interim')
    assert events[-1]['type']=='turn.completed',events
    text='\n'.join(row['content'] for row in events[-1]['payload']['messages'])
    assert '图查询鸡蛋' in text and '¥7.77' in text and '库存 2' in text and '¥5.00' not in text
    assert '9999kg' not in text
    assert len([event for event in events if event['type']=='message.interim'])==1
    summary=events[-1]['payload']['runtime_summary']
    assert summary['interim_audit_attempts']==summary['interim_messages']==summary['graph_tool_attempts']==1
    assert client.get(BASE).json()['plan'] is None and client.get('/api/v1/cart').json()['items']==[]


def test_graph_summary_survives_bounded_event_tail(pi_client, controlled_graph, monkeypatch):
    from app.services.pi_product_runtime import PiProductRuntime
    record=PiProductRuntime._record_event
    def record_with_long_tail(self,event):
        record(self,event)
        if event['type']=='graph_query_end':
            for _ in range(300):
                record(self,{'type':'controlled_tail_event'})
    monkeypatch.setattr(PiProductRuntime,'_record_event',record_with_long_tail)
    client,requests=pi_client
    def respond(body):
        outputs=[json.loads(row['content']) for row in body['messages'] if row['role']=='tool']
        if not outputs:
            return call(body,'guide_request',{'kind':'question'})
        if len(outputs)==1:
            return call(body,'search_recipe_relations',{'query':'鸡蛋菜谱关系'})
        return call(body,'finish_response',{'status':'completed','answer_kind':'recipe_facts','dish_refs':[outputs[-1]['dishes'][0]['ref']]})
    requests.answer_hook=respond
    events=turn(client,'明确查鸡蛋菜谱图关系','graph-summary-tail')
    assert events[-1]['type']=='turn.completed',events
    result=events[-1]['payload']
    assert result['runtime_summary']['events_truncated'] is True
    assert result['runtime_summary']['graph_tool_attempts']==result['runtime_summary']['graph_provider_calls']==1
    assert len(result['runtime_summary']['graph_queries'])==1
    assert result['runtime_summary']['graph_queries'][0]['graph_query_id']=='controlled-query-1'
    assert all(event['type']!='graph_query_end' for event in result['runtime_events'])


@pytest.mark.parametrize('interrupt',['stop','deadline'])
def test_graph_lookup_uses_original_run_deadline_and_never_publishes_late_facts(pi_client, monkeypatch, interrupt):
    from app.services.knowledge_service import knowledge,check_budget
    client,requests=pi_client
    def blocked(query,method='local',*,deadline,should_stop):
        requests.started.set()
        while True:
            check_budget(deadline,should_stop)
            time.sleep(.01)
    monkeypatch.setattr(knowledge,'graph',blocked)
    def respond(body):
        outputs=[json.loads(row['content']) for row in body['messages'] if row['role']=='tool']
        if not outputs:
            return call(body,'guide_request',{'kind':'question'})
        if len(outputs)==1:
            return call(body,'search_recipe_relations',{'query':'鸡蛋图关系'})
        pytest.fail('Cancelled/deadline graph result reached another Pi model turn')
    requests.answer_hook=respond
    state=client.get(BASE).json()
    body={'request_id':'graph-interrupt-'+interrupt,'message':'明确查鸡蛋图关系','expected_task_id':state['task_id'],
          'expected_state_version':state['state_version'],'expected_session_version':state['session_version']}
    started=time.monotonic()
    response=client.post(BASE+'/runs',json=body)
    assert response.status_code==202,response.text
    assert requests.started.wait(timeout=10)
    if interrupt=='stop':
        stopped=client.post(BASE+'/turns/stop',json={'request_id':body['request_id']})
        assert stopped.status_code==200 and stopped.json()['cancelled']
    events=[json.loads(line[6:]) for line in client.get(BASE+f"/runs/{response.json()['run_id']}/stream").text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type']==('turn.stopped' if interrupt=='stop' else 'turn.completed'),events
    assert events[-1]['payload']['runtime_status']==('stopped' if interrupt=='stop' else 'deadline')
    if interrupt=='deadline':
        assert 14 <= time.monotonic()-started < 20
    assert not any(event['type']=='message.interim' for event in events)
    assert len(requests)==2
    assert client.get('/api/v1/cart').json()['items']==[]

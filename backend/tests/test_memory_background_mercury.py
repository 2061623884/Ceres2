"""Actual LangGraph completed publication is an automatic memory source."""
import json
from types import SimpleNamespace
from test_mercury_public import mercury_client, tool_message
from test_memory_mercury import payload
from app.services.memory_background import MemoryWorker


def test_only_completed_mercury_chat_enqueues_its_user_source_and_keeps_role_boundary(mercury_client):
    from app.mercury.router import get_query_model
    client, app, selected_url, sessions = mercury_client
    class Query:
        def chat(self,messages,tools=None):
            return SimpleNamespace(content='查询结果',tool_calls=[]) if messages[-1]['role']=='tool' else tool_message()
        def cancel(self): pass
    app.dependency_overrides[get_query_model] = Query
    calls = []
    def extract(source):
        calls.append(source)
        return {'records':[
            {'category':'feedback','domain':'communication','key':'style','content':'回复先说结论',
                'source_quote':'回复先说结论','scope':'durable'},
            {'category':'user','domain':'shopping','key':'shopping-only','content':'回复先说结论',
                'source_quote':'回复先说结论','scope':'durable'}]}
    worker = MemoryWorker(sessions.kw['bind'],extract=extract,dream=lambda _: {'records':[]})
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    waiting = payload(client.post('/api/v1/mercury/sessions/'+sid+'/turns/stream',
        json={'message':'查看订单','request_id':'waiting-no-source'}))
    assert waiting['status'] == 'awaiting_order'
    assert not worker.run_once()
    completed = payload(client.post(selected_url+'/turns/stream',
        json={'message':'查看订单，我长期希望回复先说结论','request_id':'momo-auto-source'}))
    assert completed['status'] == 'completed' and '已记住' not in completed['final_text']
    assert worker.run_once()
    assert len(calls) == 1 and calls[0]['role'] == 'momo'
    class List:
        def chat(self,messages,tools=None):
            return SimpleNamespace(content='',tool_calls=[]) if messages[-1]['role']=='tool' else tool_message('memory_command',json.dumps({'action':'list'}))
        def cancel(self): pass
    app.dependency_overrides[get_query_model] = List
    result = payload(client.post(selected_url+'/turns/stream',json={'message':'查看记忆','request_id':'momo-auto-list'}))
    assert result['status'] == 'completed' and result['action_results'], result
    records = result['action_results'][0]['records']
    assert [(r['content'],r['origin_role'],r['domain']) for r in records] == [('回复先说结论','momo','communication')]
    assert not worker.run_once(), 'Management-only turns must not become automatic extraction sources'


def test_oversized_mercury_source_is_not_silently_prefix_extracted(mercury_client):
    from app.mercury.router import get_query_model
    client, app, selected_url, sessions = mercury_client
    class Query:
        def chat(self,messages,tools=None):
            return SimpleNamespace(content='',tool_calls=[]) if messages[-1]['role']=='tool' else tool_message()
        def cancel(self): pass
    app.dependency_overrides[get_query_model]=Query
    message='查看订单，我长期希望回复先说结论。'+'普通背景。'*1700+'更正：不用保存上述偏好。'
    assert len(message)>8000
    assert payload(client.post(selected_url+'/turns/stream',json={'message':message,
        'request_id':'oversized-memory-source'}))['status']=='completed'
    calls=[]
    def extract(source):
        calls.append(source)
        return {'records':[{'category':'feedback','domain':'communication','key':'style',
            'content':'回复先说结论','source_quote':'回复先说结论','scope':'durable'}]}
    worker=MemoryWorker(sessions.kw['bind'],extract=extract,dream=lambda _: {'records':[]})
    assert worker.run_once()
    assert not worker.run_once()
    assert calls==[], 'Oversized immutable source must be failed whole, never partially modeled'
    class List:
        def chat(self,messages,tools=None):
            return SimpleNamespace(content='',tool_calls=[]) if messages[-1]['role']=='tool' else tool_message('memory_command',json.dumps({'action':'list'}))
        def cancel(self): pass
    app.dependency_overrides[get_query_model]=List
    result=payload(client.post(selected_url+'/turns/stream',json={'message':'查看记忆','request_id':'oversized-source-list'}))
    assert result['status']=='completed' and result['action_results'], result
    assert result['action_results'][0]['records']==[]

"""Actual LangGraph public memory commands and need-to-know query context."""
import json
from types import SimpleNamespace
from test_mercury_public import mercury_client, tool_message


def payload(response):
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')][-1]


def test_momo_memory_without_order_is_committed_with_chat_and_used_only_when_relevant(mercury_client):
    from app.mercury.router import get_query_model
    client, app, selected_url, sessions = mercury_client
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = '/api/v1/mercury/sessions/' + sid
    class Model:
        command = {'action':'save','category':'feedback','domain':'communication','key':'answer_style',
            'content':'回复先说结论','source_quote':'请记住回复先说结论'}
        seen = []
        def chat(self, messages, tools=None):
            self.seen.append(messages)
            if self.command:
                return tool_message('memory_command',json.dumps(self.command,ensure_ascii=False))
            return SimpleNamespace(content='',tool_calls=[]) if messages[-1]['role']=='tool' else tool_message()
        def cancel(self): pass
    model = Model()
    app.dependency_overrides[get_query_model] = lambda: model
    response = client.post(url+'/turns/stream',json={'message':'请记住回复先说结论','request_id':'save'})
    result = payload(response)
    assert result['status'] == 'completed', result
    saved = result['action_results'][0]['records'][0]
    assert saved['origin_role'] == 'momo' and saved['source'] == 'explicit'
    assert '已记住' in client.get(url).json()['messages'][-1]['content']
    model.command = None
    model.seen.clear()
    answer = payload(client.post(selected_url+'/turns/stream',json={'message':'查看订单','request_id':'query'}))
    assert '15.00' in answer['final_text']
    assert '回复先说结论' in model.seen[0][0]['content']
    model.command = {'action':'delete','memory_id':saved['memory_id'],'expected_revision':1,'source_quote':'删除这条记忆'}
    assert payload(client.post(url+'/turns/stream',json={'message':'删除这条记忆','request_id':'delete'}))['status'] == 'completed'
    model.command = None
    model.seen.clear()
    client.post(selected_url+'/turns/stream',json={'message':'查看订单','request_id':'query-again'})
    assert '回复先说结论' not in model.seen[0][0]['content']

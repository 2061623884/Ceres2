"""Natural correction resolves an owned record before the single write."""
import json
from types import SimpleNamespace
from test_runtime_pi_product_query import pi_client
from test_memory_public import memory_turn
from test_guide_semantics import turn
from test_mercury_public import mercury_client,tool_message
from test_memory_mercury import payload


def correction(outputs):
    if not outputs:
        return {'action':'list'}
    return {'action':'update','memory_id':outputs[-1]['records'][0]['memory_id'],
        'expected_revision':outputs[-1]['records'][0]['revision'],'content':'可乐选小瓶',
        'source_quote':'把刚才的可乐偏好改为小瓶'}


def test_keke_can_resolve_then_correct_memory_in_one_natural_turn(pi_client):
    client,requests=pi_client
    memory_turn(client,requests,'记住可乐选无糖',{'action':'save','category':'user','domain':'shopping',
        'key':'drink','content':'可乐选无糖','source_quote':'记住可乐选无糖'},'save')
    def hook(body):
        outputs=[json.loads(m['content']) for m in body['messages'] if m['role']=='tool']
        if len(outputs)<2:
            return {'role':'assistant','tool_calls':[{'index':0,'id':f'memory-{len(outputs)}','type':'function',
                'function':{'name':'memory_command','arguments':json.dumps(correction(outputs),ensure_ascii=False)}}]},'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'memory_result',
            'memory_ref':outputs[-1]['memory_ref']})},'stop'
    requests.answer_hook=hook
    events=turn(client,'把刚才的可乐偏好改为小瓶','correct')
    assert events[-1]['type']=='turn.completed',events
    record=events[-1]['payload']['action_results'][0]['records'][0]
    assert record['revision']==2 and record['content']=='可乐选小瓶'


def test_momo_can_resolve_then_correct_memory_in_one_natural_turn(mercury_client):
    from app.mercury.router import get_query_model
    client,app,url,sessions=mercury_client
    class Model:
        correcting=False
        def chat(self,messages,tools=None):
            if not self.correcting:
                return tool_message('memory_command',json.dumps({'action':'save','category':'user','domain':'shopping',
                    'key':'drink','content':'可乐选无糖','source_quote':'记住可乐选无糖'},ensure_ascii=False))
            outputs=[json.loads(m['content']) for m in messages if m['role']=='tool']
            return tool_message('memory_command',json.dumps(correction(outputs),ensure_ascii=False))
        def cancel(self): pass
    model=Model()
    app.dependency_overrides[get_query_model]=lambda:model
    assert payload(client.post(url+'/turns/stream',json={'message':'记住可乐选无糖','request_id':'save'}))['status']=='completed'
    model.correcting=True
    result=payload(client.post(url+'/turns/stream',json={'message':'把刚才的可乐偏好改为小瓶','request_id':'correct'}))
    assert result['status']=='completed',result
    record=result['action_results'][0]['records'][0]
    assert record['revision']==2 and record['content']=='可乐选小瓶'


def test_reference_source_can_be_explicitly_cleared_in_both_runtimes(pi_client,mercury_client):
    client,requests=pi_client
    source='https://example.org/recipe'
    saved=memory_turn(client,requests,'记住来源'+source,{'action':'save','category':'reference','domain':'shopping',
        'key':'recipe','content':'可乐配方参考','source_quote':'记住来源'+source,'reference_url':source},'source')['records'][0]
    updated=memory_turn(client,requests,'更正参考说明并清除来源链接',{'action':'update','memory_id':saved['memory_id'],
        'expected_revision':1,'content':'用户自述参考','source_quote':'更正参考说明并清除来源链接','reference_url':None},'clear')
    assert updated['records'][0]['reference_url'] is None
    from app.mercury.router import get_query_model
    mclient,app,url,sessions=mercury_client
    class Model:
        command={'action':'save','category':'reference','domain':'aftersales','key':'support',
            'content':'售后参考','source_quote':'记住来源'+source,'reference_url':source}
        def chat(self,messages,tools=None): return tool_message('memory_command',json.dumps(self.command,ensure_ascii=False))
        def cancel(self): pass
    model=Model()
    app.dependency_overrides[get_query_model]=lambda:model
    result=payload(mclient.post(url+'/turns/stream',json={'message':'记住来源'+source,'request_id':'source'}))
    record=result['action_results'][0]['records'][0]
    model.command={'action':'update','memory_id':record['memory_id'],'expected_revision':1,'content':'自述',
        'source_quote':'更正参考并清除链接','reference_url':None}
    result=payload(mclient.post(url+'/turns/stream',json={'message':'更正参考并清除链接','request_id':'clear'}))
    assert result['action_results'][0]['records'][0]['reference_url'] is None

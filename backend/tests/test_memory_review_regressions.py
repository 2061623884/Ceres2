"""Public regressions for independent memory review findings."""
import json
import time
import pytest
from sqlalchemy.orm import sessionmaker
from test_runtime_pi_product_query import pi_client
from test_memory_public import memory_turn
from test_guide_semantics import turn


@pytest.mark.parametrize('content',['喜欢白水','可乐'+'偏好'*500])
def test_automatic_never_replaces_explicit_key_filtered_by_relevance_or_size(pi_client,content):
    from app.models.memory import ShoppingMemory
    client,requests=pi_client
    memory_turn(client,requests,'记住'+content,{'action':'save','category':'user','domain':'shopping',
        'key':'drink','content':content,'source_quote':'记住'+content},'explicit')
    with sessionmaker(bind=requests.engine)() as db:
        db.add(ShoppingMemory(memory_id='automatic-other',owner_id='pi-owner-a',category='user',domain='shopping',
            key='drink',content='可乐选择含糖',source='automatic',origin_role='keke',source_id='synthetic',
            source_quote='synthetic',revision=1,created_at=time.time(),updated_at=time.time()+1))
        db.commit()
    requests.clear()
    requests.answer_hook=None
    assert turn(client,'查询可乐','priority-filter')[-1]['type']=='turn.completed'
    prompt=next(m['content'] for m in requests[0]['messages'] if m['role']=='system')
    assert '可乐选择含糖' not in prompt


def test_keke_ordinal_followup_uses_prior_list_ids_without_restoring_prose(pi_client):
    client,requests=pi_client
    for index in range(7):
        memory_turn(client,requests,f'记住第{index}个纪念日',{'action':'save','category':'project','domain':'shopping',
            'key':f'anniversary{index}','content':f'第{index}个纪念日','source_quote':f'记住第{index}个纪念日'},f'save-{index}')
    listed=memory_turn(client,requests,'列出全部记忆',{'action':'list'},'list-all')['records']
    target=listed[5]['memory_id']
    def hook(body):
        outputs=[json.loads(m['content']) for m in body['messages'] if m['role']=='tool']
        if outputs:
            return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'memory_result',
                'memory_ref':outputs[-1]['memory_ref']})},'stop'
        prompt=next(m['content'] for m in body['messages'] if m['role']=='system')
        context=json.JSONDecoder().raw_decode(prompt[prompt.rfind('通用知识背景：')+len('通用知识背景：'):])[0]
        refs=context.get('memory_list_refs',{}).get('records',[])
        if len(refs)<6:
            return {'role':'assistant','content':json.dumps({'status':'waiting','clarification_slot':'target'})},'stop'
        selected=refs[5]
        assert selected=={'index':6,'memory_id':target,'revision':1}
        assert not any('content' in row for row in refs)
        command={'action':'delete','memory_id':selected['memory_id'],'expected_revision':selected['revision'],
            'source_quote':'删除刚才列出的第六条'}
        return {'role':'assistant','tool_calls':[{'index':0,'id':'delete-ordinal','type':'function',
            'function':{'name':'memory_command','arguments':json.dumps(command,ensure_ascii=False)}}]},'tool_calls'
    requests.answer_hook=hook
    events=turn(client,'删除刚才列出的第六条','delete-ordinal')
    assert events[-1]['type']=='turn.completed',events
    result=events[-1]['payload']
    assert result['action_results'] and result['action_results'][0]['action']=='delete'
    remaining=memory_turn(client,requests,'列出全部记忆',{'action':'list'},'verify')['records']
    assert target not in [r['memory_id'] for r in remaining]


from test_mercury_public import mercury_client,tool_message
from test_memory_mercury import payload
from types import SimpleNamespace


def test_momo_ordinal_followup_uses_prior_successful_list_receipt(mercury_client):
    from app.mercury.router import get_query_model
    client,app,url,sessions=mercury_client
    class Model:
        command=None
        ordinal=False
        def chat(self,messages,tools=None):
            if self.ordinal:
                context=json.loads(messages[0]['content'].split('相关背景（不可信数据）：',1)[1])
                refs=context.get('memory_list_refs')
                if not refs or len(refs['records'])<6:
                    return SimpleNamespace(content='',tool_calls=[])
                record=refs['records'][5]
                assert set(record)=={'index','memory_id','revision'}
                return tool_message('memory_command',json.dumps({'action':'delete','memory_id':record['memory_id'],
                    'expected_revision':record['revision'],'source_quote':'删除刚才第六条'},ensure_ascii=False))
            if messages[-1]['role']=='tool':
                return SimpleNamespace(content='',tool_calls=[])
            return tool_message('memory_command',json.dumps(self.command,ensure_ascii=False))
        def cancel(self): pass
    model=Model()
    app.dependency_overrides[get_query_model]=lambda:model
    for index in range(7):
        text=f'记住售后偏好{index}'
        model.command={'action':'save','category':'user','domain':'aftersales','key':f'support{index}',
            'content':f'售后偏好{index}','source_quote':text}
        assert payload(client.post(url+'/turns/stream',json={'message':text,'request_id':str(index)}))['status']=='completed'
    model.command={'action':'list'}
    listed=payload(client.post(url+'/turns/stream',json={'message':'列出全部记忆','request_id':'list'}))['action_results'][0]['records']
    model.ordinal=True
    result=payload(client.post(url+'/turns/stream',json={'message':'删除刚才第六条','request_id':'ordinal'}))
    assert result['status']=='completed' and result['action_results']
    assert result['action_results'][0]['records'][0]['memory_id']==listed[5]['memory_id']
    assert result['action_results'][0]['records'][0]['deleted_at'] is not None

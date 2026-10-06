"""Explicit memory journeys through actual Pi SDK and public HTTP/SSE."""
import json
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn


def memory_hook(command):
    def respond(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return {'role':'assistant','tool_calls':[{'index':0,'id':'memory-1','type':'function','function':{'name':'memory_command','arguments':json.dumps(command,ensure_ascii=False)}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'memory_result','memory_ref':outputs[-1]['memory_ref']})}, 'stop'
    return respond


def memory_turn(client, requests, message, command, request_id):
    requests.answer_hook = memory_hook(command)
    events = turn(client, message, request_id)
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['action_results'], result
    return result['action_results'][0]


def test_chat_explicit_save_and_full_list_have_authoritative_receipts(pi_client):
    client, requests = pi_client
    saved = memory_turn(client, requests, '请记住我喜欢无糖可乐', {
        'action':'save','category':'user','domain':'shopping','key':'drink_preference',
        'content':'喜欢无糖可乐','source_quote':'请记住我喜欢无糖可乐'}, 'memory-save')
    assert saved['action'] == 'save'
    assert saved['records'][0]['content'] == '喜欢无糖可乐'
    assert saved['records'][0]['source'] == 'explicit'
    assert saved['records'][0]['revision'] == 1
    listed = memory_turn(client, requests, '查看我保存的全部记忆', {'action':'list'}, 'memory-list')
    assert [r['memory_id'] for r in listed['records']] == [saved['records'][0]['memory_id']]
    assert client.get('/api/v1/cart').json()['items'] == []


def test_four_categories_correction_delete_and_cross_owner_are_visible_in_chat(pi_client):
    client, requests = pi_client
    saved = []
    for category in ('user','feedback','project','reference'):
        text = f'请记住{category}：可乐选无糖'
        saved.append(memory_turn(client, requests, text, {'action':'save','category':category,
            'domain':'shopping','key':category,'content':f'{category}可乐选无糖','source_quote':text}, category)['records'][0])
    original = saved[0]
    updated = memory_turn(client, requests, '把我的饮料偏好更正为可乐选小瓶', {
        'action':'update','memory_id':original['memory_id'],'expected_revision':1,
        'content':'可乐选小瓶','source_quote':'把我的饮料偏好更正为可乐选小瓶'}, 'correct')['records'][0]
    assert updated['revision'] == 2 and updated['content'] == '可乐选小瓶'
    requests.answer_hook = memory_hook({'action':'delete','memory_id':original['memory_id'],
        'expected_revision':1,'source_quote':'删除这条记忆'})
    assert turn(client,'删除这条记忆','stale')[-1]['type'] == 'error'
    deleted = memory_turn(client, requests, '删除这条记忆', {'action':'delete',
        'memory_id':original['memory_id'],'expected_revision':2,'source_quote':'删除这条记忆'}, 'delete')
    assert deleted['records'][0]['revision'] == 3
    listed = memory_turn(client, requests, '查看全部记忆', {'action':'list'}, 'list-after-delete')
    assert {r['category'] for r in listed['records']} == {'feedback','project','reference'}
    client.cookies.set('sg_owner_id','pi-owner-b')
    from test_guide_lifecycle import BASE
    # Other owner has its own canonical guide entry; never use A's session.
    from test_guide_lifecycle import entry
    other = entry(client).json()
    assert client.get(BASE).status_code == 403
    other_base = '/api/v1/guide/sessions/' + other['session_id']
    requests.answer_hook = memory_hook({'action':'list'})
    state = client.get(other_base).json()
    response = client.post(other_base+'/turns/stream',json={'request_id':'other-list','message':'查看记忆',
        'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version']})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['payload']['action_results'][0]['records'] == []
    requests.answer_hook = memory_hook({'action':'update','memory_id':saved[1]['memory_id'],'expected_revision':1,
        'content':'偷改','source_quote':'请改记忆'})
    response = client.post(other_base+'/turns/stream',json={'request_id':'other-update','message':'请改记忆',
        'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version']})
    assert 'MEMORY_NOT_FOUND' in response.text


def test_expiry_current_conditions_and_role_context_do_not_leak_into_recall(pi_client):
    from test_guide_lifecycle import command
    client, requests = pi_client
    cases = [
        ('shopping','drink','可乐喜欢小瓶',None),
        ('shopping','budget_fen','可乐预算长期20元',None),
        ('aftersales','support','可乐售后只需要邮件','2099-01-01T00:00:00Z'),
        ('shopping','expired','可乐旧偏好不应再用','2000-01-01T00:00:00Z'),
    ]
    for domain,key,content,expiry in cases:
        args = {'action':'save','category':'user','domain':domain,'key':key,'content':content,'source_quote':'记住'+content}
        if expiry: args['expires_at'] = expiry
        memory_turn(client,requests,'记住'+content,args,'save-'+key)
    command(client,'new_goal',goal='买可乐',conditions={'budget_fen':1000})
    requests.clear()
    # Existing controlled SDK product search path reads the same new context.
    requests.answer_hook = None
    events = turn(client,'查询可乐','recall-new-task')
    assert events[-1]['type'] == 'turn.completed', events
    system = '\n'.join(str(m['content']) for m in requests[0]['messages'] if m['role']=='system')
    assert '可乐喜欢小瓶' in system
    assert '可乐预算长期20元' not in system
    assert '可乐售后只需要邮件' not in system
    assert '可乐旧偏好不应再用' not in system
    listed = memory_turn(client,requests,'查看全部记忆',{'action':'list'},'full')
    assert len(listed['records']) == 3, 'Explicit list includes valid aftersales memory, not expired memory'


def test_forged_source_or_owner_fields_never_create_memory(pi_client):
    client, requests = pi_client
    for index, additions in enumerate(({'source_quote':'并非当前用户原文'}, {'source_quote':'记住可乐','owner_id':'pi-owner-b'})):
        requests.answer_hook = memory_hook({'action':'save','category':'user','domain':'shopping',
            'key':'drink','content':'可乐',**additions})
        assert turn(client,'记住可乐',f'forged-{index}')[-1]['type'] == 'error'
    assert memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-forged')['records'] == []


def test_full_list_is_not_bounded_recall(pi_client):
    client, requests = pi_client
    for index in range(7):
        text = f'记住回复偏好第{index}条：简短'
        memory_turn(client,requests,text,{'action':'save','category':'feedback','domain':'communication',
            'key':f'style-{index}','content':f'回复偏好第{index}条：简短','source_quote':text},f'many-{index}')
    listed = memory_turn(client,requests,'列出全部七条记忆',{'action':'list'},'all-seven')
    assert len(listed['records']) == 7
    requests.clear()
    requests.answer_hook = None
    assert turn(client,'查询可乐','bounded')[-1]['type'] == 'turn.completed'
    prompt = next(m['content'] for m in requests[0]['messages'] if m['role']=='system')
    # Parse the public provider context rather than testing a private recall method.
    context = json.JSONDecoder().raw_decode(prompt[prompt.rfind('通用知识背景：')+len('通用知识背景：'):])[0]
    recalled = context['memory']['records']
    assert 0 < len(recalled) <= 5
    assert sum(len(json.dumps(row,ensure_ascii=False)) for row in recalled) <= 2000

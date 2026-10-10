"""Tester-only public HTTP smoke; does not claim browser/UI acceptance."""
import json
import os
from pathlib import Path
import urllib.request

manifest=json.loads(Path(os.environ['FIXTURE_MANIFEST']).read_text())
base=os.environ['BROWSER_BASE_URL']
headers={'Content-Type':'application/json','Cookie':manifest['cookie']['name']+'='+manifest['cookie']['value']}


def request(path,body=None,method=None,stream=False):
    wire=urllib.request.Request(base+path,data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None,
        headers=headers,method=method)
    with urllib.request.urlopen(wire,timeout=25) as response:
        raw=response.read().decode()
    if not stream:
        return json.loads(raw)
    events=[]
    event_name=None
    for line in raw.splitlines():
        if line.startswith('event:'):
            event_name=line[6:].strip()
        elif line.startswith('data: '):
            payload=json.loads(line[6:])
            events.append({'event':event_name,'data':payload} if event_name else payload)
        elif not line:
            event_name=None
    return events


bootstrap=request('/api/v1/bootstrap')
assert bootstrap['owner_id']==manifest['owner_id']
assert {row['order_id'] for row in request('/api/v1/mercury/orders')['orders']}==set(manifest['order_ids'])
state=request('/api/v1/guide/sessions',{'entry_context':{'page':'home','store_id':bootstrap['store_id'],'delivery_zone_id':bootstrap['delivery_zone_id']}})
session=state['session_id'];guide='/api/v1/guide/sessions/'+session;nav='/api/v1/navigation/sessions/'+session
opening=request(nav+'/opening',{'role':'keke'})
summary={}
for scenario in ('interim','mixed','typed'):
    identity='fixture-smoke-'+scenario
    message=manifest['scenarios'][scenario]
    state=request(guide)
    route=request(nav+'/routes',{'request_id':identity,'opening_id':opening['opening_id'],'role':'keke','message':message})
    assert route['status']=='ready',route
    events=request(guide+'/turns/stream',{'request_id':identity,'routing_request_id':identity,'message':message,
        'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],
        'expected_session_version':state['session_version']},stream=True)
    assert events[-1]['type']=='turn.completed',events
    result=events[-1]['payload']
    if scenario=='interim':
        assert sum(row['type']=='message.interim' for row in events)==2,events
    elif scenario=='mixed':
        assert result['navigation_action']['request']['target_role']=='momo'
        assert len(result['messages'])>=3,result
    else:
        assert result['active_question'] is not None,result
    summary[scenario]='passed'
assert request('/api/v1/cart')['items']==[]
request(nav+'/switches',{'opening_id':opening['opening_id'],'target_role':'momo','accept':True})
case=request('/api/v1/mercury/sessions',{})
mercury='/api/v1/mercury/sessions/'+case['session_id']
case=request(mercury)
request(mercury+'/order',{'order_id':manifest['order_ids'][0],'selection_version':case['selection_version']},method='PUT')
events=request(mercury+'/turns/stream',{'message':'查看演示订单详情','request_id':'fixture-mercury-read'},stream=True)
assert events[-1]['event']=='turn.completed',events
assert events[-1]['data']['status']=='completed',events
assert manifest['order_ids'][0] in events[-1]['data']['final_text'],events
assert manifest['product']['name'] in events[-1]['data']['final_text'],events
assert not any(row['event']=='error' for row in events),events
saved=request(mercury)
assert saved['status']=='completed' and saved['tool_rounds']>=1,saved
summary['real_langgraph_order_read']='passed'
print(json.dumps({'backend_fixture_api_smoke':summary,'browser_ui_acceptance':False}),flush=True)

"""Same canonical owner: automatic updates cannot move facts between roles."""
from datetime import datetime, timezone
import json
from types import SimpleNamespace
import pytest
from sqlalchemy.orm import sessionmaker
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn
from test_memory_public import memory_turn
from test_memory_mercury import payload
from test_mercury_public import tool_message
from app.services.memory_background import MemoryWorker


@pytest.mark.parametrize('first_domain,second_domain,accepted',[
    ('shopping','aftersales',False), ('communication','communication',True),
])
def test_actual_role_same_key_keeps_domain_fence_and_truthful_origin(pi_client,tmp_path,monkeypatch,first_domain,second_domain,accepted):
    from app.core.config import get_settings
    from app.main import app
    from app.mercury.models import SimulatedOrder
    from app.mercury.router import get_query_model
    client, requests = pi_client
    first = '喜欢无糖可乐' if first_domain=='shopping' else '回复尽量简短'
    def extract(source):
        is_keke = source['role']=='keke'
        content = first if is_keke else '售后回复先说结论'
        return {'records':[{'category':'user','domain':first_domain if is_keke else second_domain,
            'key':'preference','content':content,'source_quote':content,'scope':'durable'}]}
    worker = MemoryWorker(requests.engine,extract=extract,dream=lambda _: {'records':[]})
    assert turn(client,'我一直'+first,'keke-auto-collision')[-1]['type'] == 'turn.completed'
    assert worker.run_once()
    with sessionmaker(bind=requests.engine)() as db:
        db.add(SimulatedOrder(order_id='role-memory-order',owner_id='pi-owner-a',status='paid',total_fen=350,
            created_at=datetime.now(timezone.utc),snapshot_json=json.dumps({'items':[
                {'sku_id':'pi-cola','name':'测试可乐','unit_price_fen':350,'quantity':1,'returnable':True,'return_policy_source':'synthetic'}]})))
        db.commit()
    monkeypatch.setattr(get_settings(),'mercury_checkpoint_path',tmp_path/'automatic-role-graph.sqlite3')
    class Query:
        def chat(self,messages,tools=None):
            return SimpleNamespace(content='',tool_calls=[]) if messages[-1]['role']=='tool' else tool_message('get_order_details','{"order_id":"role-memory-order"}')
        def cancel(self): pass
    app.dependency_overrides[get_query_model] = Query
    sid=client.post('/api/v1/mercury/sessions').json()['session_id']
    url='/api/v1/mercury/sessions/'+sid
    assert client.put(url+'/order',json={'order_id':'role-memory-order','selection_version':0}).status_code==200
    assert payload(client.post(url+'/turns/stream',json={'message':'查看订单，我一直希望售后回复先说结论',
        'request_id':'momo-auto-collision'}))['status']=='completed'
    assert worker.run_once()
    found=memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-role-collision')['records']
    assert len(found)==1
    assert (found[0]['content'],found[0]['domain'],found[0]['origin_role']) == (
        '售后回复先说结论' if accepted else first, first_domain, 'momo' if accepted else 'keke')

"""Same owner, actual Pi and Mercury entries, isolated canonical order facts."""
from datetime import datetime, timezone
import json
from types import SimpleNamespace
from sqlalchemy.orm import sessionmaker
from test_runtime_pi_product_query import pi_client
from test_memory_public import memory_turn
from test_memory_mercury import payload
from test_mercury_public import tool_message


def test_same_user_keke_memory_is_need_to_know_in_actual_momo_query(pi_client, tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.main import app
    from app.mercury.models import SimulatedOrder
    from app.mercury.router import get_query_model
    client, requests = pi_client
    for domain,key,content in (
        ('shopping','drink','可乐偏好无糖'),
        ('aftersales','contact','订单问题希望先解释原因'),
        ('communication','style','回复先说结论'),
    ):
        memory_turn(client,requests,'请记住'+content,{'action':'save','category':'user','domain':domain,
            'key':key,'content':content,'source_quote':'请记住'+content},key)
    sessions = sessionmaker(bind=requests.engine)
    with sessions() as db:
        db.add(SimulatedOrder(order_id='memory-order',owner_id='pi-owner-a',status='paid',total_fen=350,
            created_at=datetime.now(timezone.utc),snapshot_json=json.dumps({'items':[
                {'sku_id':'pi-cola','name':'测试可乐','unit_price_fen':350,'quantity':1,'returnable':True,'return_policy_source':'synthetic'}]})))
        db.commit()
    monkeypatch.setattr(get_settings(),'mercury_checkpoint_path',tmp_path/'memory-graph.sqlite3')
    class Model:
        seen=[]
        def chat(self,messages,tools=None):
            self.seen.append(messages)
            if messages[-1]['role']=='tool':
                return SimpleNamespace(content='已退款999元',tool_calls=[])
            return tool_message('get_order_details','{"order_id":"memory-order"}')
        def cancel(self): pass
    model=Model()
    app.dependency_overrides[get_query_model]=lambda:model
    sid=client.post('/api/v1/mercury/sessions').json()['session_id']
    url='/api/v1/mercury/sessions/'+sid
    assert client.put(url+'/order',json={'order_id':'memory-order','selection_version':0}).status_code==200
    result=payload(client.post(url+'/turns/stream',json={'message':'查看订单问题','request_id':'recall'}))
    prompt=model.seen[0][0]['content']
    assert '订单问题希望先解释原因' in prompt and '回复先说结论' in prompt
    assert '可乐偏好无糖' not in prompt
    assert '3.50' in result['final_text'] and '测试可乐' in result['final_text']
    assert '999' not in result['final_text'] and '已退款' not in result['final_text']
    assert client.get('/api/v1/cart').json()['items']==[]


def test_explicit_preference_beats_newer_automatic_seed_at_actual_provider_boundary(pi_client):
    import time
    from app.models.memory import ShoppingMemory
    from test_guide_semantics import turn
    client,requests=pi_client
    memory_turn(client,requests,'记住可乐选择无糖',{'action':'save','category':'user','domain':'shopping',
        'key':'drink','content':'可乐选择无糖','source_quote':'记住可乐选择无糖'},'explicit')
    # Synthetic prior persisted data only. TASK10 extraction is not implemented here.
    with sessionmaker(bind=requests.engine)() as db:
        db.add(ShoppingMemory(memory_id='automatic-seed',owner_id='pi-owner-a',category='user',domain='shopping',
            key='drink',content='可乐选择含糖',source='automatic',origin_role='keke',source_id='synthetic-source',
            source_quote='synthetic user source',revision=1,created_at=time.time(),updated_at=time.time()+1,
            expires_at=time.time()+86400))
        db.commit()
    requests.clear()
    requests.answer_hook=None
    assert turn(client,'查询可乐','priority')[-1]['type']=='turn.completed'
    prompt=next(m['content'] for m in requests[0]['messages'] if m['role']=='system')
    assert '可乐选择无糖' in prompt and '可乐选择含糖' not in prompt

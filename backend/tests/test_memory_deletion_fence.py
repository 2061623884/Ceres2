"""An explicit deletion cannot revive an automatic predecessor for that key."""
import time
from sqlalchemy.orm import sessionmaker
from test_runtime_pi_product_query import pi_client
from test_memory_public import memory_turn
from test_guide_semantics import turn


def test_explicit_tombstone_blocks_automatic_predecessor_but_new_explicit_save_wins(pi_client):
    from app.models.memory import ShoppingMemory
    client,requests=pi_client
    with sessionmaker(bind=requests.engine)() as db:
        for key,content in (('drink','可乐选择含糖'),('pack','可乐选择罐装')):
            db.add(ShoppingMemory(memory_id='automatic-'+key,owner_id='pi-owner-a',category='user',domain='shopping',
                key=key,content=content,source='automatic',origin_role='keke',source_id='synthetic-'+key,
                source_quote='synthetic',revision=1,created_at=time.time()-100,updated_at=time.time()-100))
        db.commit()
    saved=memory_turn(client,requests,'记住可乐选择无糖',{'action':'save','category':'user','domain':'shopping',
        'key':'drink','content':'可乐选择无糖','source_quote':'记住可乐选择无糖'},'save')['records'][0]
    memory_turn(client,requests,'删除可乐糖分偏好',{'action':'delete','memory_id':saved['memory_id'],
        'expected_revision':1,'source_quote':'删除可乐糖分偏好'},'delete')
    requests.clear()
    requests.answer_hook=None
    assert turn(client,'查询可乐','after-delete')[-1]['type']=='turn.completed'
    prompt=next(m['content'] for m in requests[0]['messages'] if m['role']=='system')
    assert '可乐选择含糖' not in prompt
    assert '可乐选择无糖' not in prompt
    assert '可乐选择罐装' in prompt, 'Unrelated keys remain usable'
    replacement=memory_turn(client,requests,'重新记住可乐选小瓶',{'action':'save','category':'user','domain':'shopping',
        'key':'drink','content':'可乐选小瓶','source_quote':'重新记住可乐选小瓶'},'replacement')['records'][0]
    assert replacement['memory_id']!=saved['memory_id']
    requests.clear()
    requests.answer_hook=None
    assert turn(client,'查询可乐','after-replacement')[-1]['type']=='turn.completed'
    prompt=next(m['content'] for m in requests[0]['messages'] if m['role']=='system')
    assert '可乐选小瓶' in prompt and '可乐选择含糖' not in prompt
    listed=memory_turn(client,requests,'查看全部有效记忆',{'action':'list'},'valid-list')['records']
    assert saved['memory_id'] not in [row['memory_id'] for row in listed]

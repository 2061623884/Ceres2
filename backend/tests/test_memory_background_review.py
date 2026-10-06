"""Public regressions for independent review's source and publication failures."""
import time
import pytest
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn
from test_memory_public import memory_turn
from app.services.memory_background import MemoryWorker


def test_full_accepted_user_source_keeps_the_trailing_correction(pi_client):
    client, requests = pi_client
    message='我长期喜欢无糖可乐。' + '普通背景。'*850 + '更正：我长期更喜欢无甜味苏打水。'
    assert 4000 < len(message) < 8000
    assert turn(client,message,'long-source-correction')[-1]['type']=='turn.completed'
    seen=[]
    def extract(source):
        seen.append(source['text'])
        content='更喜欢无甜味苏打水' if '更正：' in source['text'] else '喜欢无糖可乐'
        return {'records':[{'category':'user','domain':'shopping','key':'drink','content':content,
            'source_quote':content,'scope':'durable'}]}
    assert MemoryWorker(requests.engine,extract=extract,dream=lambda _: {'records':[]}).run_once()
    found=memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-long-source')['records']
    assert [row['content'] for row in found]==['更喜欢无甜味苏打水']
    assert seen==[message]


def test_publication_sql_fault_propagates_and_remains_recoverable_without_fake_save(pi_client):
    client, requests = pi_client
    now=[time.time()]
    assert turn(client,'我长期喜欢无糖可乐','sql-fault-source')[-1]['type']=='turn.completed'
    def extract(_):
        return {'records':[{'category':'user','domain':'shopping','key':'drink','content':'喜欢无糖可乐',
            'source_quote':'喜欢无糖可乐','scope':'durable'}]}
    failed=[False]
    def reject_one_insert(_connection,_cursor,statement,parameters,_context,_many):
        if statement.startswith('INSERT INTO shopping_memories') and not failed[0]:
            failed[0]=True
            raise OperationalError(statement,(),RuntimeError('controlled storage fault'))
    event.listen(requests.engine,'before_cursor_execute',reject_one_insert)
    try:
        worker=MemoryWorker(requests.engine,extract=extract,dream=lambda _: {'records':[]},clock=lambda:now[0])
        with pytest.raises(OperationalError) as raised:
            worker.run_once()
        assert isinstance(raised.value.orig,RuntimeError)
    finally:
        event.remove(requests.engine,'before_cursor_execute',reject_one_insert)
    assert memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-sql-fault')['records']==[]
    now[0]+=61
    recovered=MemoryWorker(requests.engine,extract=extract,dream=lambda _: {'records':[]},clock=lambda:now[0])
    assert recovered.run_once()
    assert [row['content'] for row in memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-sql-recovery')['records']]==['喜欢无糖可乐']

"""Dream's lease and explicit-edit fences are visible through chat memory CRUD."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn
from test_memory_public import memory_turn
from app.services.memory_background import MemoryWorker


def extract_ten(_):
    return {'records':[{'category':'user','domain':'shopping','key':f'dream-{i}',
        'content':f'长期偏好{i}无糖','source_quote':f'长期偏好{i}无糖','scope':'durable'} for i in range(10)]}


def seed(client, requests, worker):
    assert turn(client,'；'.join(f'长期偏好{i}无糖' for i in range(10)),'ten-dream-source')[-1]['type'] == 'turn.completed'
    assert worker.run_once()
    return memory_turn(client,requests,'查看全部记忆',{'action':'list'},'ten-before-dream')['records']


def test_one_active_dream_and_explicit_correction_win_over_late_organized_result(pi_client):
    client, requests = pi_client
    started, release = threading.Event(), threading.Event()
    calls = []
    def dream(source):
        calls.append(source)
        started.set()
        assert release.wait(8)
        return {'records':[{'memory_id':row['memory_id'],'content':row['content']+'（整理）'} for row in source['records']]}
    worker = MemoryWorker(requests.engine,extract=extract_ten,dream=dream)
    before = seed(client,requests,worker)
    target = next(row for row in before if row['key']=='dream-0')
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(worker.run_once)
        try:
            assert started.wait(2)
            concurrent = MemoryWorker(requests.engine,extract=extract_ten,dream=dream)
            assert not concurrent.run_once(), 'A second active Dream for the owner must not run'
            memory_turn(client,requests,'更正为长期偏好0不再选无糖',{'action':'update',
                'memory_id':target['memory_id'],'expected_revision':target['revision'],
                'content':'长期偏好0不再选无糖','source_quote':'更正为长期偏好0不再选无糖'},'correct-during-dream')
        finally:
            release.set()
        assert pending.result(timeout=3)
    after = memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-late-dream')['records']
    corrected = next(row for row in after if row['memory_id']==target['memory_id'])
    assert corrected['content'] == '长期偏好0不再选无糖' and corrected['source'] == 'explicit'
    assert len(calls) == 1
    assert not any('（整理）' in row['content'] for row in after)


def test_interrupted_dream_recovers_only_after_lease_expiry(pi_client):
    client, requests = pi_client
    now = [time.time()]
    def crash(_):
        raise SystemExit('controlled Dream interruption')
    worker = MemoryWorker(requests.engine,extract=extract_ten,dream=crash,clock=lambda:now[0])
    before = seed(client,requests,worker)
    with pytest.raises(SystemExit):
        worker.run_once()
    calls = []
    def dream(source):
        calls.append(source)
        return {'records':[{'memory_id':source['records'][0]['memory_id'],'content':source['records'][0]['content']+'（整理）'}]}
    recovered = MemoryWorker(requests.engine,extract=extract_ten,dream=dream,clock=lambda:now[0])
    assert not recovered.run_once()
    now[0] += 61
    assert recovered.run_once()
    assert not recovered.run_once()
    after = memory_turn(client,requests,'查看全部记忆',{'action':'list'},'dream-recovered')['records']
    assert sum('（整理）' in row['content'] for row in after) == 1
    assert len(calls) == 1
    assert {row['memory_id']:row['expires_at'] for row in before} == {row['memory_id']:row['expires_at'] for row in after}


def test_failed_dream_does_not_mutate_memories_or_busy_retry_after_restart(pi_client):
    client, requests = pi_client
    calls = []
    def fail(source):
        calls.append(source)
        raise RuntimeError('controlled Dream failure')
    worker = MemoryWorker(requests.engine,extract=extract_ten,dream=fail)
    before = seed(client,requests,worker)
    assert worker.run_once()
    assert not MemoryWorker(requests.engine,extract=extract_ten,dream=fail).run_once()
    after = memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-failed-dream')['records']
    assert after == before
    assert len(calls) == 1


def test_expired_automatic_memories_are_not_counted_for_dream_or_listed(pi_client, monkeypatch):
    from types import SimpleNamespace
    from app.services import memory_service
    client, requests = pi_client
    now = [time.time()]
    calls = []
    worker = MemoryWorker(requests.engine,extract=extract_ten,
        dream=lambda source: calls.append(source) or {'records':[]},clock=lambda:now[0])
    seed(client,requests,worker)
    now[0] += 30 * 86400
    monkeypatch.setattr(memory_service,'time',SimpleNamespace(time=lambda:now[0]))
    assert not worker.run_once()
    assert memory_turn(client,requests,'查看全部记忆',{'action':'list'},'expired-auto-list')['records'] == []
    assert calls == []


def test_unchanged_successful_dream_can_run_again_after_durable_cooldown(pi_client):
    client, requests = pi_client
    now=[time.time()]
    calls=[]
    def unchanged(source):
        calls.append(source)
        return {'records':[]}
    worker=MemoryWorker(requests.engine,extract=extract_ten,dream=unchanged,clock=lambda:now[0])
    before=seed(client,requests,worker)
    assert worker.run_once()
    assert not worker.run_once()
    now[0]+=86400
    assert MemoryWorker(requests.engine,extract=extract_ten,dream=unchanged,clock=lambda:now[0]).run_once()
    assert len(calls)==2
    after=memory_turn(client,requests,'查看全部记忆',{'action':'list'},'unchanged-second-dream')['records']
    assert after==before


def test_explicit_tombstone_shadow_is_excluded_from_dream_threshold_and_model_input(pi_client):
    client, requests=pi_client
    calls=[]
    def dream(source):
        calls.append(source)
        return {'records':[]}
    worker=MemoryWorker(requests.engine,extract=extract_ten,dream=dream)
    seed(client,requests,worker)
    explicit=memory_turn(client,requests,'记住长期偏好0无糖',{'action':'save','category':'user',
        'domain':'shopping','key':'dream-0','content':'长期偏好0无糖','source_quote':'长期偏好0无糖'},'explicit-shadow')['records'][0]
    memory_turn(client,requests,'删除这条记忆',{'action':'delete','memory_id':explicit['memory_id'],
        'expected_revision':explicit['revision'],'source_quote':'删除这条记忆'},'delete-shadow')
    assert not worker.run_once(), 'Ten stored auto rows contain only nine effective non-deleted facts'
    assert calls==[]
    requests.answer_hook=None
    assert turn(client,'长期偏好10无糖','eleventh-for-shadow')[-1]['type']=='turn.completed'
    worker.extract=lambda _: {'records':[{'category':'user','domain':'shopping','key':'dream-10',
        'content':'长期偏好10无糖','source_quote':'长期偏好10无糖','scope':'durable'}]}
    assert worker.run_once()
    assert worker.run_once()
    assert len(calls)==1 and len(calls[0]['records'])==10
    assert all(row['key']!='dream-0' for row in calls[0]['records'])


@pytest.mark.parametrize('change',['delete','expire','automatic_revision'])
def test_reclaimed_dream_validates_captured_facts_before_sending_any_source_to_model(pi_client,change):
    client, requests=pi_client
    now=[time.time()]
    def crash(_): raise SystemExit('controlled process interruption')
    interrupted=MemoryWorker(requests.engine,extract=extract_ten,dream=crash,clock=lambda:now[0])
    before=seed(client,requests,interrupted)
    target=next(row for row in before if row['key']=='dream-0')
    with pytest.raises(SystemExit): interrupted.run_once()
    if change=='delete':
        memory_turn(client,requests,'删除这条记忆',{'action':'delete','memory_id':target['memory_id'],
            'expected_revision':target['revision'],'source_quote':'删除这条记忆'},'delete-before-dream-reclaim')
        now[0]+=61
    elif change=='expire':
        now[0]+=30*86400
    else:
        requests.answer_hook=None
        assert turn(client,'长期偏好0改成小瓶无糖','automatic-change-before-reclaim')[-1]['type']=='turn.completed'
        update=MemoryWorker(requests.engine,extract=lambda _: {'records':[{'category':'user','domain':'shopping',
            'key':'dream-0','content':'长期偏好0改成小瓶无糖','source_quote':'长期偏好0改成小瓶无糖','scope':'durable'}]},
            dream=lambda _: {'records':[]},clock=lambda:now[0])
        assert update.run_once()
        now[0]+=61
    calls=[]
    resumed=MemoryWorker(requests.engine,extract=extract_ten,
        dream=lambda source: calls.append(source) or {'records':[]},clock=lambda:now[0])
    assert resumed.run_once()
    assert calls==[], 'Reclaimed work must not send deleted, expired or replaced captured prose to a model'


def test_recovered_bounded_dream_rechecks_ten_gate_when_an_omitted_record_expires(pi_client):
    client, requests=pi_client
    start=time.time()
    now=[start]
    def extract(source):
        indices=range(9) if '九条' in source['text'] else [9]
        return {'records':[{'category':'user','domain':'shopping','key':f'large-{i}',
            'content':f'长期偏好{i}无糖'+'偏好说明'*490+('。' if '再次' in source['text'] else ''),
            'source_quote':f'长期偏好{i}无糖','scope':'durable'} for i in indices]}
    captured=[]
    def crash(source):
        captured.append(source)
        raise SystemExit('controlled bounded Dream interruption')
    worker=MemoryWorker(requests.engine,extract=extract,dream=crash,clock=lambda:now[0])
    assert turn(client,'长期偏好9无糖','older-expiring-auto')[-1]['type']=='turn.completed'
    assert worker.run_once()
    now[0]+=60
    assert turn(client,'九条：'+'；'.join(f'长期偏好{i}无糖' for i in range(9)),'newer-nine-auto')[-1]['type']=='turn.completed'
    assert worker.run_once()
    now[0]+=60
    assert turn(client,'再次表达长期偏好9无糖','older-auto-reordered')[-1]['type']=='turn.completed'
    assert worker.run_once()
    # The earlier row is newest by updated_at but keeps its earlier expiry.
    # Large controlled contents force the 20k model-context subset to omit it.
    with pytest.raises(SystemExit): worker.run_once()
    assert len(captured)==1 and len(captured[0]['records'])<10
    assert all(row['key']!='large-9' for row in captured[0]['records'])
    now[0]=start+30*86400+1
    calls=[]
    resumed=MemoryWorker(requests.engine,extract=extract,
        dream=lambda source:calls.append(source) or {'records':[]},clock=lambda:now[0])
    assert resumed.run_once()
    assert calls==[], 'Reclaim must enforce ten effective records, even when all captured subset rows remain live'

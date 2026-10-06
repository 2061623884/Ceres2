"""Recover durable sources and preserve user decisions through public chat."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn
from test_memory_public import memory_turn
from app.services.memory_background import MemoryWorker


def candidate(content='喜欢无糖可乐', **changes):
    return {'category':'user','domain':'shopping','key':'drink', 'content':content,
        'source_quote':'喜欢无糖可乐','scope':'durable', **changes}


def records(client, requests, request_id):
    return memory_turn(client,requests,'查看全部记忆',{'action':'list'},request_id)['records']


def test_duplicate_source_and_crash_recover_once_after_expired_lease(pi_client):
    client, requests = pi_client
    now = [time.time()]
    for _ in range(2):
        assert turn(client,'我平时喜欢无糖可乐','retry-source')[-1]['type'] == 'turn.completed'
    def crash(_):
        raise SystemExit('simulated process interruption before commit')
    interrupted = MemoryWorker(requests.engine,extract=crash,dream=lambda _: {'records':[]},clock=lambda:now[0])
    with pytest.raises(SystemExit):
        interrupted.run_once()
    calls = []
    def extract(source):
        calls.append(source)
        return {'records':[candidate()]}
    restarted = MemoryWorker(requests.engine,extract=extract,dream=lambda _: {'records':[]},clock=lambda:now[0])
    assert not restarted.run_once(), 'A live lease cannot be stolen'
    now[0] += 61
    assert restarted.run_once()
    assert not restarted.run_once()
    assert len(calls) == 1
    assert [r['content'] for r in records(client,requests,'after-recovery')] == ['喜欢无糖可乐']


def test_stale_worker_cannot_publish_after_an_expired_lease_is_reclaimed(pi_client):
    client, requests = pi_client
    now = [time.time()]
    assert turn(client,'我平时喜欢无糖可乐，小瓶','lease-source')[-1]['type'] == 'turn.completed'
    started, release = threading.Event(), threading.Event()
    def old_extract(_):
        started.set()
        assert release.wait(8)
        return {'records':[candidate()]}
    old = MemoryWorker(requests.engine,extract=old_extract,dream=lambda _: {'records':[]},clock=lambda:now[0])
    new = MemoryWorker(requests.engine,extract=lambda _: {'records':[candidate('喜欢小瓶无糖可乐')]},
        dream=lambda _: {'records':[]},clock=lambda:now[0])
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(old.run_once)
        try:
            assert started.wait(2)
            now[0] += 61
            assert new.run_once()
        finally:
            release.set()
        assert pending.result(timeout=3)
    assert [r['content'] for r in records(client,requests,'after-lease-reclaim')] == ['喜欢小瓶无糖可乐']


def test_model_failure_does_not_report_saved_or_retry_unchanged_failed_source(pi_client):
    client, requests = pi_client
    events = turn(client,'我平时喜欢无糖可乐','failed-auto-source')
    assert events[-1]['type'] == 'turn.completed'
    assert '已记住' not in events[-1]['payload']['message']
    calls = []
    def failing(source):
        calls.append(source)
        raise RuntimeError('controlled model failure')
    worker = MemoryWorker(requests.engine,extract=failing,dream=lambda _: {'records':[]})
    assert worker.run_once()
    assert not worker.run_once()
    assert len(calls) == 1
    assert records(client,requests,'after-auto-failure') == []


def test_four_categories_reject_assistant_claims_current_conditions_and_foreign_domains(pi_client):
    client, requests = pi_client
    source = '我平时喜欢无糖可乐；请长期先说结论；持续准备周末露营；参考链接 https://example.com/guide；今天预算20元，两个人'
    assert turn(client,source,'four-category-source')[-1]['type'] == 'turn.completed'
    output = [candidate(),
        candidate('长期先说结论',category='feedback',domain='communication',key='style',source_quote='请长期先说结论'),
        candidate('持续准备周末露营',category='project',key='camping',source_quote='持续准备周末露营'),
        candidate('参考露营资料',category='reference',key='guide',source_quote='参考链接 https://example.com/guide',reference_url='https://example.com/guide'),
        candidate('助手建议买大瓶',key='assistant',source_quote='助手建议买大瓶'),
        candidate('预算20元',key='budget_fen',source_quote='今天预算20元'),
        candidate('两个人',key='people',source_quote='两个人'),
        candidate('今天预算20元',key='temporary',source_quote='今天预算20元',scope='current'),
        candidate('喜欢无糖可乐',key='foreign-role',domain='aftersales'),
        candidate('伪造参考链接',category='reference',key='forged-link',reference_url='https://example.com/forged')]
    worker = MemoryWorker(requests.engine,extract=lambda _: {'records':output},dream=lambda _: {'records':[]})
    assert worker.run_once()
    found = records(client,requests,'all-four-categories')
    assert {r['category'] for r in found} == {'user','feedback','project','reference'}
    assert len(found) == 4
    assert all(r['source']=='automatic' and r['origin_role']=='keke' for r in found)


def test_unchanged_reextraction_does_not_renew_ttl_or_revision(pi_client):
    client, requests = pi_client
    now = [time.time()]
    worker = MemoryWorker(requests.engine,extract=lambda _: {'records':[candidate()]},
        dream=lambda _: {'records':[]},clock=lambda:now[0])
    assert turn(client,'我平时喜欢无糖可乐','ttl-source-one')[-1]['type'] == 'turn.completed'
    assert worker.run_once()
    first = records(client,requests,'ttl-before')[0]
    now[0] += 86400
    requests.answer_hook = None
    assert turn(client,'我平时喜欢无糖可乐','ttl-source-two')[-1]['type'] == 'turn.completed'
    assert worker.run_once()
    second = records(client,requests,'ttl-after')[0]
    assert (second['memory_id'],second['revision'],second['expires_at'],second['source_id']) == (
        first['memory_id'],first['revision'],first['expires_at'],first['source_id'])

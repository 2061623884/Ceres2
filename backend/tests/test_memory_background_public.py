"""Post-reply extraction observed through the actual Pi chat memory list."""
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn
from test_memory_public import memory_turn


def test_completed_chat_recovers_extraction_and_lists_automatic_memory(pi_client):
    from app.services.memory_background import MemoryWorker
    client, requests = pi_client
    events = turn(client, '我平时一直喜欢无糖可乐，查询可乐', 'automatic-source')
    assert events[-1]['type'] == 'turn.completed'
    assert '已记住' not in events[-1]['payload']['messages'][0]['content']
    calls = []
    def extract(payload):
        calls.append(payload)
        return {'records': [{'category':'user','domain':'shopping','key':'drink_preference',
            'content':'喜欢无糖可乐','source_quote':'我平时一直喜欢无糖可乐','scope':'durable',
            'reference_url':None}]}
    worker = MemoryWorker(requests.engine, extract=extract, dream=lambda _: {'records':[]})
    assert worker.run_once()
    listed = memory_turn(client, requests, '查看全部记忆', {'action':'list'}, 'automatic-list')
    assert [(r['content'],r['source']) for r in listed['records']] == [('喜欢无糖可乐','automatic')]
    record = listed['records'][0]
    assert record['expires_at'] - record['created_at'] == 30 * 86400
    assert len(calls) == 1


def test_dream_waits_for_ten_valid_automatic_records_and_twenty_four_hours(pi_client):
    import time
    from app.services.memory_background import MemoryWorker
    client, requests = pi_client
    now = [time.time()]
    dreams = []
    def extract(source):
        indices = range(9) if '首批' in source['text'] else [9] if '第十' in source['text'] else [10]
        return {'records':[{'category':'user','domain':'shopping','key':f'preference-{i}',
            'content':f'长期偏好{i}无糖','source_quote':f'长期偏好{i}无糖','scope':'durable'} for i in indices]}
    def dream(source):
        dreams.append(source)
        row = next(row for row in source['records'] if row['key'] == 'preference-0')
        return {'records':[{'memory_id':row['memory_id'],'content':'长期偏好0：无糖'}]}
    worker = MemoryWorker(requests.engine, extract=extract, dream=dream, clock=lambda:now[0])
    text = '首批：' + '；'.join(f'长期偏好{i}无糖' for i in range(9))
    assert turn(client, text, 'dream-nine')[-1]['type'] == 'turn.completed'
    assert worker.run_once()
    assert not worker.run_once(), 'Nine valid records must not start Dream'
    assert dreams == []
    assert turn(client, '第十：长期偏好9无糖', 'dream-ten')[-1]['type'] == 'turn.completed'
    assert worker.run_once()
    before = memory_turn(client,requests,'查看全部记忆',{'action':'list'},'before-dream')['records']
    assert worker.run_once(), 'Ten valid automatic records must permit the first Dream'
    after = memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-dream')['records']
    assert next(r for r in after if r['key']=='preference-0')['content'] == '长期偏好0：无糖'
    assert {r['memory_id']:r['expires_at'] for r in after} == {r['memory_id']:r['expires_at'] for r in before}
    assert len(dreams) == 1
    requests.answer_hook = None
    assert turn(client, '新增：长期偏好10无糖', 'dream-eleven')[-1]['type'] == 'turn.completed'
    assert worker.run_once()
    assert not worker.run_once(), 'A successful Dream starts a durable 24-hour cooldown'
    now[0] += 86400
    restarted = MemoryWorker(requests.engine, extract=extract, dream=dream, clock=lambda:now[0])
    assert restarted.run_once()
    assert len(dreams) == 2


def test_application_worker_does_not_hold_main_reply_while_extraction_is_running(pi_client, monkeypatch):
    import threading
    import time
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.core.database import get_db
    from app.services import memory_model
    original, requests = pi_client
    started, release = threading.Event(), threading.Event()
    def extract(source):
        started.set()
        assert release.wait(8)
        return {'records':[{'category':'user','domain':'shopping','key':'drink',
            'content':'喜欢无糖可乐','source_quote':'喜欢无糖可乐','scope':'durable'}]}
    monkeypatch.setattr(memory_model,'extract_memory',extract)
    monkeypatch.setattr(memory_model,'dream_memory',lambda _: {'records':[]})
    app = create_app(requests.engine)
    app.dependency_overrides[get_db] = original.app.dependency_overrides[get_db]
    with TestClient(app) as client:
        client.cookies.set('sg_owner_id','pi-owner-a')
        try:
            events = turn(client,'我平时喜欢无糖可乐','managed-extraction')
            assert events[-1]['type'] == 'turn.completed'
            assert started.wait(3), 'Application startup must run the durable memory worker'
            assert not release.is_set(), 'Main reply completed while the independent model is blocked'
            assert memory_turn(client,requests,'查看记忆',{'action':'list'},'before-release')['records'] == []
        finally:
            release.set()
        until = time.monotonic() + 4
        records = []
        attempt = 0
        while not records and time.monotonic() < until:
            attempt += 1
            records = memory_turn(client,requests,'查看记忆',{'action':'list'},f'after-release-{attempt}')['records']
            if not records:
                time.sleep(0.05)
        assert [r['content'] for r in records] == ['喜欢无糖可乐']


def test_late_extraction_cannot_recreate_deleted_fact_under_another_key(pi_client):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from app.services.memory_background import MemoryWorker
    client, requests = pi_client
    saved = memory_turn(client,requests,'请记住我喜欢无糖可乐',{'action':'save','category':'user',
        'domain':'shopping','key':'drink','content':'喜欢无糖可乐','source_quote':'喜欢无糖可乐'},'fence-save')['records'][0]
    requests.answer_hook = None
    assert turn(client,'我平时喜欢无糖可乐，查询可乐','late-source')[-1]['type'] == 'turn.completed'
    started, release = threading.Event(), threading.Event()
    def extract(source):
        started.set()
        assert release.wait(8)
        return {'records':[{'category':'user','domain':'shopping','key':'different-model-key',
            'content':'喜欢无糖可乐','source_quote':'喜欢无糖可乐','scope':'durable'}]}
    worker = MemoryWorker(requests.engine,extract=extract,dream=lambda _: {'records':[]})
    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(worker.run_once)
        try:
            assert started.wait(2)
            memory_turn(client,requests,'删除这条记忆',{'action':'delete','memory_id':saved['memory_id'],
                'expected_revision':saved['revision'],'source_quote':'删除这条记忆'},'delete-during-extraction')
        finally:
            release.set()
        assert result.result(timeout=3)
    assert memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-late-source')['records'] == []


def test_application_restart_drains_preexisting_pending_source_without_duplicate_save(pi_client, monkeypatch):
    import time
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.core.database import get_db
    from app.services import memory_model
    original, requests = pi_client
    assert turn(original,'我平时喜欢无糖可乐','before-process-restart')[-1]['type'] == 'turn.completed'
    calls = []
    def extract(source):
        calls.append(source)
        return {'records':[{'category':'user','domain':'shopping','key':'drink','content':'喜欢无糖可乐',
            'source_quote':'喜欢无糖可乐','scope':'durable'}]}
    monkeypatch.setattr(memory_model,'extract_memory',extract)
    monkeypatch.setattr(memory_model,'dream_memory',lambda _: {'records':[]})
    snapshots = []
    for generation in range(2):
        app = create_app(requests.engine)
        app.dependency_overrides[get_db] = original.app.dependency_overrides[get_db]
        with TestClient(app) as restarted:
            restarted.cookies.set('sg_owner_id','pi-owner-a')
            records = []
            until = time.monotonic() + 4
            attempt = 0
            while not records and time.monotonic() < until:
                attempt += 1
                records = memory_turn(restarted,requests,'查看全部记忆',{'action':'list'},f'restarted-{generation}-{attempt}')['records']
                if not records: time.sleep(0.05)
            assert [row['content'] for row in records] == ['喜欢无糖可乐']
            snapshots.append(records)
    assert snapshots[0] == snapshots[1]
    assert len(calls) == 1

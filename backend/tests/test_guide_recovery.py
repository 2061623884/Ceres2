"""Public startup recovery with synthetic former-process rows; no provider retry."""
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.guide import GuideTurnReceipt
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE


def test_restart_marks_dead_process_only_and_preserves_committed_result(pi_client):
    _client, requests = pi_client
    from app.services.guide_run_service import BOOT_ID, EXECUTION_ID
    with Session(requests.engine) as db:
        for run_id, state, incarnation in [('dead-run', 'running', f'{BOOT_ID}:99999999:0'), ('live-run', 'running', EXECUTION_ID), ('saved-run', 'completed', f'{BOOT_ID}:99999999:0')]:
            db.add(GuideTurnReceipt(run_id=run_id, owner_id='pi-owner-a', session_id='pi-session-a', request_id=run_id, digest='fixture', status=state, execution_id=incarnation, result_json=json.dumps({'message': '保留结果'}) if state == 'completed' else None))
        db.commit()
    from app.main import create_app
    from app.core.database import get_db
    app = create_app(requests.engine)
    def database():
        with Session(requests.engine) as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as restarted:
        restarted.cookies.set('sg_owner_id', 'pi-owner-a')
        assert restarted.get(BASE + '/turns/dead-run').json()['status'] == 'interrupted'
        assert restarted.get(BASE + '/turns/live-run').json()['status'] == 'running'
        assert restarted.get(BASE + '/turns/saved-run').json()['result'] == {'message': '保留结果'}
        events = restarted.get(BASE + '/runs/dead-run/events').json()['events']
        assert events[-1]['payload']['code'] == 'RUN_INTERRUPTED'
    assert len(requests) == 0


def test_waiting_run_has_distinct_durable_status_and_task_stays_active(pi_client):
    client, _ = pi_client
    from test_guide_lifecycle import command
    state = command(client, 'new_goal', goal='选可乐').json()
    client.post(BASE + '/turns/stream', json={'request_id': 'waiting-run', 'message': '帮我选可乐包装', 'expected_task_id': state['task_id'], 'expected_state_version': 0, 'expected_session_version': state['session_version']})
    assert client.get(BASE + '/turns/waiting-run').json()['status'] == 'waiting_clarification'
    assert client.get(BASE).json()['task_status'] == 'active'


def test_app_shutdown_fences_and_drains_its_own_inflight_run(pi_client):
    _client, requests = pi_client
    import time
    from app.main import create_app
    from app.core.database import get_db
    app = create_app(requests.engine)
    def database():
        with Session(requests.engine) as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as live:
        live.cookies.set('sg_owner_id', 'pi-owner-a')
        accepted = live.post(BASE + '/runs', json={'request_id': 'shutdown-run', 'message': '受控慢查询可乐', 'expected_state_version': 0, 'expected_session_version': 0})
        assert accepted.status_code == 202
        assert requests.started.wait(timeout=5)
        start = time.monotonic()
    assert time.monotonic() - start < 3
    receipt = _client.get(BASE + '/turns/shutdown-run').json()
    assert receipt['status'] == 'interrupted'
    assert receipt['result']['code'] == 'RUN_INTERRUPTED'
    assert len(requests) == 1
    requests.release.set()


def test_shutdown_rejects_new_admission_without_orphan_running_receipt(pi_client):
    client, requests = pi_client
    from app.main import create_app
    from app.core.database import get_db
    app = create_app(requests.engine)
    def database():
        with Session(requests.engine) as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app):
        pass
    rejected = client.post(BASE + '/runs', json={'request_id':'after-shutdown','message':'查可乐','expected_state_version':0,'expected_session_version':0})
    assert rejected.status_code == 503
    assert client.get(BASE + '/turns/after-shutdown').status_code == 404
    assert len(requests) == 0


def test_shutdown_cancels_even_when_sqlite_writer_blocks_interruption_record(pi_client):
    client, requests = pi_client
    import sqlite3
    import time
    from app.main import create_app
    from app.core.database import get_db
    app = create_app(requests.engine)
    def database():
        with Session(requests.engine) as db:
            yield db
    app.dependency_overrides[get_db] = database
    blocker = sqlite3.connect(requests.engine.url.database, check_same_thread=False)
    try:
        with TestClient(app) as live:
            live.cookies.set('sg_owner_id', 'pi-owner-a')
            accepted = live.post(BASE + '/runs', json={'request_id':'contended-shutdown','message':'受控慢查询可乐','expected_state_version':0,'expected_session_version':0})
            assert accepted.status_code == 202
            assert requests.started.wait(timeout=5)
            blocker.execute('BEGIN IMMEDIATE')
            # The SQL lock deliberately outlasts the allowed cleanup wait.
            release = __import__('threading').Timer(2, blocker.commit)
            release.start()
            started = time.monotonic()
        elapsed = time.monotonic() - started
        release.join()
        assert elapsed < 1.5, 'Shutdown cancellation cannot wait for this writer'
        # A same-process app restart must flush the deferred interruption once
        # SQLite accepts writes, never restart its model exploration.
        with TestClient(app) as reopened:
            reopened.cookies.set('sg_owner_id', 'pi-owner-a')
            result = reopened.get(BASE + '/turns/contended-shutdown').json()
            assert result['status'] == 'interrupted'
            assert result['result']['code'] == 'RUN_INTERRUPTED'
        assert len(requests) == 1
    finally:
        requests.release.set()
        blocker.close()

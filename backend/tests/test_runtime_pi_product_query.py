"""Public SSE slice: real Pi SDK, deterministic HTTP model boundary, isolated DB."""
import json
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def pi_client(tmp_path, monkeypatch):
    class ModelRequests(list):
        def __init__(self):
            super().__init__()
            self.started = threading.Event()
            self.release = threading.Event()
            self.answer_hook = None
    requests = ModelRequests()

    class ModelHandler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            prompt_text = json.dumps([m['content'] for m in body['messages'] if m['role'] == 'user'], ensure_ascii=False)
            if '模型连接中断' in prompt_text:
                self.close_connection = True
                self.connection.close()
                return
            if '模型伪造状态文本' in prompt_text:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                self.wfile.write(b'data: {"error":{"message":"401 offline-fixture-key private provider message"}}\n\ndata: [DONE]\n\n')
                return
            if '模型认证失败' in prompt_text:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': {'message': 'authorization rejected offline-fixture-key private provider message', 'type': 'invalid_api_key', 'code': 'invalid_api_key'}}).encode())
                return
            tool_messages = [m for m in body['messages'] if m['role'] == 'tool']
            if '受控慢查询' in prompt_text:
                requests.started.set()
                requests.release.wait(timeout=25)
            override = requests.answer_hook(body) if requests.answer_hook else None
            if override is not None:
                delta, reason = override
            elif '未查询空选择' in prompt_text or (tool_messages and ('有匹配空选择' in prompt_text or '无匹配空选择' in prompt_text)):
                delta = {'role': 'assistant', 'content': json.dumps({'status': 'completed', 'product_refs': []})}
                reason = 'stop'
            elif '无匹配空选择' in prompt_text:
                delta = {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'empty-search-1', 'type': 'function', 'function': {'name': 'search_products', 'arguments': json.dumps({'query': '不存在商品XYZ'})}}]}
                reason = 'tool_calls'
            elif '伪造等待价格' in prompt_text:
                delta = {'role': 'assistant', 'content': json.dumps({'status': 'waiting', 'clarification_slot': 'packaging', 'question': '可乐仅需0.01元，已替你加购。'})}
                reason = 'stop'
            elif '越权写工具' in prompt_text:
                delta = {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'write-1', 'type': 'function', 'function': {'name': 'add_to_cart', 'arguments': json.dumps({'sku_id': 'pi-cola', 'quantity': 1})}}]}
                reason = 'tool_calls'
            elif '伪造详情引用' in prompt_text:
                delta = {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'forged-1', 'type': 'function', 'function': {'name': 'product_details', 'arguments': json.dumps({'ref': 'other-owner-product'})}}]}
                reason = 'tool_calls'
            elif '伪造回复引用' in prompt_text:
                delta = {'role': 'assistant', 'content': json.dumps({'status': 'completed', 'product_refs': ['other-owner-product']})}
                reason = 'stop'
            elif '错误回复形状' in prompt_text:
                delta = {'role': 'assistant', 'content': '[]'}
                reason = 'stop'
            elif any('帮我选可乐包装' in json.dumps(m.get('content'), ensure_ascii=False) for m in body['messages'] if m['role'] == 'user'):
                delta = {'role': 'assistant', 'content': json.dumps({'status': 'waiting', 'product_refs': [], 'clarification_slot': 'packaging', 'question': '你想看罐装还是瓶装可乐？'})}
                reason = 'stop'
            elif any('一直查可乐' in json.dumps(m.get('content'), ensure_ascii=False) for m in body['messages'] if m['role'] == 'user'):
                delta = {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': f'search-{len(tool_messages)}', 'type': 'function', 'function': {'name': 'search_products', 'arguments': json.dumps({'query': '可乐'})}}]}
                reason = 'tool_calls'
            elif not tool_messages and any('查饮料品类' in json.dumps(m.get('content'), ensure_ascii=False) for m in body['messages'] if m['role'] == 'user'):
                delta = {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'category-1', 'type': 'function', 'function': {'name': 'search_products', 'arguments': json.dumps({'category_id': 'beverage'})}}]}
                reason = 'tool_calls'
            elif not tool_messages:
                delta = {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'search-1', 'type': 'function', 'function': {'name': 'search_products', 'arguments': json.dumps({'query': '可乐'})}}]}
                reason = 'tool_calls'
            elif len(tool_messages) == 1:
                search = json.loads(tool_messages[0]['content'])
                ref = search['products'][0]['ref']
                delta = {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': 'detail-1', 'type': 'function', 'function': {'name': 'product_details', 'arguments': json.dumps({'ref': ref})}}]}
                reason = 'tool_calls'
            else:
                detail = json.loads(tool_messages[-1]['content'])
                delta = {'role': 'assistant', 'content': json.dumps({'status': 'completed', 'product_refs': [detail['product']['ref']]})}
                reason = 'stop'
            try:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.end_headers()
                for d, stop in [(delta, None), ({}, reason)]:
                    chunk = {'id': 'controlled-1', 'object': 'chat.completion.chunk', 'created': 1780000000, 'model': 'controlled-pi', 'choices': [{'index': 0, 'delta': d, 'finish_reason': stop}]}
                    self.wfile.write(('data: ' + json.dumps(chunk) + '\n\n').encode())
                self.wfile.write(b'data: [DONE]\n\n')
            except (BrokenPipeError, ConnectionResetError):
                # The real Node worker is killed on explicit stop/deadline.
                pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), ModelHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv('OPENAI_BASE_URL', f'http://127.0.0.1:{server.server_port}/v1')
    monkeypatch.setenv('OPENAI_API_KEY', 'offline-fixture-key')
    monkeypatch.setenv('LLM_MODEL', 'controlled-pi')
    monkeypatch.setenv('SOURCE_DATABASE_PATH', str(tmp_path / 'unused-source.sqlite3'))
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path}/runtime.sqlite3')
    from app.core.config import get_settings
    get_settings.cache_clear()
    from app.core.database import Base, get_db, create_db_engine
    from app.models.identity import Owner
    from app.models.guide import GuideSession
    from app.models.catalog import CatalogProduct
    from app.models.store import Store, Offer
    engine = create_db_engine(f'sqlite:///{tmp_path}/runtime.sqlite3')
    Base.metadata.create_all(engine)
    requests.engine = engine
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add_all([Owner(id='pi-owner-a'), Owner(id='pi-owner-b'), Store(store_id='pi-store', name='隔离模拟店', delivery_zone_id='zone-default'), CatalogProduct(sku_id='pi-cola', name='Cola', name_zh='测试可乐', category_id='beverage', spec_quantity=330, spec_unit='ml')])
        db.flush()
        from app.models.cart import Cart
        db.add(Cart(owner_id='pi-owner-a', store_id='pi-store', version=1))
        db.add(Offer(store_id='pi-store', sku_id='pi-cola', price_fen=350, available_qty=7))
        for owner in ('a', 'b'):
            db.add(GuideSession(session_id=f'pi-session-{owner}', owner_id=f'pi-owner-{owner}', entry_context_json=json.dumps({'page': 'home', 'store_id': 'pi-store', 'delivery_zone_id': 'zone-default'})))
        db.commit()
    def database():
        with sessions() as db:
            yield db
    from app.main import app
    app.dependency_overrides[get_db] = database
    # No lifespan: the production startup must never touch an active data path.
    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set('sg_owner_id', 'pi-owner-a')
    yield client, requests
    requests.release.set()
    # A failing concurrency assertion must not leave a live worker using this
    # fixture's transport/database after teardown. Stop then consume terminal.
    from app.models.guide import GuideTurnReceipt
    from sqlalchemy import select
    with sessions() as db:
        pending = [(row.owner_id, row.session_id, row.request_id, row.run_id) for row in db.scalars(select(GuideTurnReceipt).where(GuideTurnReceipt.status.in_(['running', 'stop_requested']), GuideTurnReceipt.started_at.is_not(None)))]
    for owner_id, session_id, request_id, run_id in pending:
        client.cookies.set('sg_owner_id', owner_id)
        client.post(f'/api/v1/guide/sessions/{session_id}/turns/stop', json={'request_id': request_id})
        until = time.monotonic() + 3
        while time.monotonic() < until:
            state = client.get(f'/api/v1/guide/sessions/{session_id}/turns/{request_id}').json()['status']
            if state not in ('running', 'stop_requested'):
                break
            time.sleep(0.03)
    client.close()
    app.dependency_overrides.clear()
    server.shutdown()
    server.server_close()
    engine.dispose()
    get_settings.cache_clear()


def test_product_query_uses_pi_search_then_details_and_persists_grounded_reply(pi_client):
    client, requests = pi_client
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-query-1', 'message': '查一下可乐的规格和价格', 'expected_task_id': None, 'expected_state_version': 0, 'expected_session_version': 0})
    assert response.status_code == 200
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['runtime'] == 'pi-agent-core'
    assert result['tool_rounds'] == 2
    assert result['runtime_status'] == 'completed'
    assert '测试可乐' in result['message']
    assert '3.50' in result['message']
    assert '330' in result['message']
    assert '模拟' in result['message']
    assert len(requests) == 3
    assert any(event['type'] == 'tool_execution_end' for event in result['runtime_events'])
    history = client.get('/api/v1/guide/sessions/pi-session-a/messages').json()
    assert any('测试可乐' in message['content'] for message in history['messages'])


def test_pi_can_finish_early_waiting_for_the_users_packaging_choice(pi_client):
    client, requests = pi_client
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-wait-1', 'message': '帮我选可乐包装', 'expected_state_version': 0, 'expected_session_version': 0})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    result = events[-1]['payload']
    assert events[-1]['type'] == 'turn.completed', events
    assert result['runtime_status'] == 'waiting'
    assert result['message'] == '你想看罐装还是瓶装，还是其他包装？'
    assert result['tool_rounds'] == 0
    assert len(requests) == 1


def test_pi_stops_at_five_tool_rounds_without_a_summary_model_call(pi_client):
    client, requests = pi_client
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-bound-1', 'message': '一直查可乐', 'expected_state_version': 0, 'expected_session_version': 0})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['runtime_status'] == 'tool_budget'
    assert result['tool_rounds'] == 5
    assert len(requests) == 5
    assert '5 轮' in result['message']
    assert '测试可乐' in result['message']
    assert result['answer_status'] == 'failed'


def test_pi_can_query_a_product_category_without_a_name_keyword(pi_client):
    client, requests = pi_client
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-category-1', 'message': '查饮料品类', 'expected_state_version': 0, 'expected_session_version': 0})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['runtime_status'] == 'completed'
    assert '测试可乐' in result['message']
    assert result['product_evidence'][0]['category_id'] == 'beverage'
    assert len(requests) == 3


@pytest.mark.parametrize(('message', 'code'), [
    ('越权写工具', 'PI_TOOL_FORBIDDEN'),
    ('伪造详情引用', 'PI_UNKNOWN_REFERENCE'),
    ('伪造回复引用', 'PI_UNKNOWN_REFERENCE'),
    ('错误回复形状', 'PI_ANSWER_INVALID'),
])
def test_untrusted_model_output_cannot_escape_read_only_contract(pi_client, message, code):
    client, requests = pi_client
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-untrusted-1', 'message': message, 'expected_state_version': 0, 'expected_session_version': 0})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error', events
    assert events[-1]['payload']['code'] == code
    assert len(requests) == 1
    assert client.get('/api/v1/guide/sessions/pi-session-a/messages').json()['messages'] == []


def test_pi_receipts_replay_only_for_the_same_owner_session_and_body(pi_client):
    client, requests = pi_client
    created = client.post('/api/v1/guide/sessions', json={'entry_context': {'page': 'home', 'store_id': 'pi-store', 'delivery_zone_id': 'zone-default'}})
    assert created.status_code == 200, created.text
    session_id = created.json()['session_id']
    path = f'/api/v1/guide/sessions/{session_id}/turns/stream'
    body = {'request_id': 'pi-replay-1', 'message': '查可乐', 'expected_state_version': 0, 'expected_session_version': 0}
    original = client.post(path, json=body)
    original_events = [json.loads(line[6:]) for line in original.text.splitlines() if line.startswith('data: ')]
    assert original_events[-1]['type'] == 'turn.completed', original_events
    replay = client.post(path, json=body)
    replay_events = [json.loads(line[6:]) for line in replay.text.splitlines() if line.startswith('data: ')]
    assert replay_events[-1]['payload'] == original_events[-1]['payload']
    assert len(requests) == 3
    changed = client.post(path, json={**body, 'message': '另一种商品'})
    changed_events = [json.loads(line[6:]) for line in changed.text.splitlines() if line.startswith('data: ')]
    assert changed_events[-1]['payload']['code'] == 'IDEMPOTENCY_CONFLICT'
    assert len(requests) == 3
    client.cookies.set('sg_owner_id', 'pi-owner-b')
    assert client.post(path, json=body).status_code == 403
    assert client.get(f'/api/v1/guide/sessions/{session_id}/messages').status_code == 403
    assert client.post(f'/api/v1/guide/sessions/{session_id}/turns/stop', json={'request_id': 'pi-replay-1'}).status_code == 403
    assert len(requests) == 3
    own = client.post('/api/v1/guide/sessions/pi-session-b/turns/stream', json=body)
    own_events = [json.loads(line[6:]) for line in own.text.splitlines() if line.startswith('data: ')]
    assert own_events[-1]['type'] == 'turn.completed', own_events
    assert own_events[-1]['payload']['product_evidence'][0]['ref'] != original_events[-1]['payload']['product_evidence'][0]['ref']
    assert len(requests) == 6


def test_explicit_stop_kills_inflight_pi_query_without_a_late_product_reply(pi_client):
    client, requests = pi_client
    body = {'request_id': 'pi-stop-1', 'message': '受控慢查询可乐', 'expected_state_version': 0, 'expected_session_version': 0}
    with ThreadPoolExecutor(max_workers=1) as worker:
        future = worker.submit(client.post, '/api/v1/guide/sessions/pi-session-a/turns/stream', json=body)
        assert requests.started.wait(timeout=5)
        stopped_at = time.monotonic()
        stop = client.post('/api/v1/guide/sessions/pi-session-a/turns/stop', json={'request_id': 'pi-stop-1'})
        assert stop.status_code == 200
        assert stop.json()['cancelled'] is True
        response = future.result(timeout=3)
        assert time.monotonic() - stopped_at < 3
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.stopped', events
    assert events[-1]['payload']['runtime_status'] == 'stopped'
    assert events[-1]['payload']['tool_rounds'] == 0
    requests.release.set()
    assert len(requests) == 1
    history = client.get('/api/v1/guide/sessions/pi-session-a/messages').json()['messages']
    assert not any('测试可乐' in row['content'] for row in history)
    assert client.get('/api/v1/guide/sessions/pi-session-a').status_code == 200


def test_pi_deadline_closes_inflight_provider_at_fifteen_seconds_without_retry(pi_client):
    client, requests = pi_client
    started_at = time.monotonic()
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-deadline-1', 'message': '受控慢查询可乐', 'expected_state_version': 0, 'expected_session_version': 0})
    elapsed = time.monotonic() - started_at
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['runtime_status'] == 'deadline'
    assert result['tool_rounds'] == 0
    assert result['answer_status'] == 'failed'
    assert '15 秒' in result['message']
    assert 14.5 <= elapsed < 18
    assert len(requests) == 1
    requests.release.set()


def test_provider_failure_has_safe_diagnostic_correlation_without_secret_text(pi_client):
    client, requests = pi_client
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-provider-failure', 'message': '模型认证失败', 'expected_state_version': 0, 'expected_session_version': 0})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error', events
    assert events[-1]['payload']['code'] == 'PI_PROVIDER_ERROR'
    assert 'HTTP_401' in events[-1]['payload']['message']
    assert 'pi-' in events[-1]['payload']['message']
    assert 'offline-fixture-key' not in response.text
    assert 'private provider message' not in response.text
    assert len(requests) == 1
    diagnostic = events[-1]['payload']['diagnostic']
    assert diagnostic['upstream_http_status'] == 401
    assert diagnostic['transport_phase'] == 'response'
    assert diagnostic['code'] == 'HTTP_401'
    assert diagnostic['kind'] == 'ProviderError'
    assert len(diagnostic['fingerprint']) == 64
    receipt = client.get('/api/v1/guide/sessions/pi-session-a/turns/pi-provider-failure').json()
    assert receipt['result']['diagnostic'] == diagnostic


@pytest.mark.parametrize('prompt, expected_phase, expected_status', [
    ('模型连接中断', 'fetch_error', None),
    ('模型伪造状态文本', 'response', 200),
])
def test_provider_transport_diagnostic_uses_observed_facts_not_error_prose(pi_client, prompt, expected_phase, expected_status):
    client, requests = pi_client
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id':'transport-facts', 'message':prompt, 'expected_state_version':0, 'expected_session_version':0})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error', events
    diagnostic = events[-1]['payload']['diagnostic']
    assert diagnostic['transport_phase'] == expected_phase
    assert diagnostic['upstream_http_status'] == expected_status
    assert diagnostic['code'] != 'HTTP_401'
    if expected_phase == 'fetch_error':
        assert diagnostic['transport_error_class'] == 'TypeError'
        assert diagnostic['transport_error_code'] in ('UND_ERR_SOCKET', 'ECONNRESET')
    assert 'offline-fixture-key' not in response.text
    assert 'private provider message' not in response.text
    assert len(requests) == 1


def test_waiting_cannot_publish_model_fabricated_price_or_completed_cart_claim(pi_client):
    client, requests = pi_client
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-waiting-attack', 'message': '伪造等待价格', 'expected_state_version': 0, 'expected_session_version': 0})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    assert events[-1]['payload']['runtime_status'] == 'waiting'
    assert events[-1]['payload']['message'] == '你想看罐装还是瓶装，还是其他包装？'
    assert '0.01' not in response.text
    assert '已替你加购' not in response.text
    history = client.get('/api/v1/guide/sessions/pi-session-a/messages').json()['messages']
    assert not any('0.01' in row['content'] or '已替你加购' in row['content'] for row in history)
    assert len(requests) == 1


@pytest.mark.parametrize('case', ['未查询空选择', '有匹配空选择', '无匹配空选择'])
def test_empty_model_selection_is_not_misreported_as_empty_catalog_evidence(pi_client, case):
    client, requests = pi_client
    response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-empty-selection', 'message': case, 'expected_state_version': 0, 'expected_session_version': 0})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    if case == '未查询空选择':
        assert events[-1]['type'] == 'error', events
        assert events[-1]['payload']['code'] == 'PI_EVIDENCE_MISSING'
        assert len(requests) == 1
    else:
        assert events[-1]['type'] == 'turn.completed', events
        message = events[-1]['payload']['message']
        if case == '有匹配空选择':
            assert '已查询到商品' in message
            assert '没有查到' not in message
        else:
            assert '没有查到匹配商品' in message
        assert len(requests) == 2


def test_spent_http_admission_budget_cannot_start_a_fresh_pi_exploration(pi_client, tmp_path):
    client, requests = pi_client
    # External infrastructure fault: hold the actual isolated SQLite write lock,
    # so receipt admission takes longer than the accepted request's 15s budget.
    blocker = sqlite3.connect(tmp_path / 'runtime.sqlite3', check_same_thread=False)
    blocker.execute('BEGIN IMMEDIATE')
    release = threading.Timer(16, blocker.commit)
    release.start()
    started_at = time.monotonic()
    try:
        response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-delayed-admission', 'message': '受控慢查询可乐', 'expected_state_version': 0, 'expected_session_version': 0})
    finally:
        release.join()
        blocker.close()
        requests.release.set()
    elapsed = time.monotonic() - started_at
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    assert events[-1]['payload']['runtime_status'] == 'deadline'
    assert len(requests) == 0
    # The blocked DB itself needs 16s to return; there is no fresh exploration
    # after it releases and no promise that a blocked DB response ends at 15s.
    assert elapsed < 19


def test_changed_session_revision_fences_a_slow_pi_reply(pi_client):
    client, requests = pi_client
    with ThreadPoolExecutor(max_workers=1) as worker:
        future = worker.submit(client.post, '/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-stale-query', 'message': '受控慢查询可乐', 'expected_state_version': 0, 'expected_session_version': 0})
        assert requests.started.wait(timeout=5)
        changed = client.post('/api/v1/guide/sessions/pi-session-a/supply-context', json={'request_id': 'supply-revision-1', 'store_id': 'pi-store', 'delivery_zone_id': 'changed-zone', 'expected_session_version': 0})
        assert changed.status_code == 200, changed.text
        assert changed.json()['session_version'] == 1
        response = future.result(timeout=3)
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error', events
    assert events[-1]['payload']['code'] == 'STALE_STATE'
    requests.release.set()
    assert len(requests) == 1
    assert client.get('/api/v1/guide/sessions/pi-session-a/messages').json()['messages'] == []
    assert client.get('/api/v1/guide/sessions/pi-session-a').json()['session_version'] == 1


def test_competing_revision_at_first_history_write_cannot_commit_stale_pi_answer(pi_client):
    from sqlalchemy import event
    client, requests = pi_client
    at_write = threading.Event()
    release_write = threading.Event()

    def pause_first_session_write(_conn, _cursor, statement, _parameters, _context, _many):
        # Approved transaction/driver fault seam, independent of Pi helper
        # methods: pause the final session/task-anchor CAS before SQLite
        # executes it. TASK03 also locks the session during admission; that
        # no-op admission lock is not the final history transaction.
        normalized = ' '.join(statement.lower().split())
        if normalized.startswith('update guide_sessions') and 'guide_sessions.current_task_id' in normalized and not at_write.is_set():
            at_write.set()
            assert release_write.wait(timeout=5)

    event.listen(requests.engine, 'before_cursor_execute', pause_first_session_write)
    try:
        with ThreadPoolExecutor(max_workers=1) as worker:
            future = worker.submit(client.post, '/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-commit-fence', 'message': '查可乐', 'expected_state_version': 0, 'expected_session_version': 0})
            try:
                assert at_write.wait(timeout=5)
                changed = client.post('/api/v1/guide/sessions/pi-session-a/supply-context', json={'request_id': 'supply-commit-race', 'store_id': 'pi-store', 'delivery_zone_id': 'changed-zone', 'expected_session_version': 0})
                assert changed.status_code == 200, changed.text
                assert changed.json()['session_version'] == 1
            finally:
                release_write.set()
            response = future.result(timeout=3)
    finally:
        event.remove(requests.engine, 'before_cursor_execute', pause_first_session_write)
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error', events
    assert events[-1]['payload']['code'] == 'STALE_STATE'
    assert len(requests) == 3
    assert client.get('/api/v1/guide/sessions/pi-session-a/messages').json()['messages'] == []
    assert client.get('/api/v1/guide/sessions/pi-session-a').json()['session_version'] == 1


def test_actual_pi_stdio_contract_emits_sdk_events_and_scoped_tool_requests(pi_client):
    import os
    import selectors
    import subprocess
    from pathlib import Path
    from app.core.config import get_settings

    _client, requests = pi_client
    settings = get_settings()
    script = Path(__file__).resolve().parents[2] / 'runtime' / 'pi' / 'dist' / 'worker.js'
    child = subprocess.Popen(['node', str(script)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, env={'PATH': os.environ['PATH']})
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ)
    frames = []
    terminal = None
    product = {'ref': 'ipc-proof-product', 'sku_id': 'ipc-cola', 'name_zh': '协议可乐', 'price_fen': 350}

    input_sequence = 0

    def send(frame):
        nonlocal input_sequence
        input_sequence += 1
        child.stdin.write((json.dumps({**frame, 'run_id': 'ipc-proof-run', 'sequence': input_sequence}) + '\n').encode())

    try:
        send({'type': 'start', 'message': '协议查可乐', 'categories': [{'id': 'beverage', 'name_zh': '饮料'}], 'model': {'id': settings.llm_model, 'baseUrl': settings.openai_base_url, 'apiKey': settings.openai_api_key}, 'maxToolRounds': 5, 'timeoutMs': 15000})
        until = time.monotonic() + 10
        while time.monotonic() < until:
            if not selector.select(timeout=0.2):
                continue
            line = child.stdout.readline()
            assert line, frames
            frame = json.loads(line)
            frames.append(frame)
            if frame['type'] == 'tool_call':
                assert set(frame['arguments']).issubset({'query', 'category_id', 'ref'})
                if frame['name'] == 'search_products':
                    assert frame['round'] == 1
                    result = {'products': [product], 'total': 1, 'is_demo': True}
                else:
                    assert frame['name'] == 'product_details'
                    assert frame['round'] == 2
                    assert frame['arguments']['ref'] == product['ref']
                    result = {'product': product, 'is_demo': True}
                send({'type': 'tool_result', 'id': frame['id'], 'result': result})
            elif frame['type'] in ('result', 'error'):
                terminal = frame
                break
        assert terminal is not None, frames
        assert all(frame['run_id'] == 'ipc-proof-run' for frame in frames)
        assert [frame['sequence'] for frame in frames] == list(range(1, len(frames) + 1))
        assert terminal['type'] == 'result', terminal
        assert terminal['status'] == 'completed'
        assert json.loads(terminal['answer'])['product_refs'] == [product['ref']]
        events = [frame['event']['type'] for frame in frames if frame['type'] == 'event']
        assert events[0] == 'agent_start'
        assert events[-1] == 'agent_end'
        assert events.count('tool_execution_end') == 2
        assert len(requests) == 3
        assert settings.openai_api_key not in json.dumps(frames)
    finally:
        selector.close()
        if child.poll() is None:
            child.kill()
        child.wait()
        child.stdin.close()
        child.stdout.close()
        child.stderr.close()


def test_unexpected_host_failure_preserves_safe_correlation_without_raw_cause(pi_client, caplog):
    import hashlib
    from sqlalchemy import event
    client, requests = pi_client
    secret_cause = 'private-host-failure do-not-log-provider-token'

    def fail_catalog_read(_conn, _cursor, statement, _parameters, _context, _many):
        if 'SELECT catalog_products.category_id' in statement:
            raise RuntimeError(secret_cause)

    event.listen(requests.engine, 'before_cursor_execute', fail_catalog_read)
    try:
        response = client.post('/api/v1/guide/sessions/pi-session-a/turns/stream', json={'request_id': 'pi-host-fault', 'message': '查可乐', 'expected_state_version': 0, 'expected_session_version': 0})
    finally:
        event.remove(requests.engine, 'before_cursor_execute', fail_catalog_read)
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error'
    assert events[-1]['payload']['code'] == 'PI_QUERY_FAILED'
    run_id = events[-1]['run_id']
    assert run_id in caplog.text
    assert hashlib.sha256(secret_cause.encode()).hexdigest() in caplog.text
    assert secret_cause not in caplog.text
    assert secret_cause not in response.text
    assert len(requests) == 0
    assert client.get('/api/v1/guide/sessions/pi-session-a/messages').json()['messages'] == []

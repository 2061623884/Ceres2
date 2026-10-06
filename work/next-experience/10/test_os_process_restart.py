"""Tester-only bounded Linux OS restart probe; no production patches or real providers."""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

# run_controlled.py sets cwd to the selected candidate's backend directory.
ROOT = Path.cwd().resolve().parent
assert Path.cwd().resolve() == ROOT / 'backend', 'Launch via the candidate controlled runner'
assert Path(__file__).resolve().parents[3] == ROOT, 'Harness must belong to the selected candidate'
CHILD = r'''
import os, sys, ipaddress

def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)) and os.path.basename(os.fsdecode(args[0])).startswith('.env'):
        raise RuntimeError('Restart probe forbids dotenv access')
    if event in ('socket.connect', 'socket.bind') and isinstance(args[1], tuple):
        host = args[1][0]
        if host != 'localhost' and not ipaddress.ip_address(host).is_loopback:
            raise RuntimeError('Restart probe requires loopback')
    if event == 'socket.getaddrinfo':
        host = args[0]
        if host not in ('localhost', b'localhost', None):
            if isinstance(host, bytes): host = host.decode()
            if not ipaddress.ip_address(host).is_loopback:
                raise RuntimeError('Restart probe requires loopback DNS')
sys.addaudithook(guard)
from app.core.config import Settings, get_settings
Settings.model_config['env_file'] = None
get_settings.cache_clear()
from app.core.database import init_db, SessionLocal
init_db()
from app.services.seed_service import seed_catalog
with SessionLocal.begin() as db:
    seed_catalog(db)
from app.main import app
import uvicorn
uvicorn.run(app, fd=int(sys.argv[1]), log_level='warning')
'''


def test_real_process_restart_preserves_checkout_and_interrupts_inflight_run(tmp_path):
    """Kill only our process group, relaunch against its DB, observe public APIs."""
    entered = threading.Event()
    release = threading.Event()
    calls = []
    transcript = []
    children = []
    logs = []

    class Fixture(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            calls.append({'path': self.path, 'body': body})
            if self.path == '/v1/systemone':
                criteria = body['questions']['service']['criteria']
                result = {'model': 'kev-latest', 'answers': {'service': {
                    'type': 'choice', 'choice': 'keke_exploration',
                    'probabilities': {key: float(key == 'keke_exploration') for key in criteria}}}}
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
            if body['model'] == 'restart-memory-fixture':
                content = json.dumps({'records': []})
            else:
                if not entered.is_set():
                    entered.set()
                    release.wait(timeout=45)
                content = json.dumps({'status': 'waiting', 'product_refs': [],
                                      'clarification_slot': 'packaging', 'question': '请选择包装'})
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            try:
                for delta, finish in [({'role': 'assistant', 'content': content}, None), ({}, 'stop')]:
                    chunk = {'id': 'restart-fixture', 'object': 'chat.completion.chunk',
                             'created': 1780000000, 'model': body['model'],
                             'choices': [{'index': 0, 'delta': delta, 'finish_reason': finish}]}
                    self.wfile.write(('data: ' + json.dumps(chunk) + '\n\n').encode())
                self.wfile.write(b'data: [DONE]\n\n')
            except (BrokenPipeError, ConnectionResetError):
                pass  # Intentional process-group death closes the pending fixture socket.

    fixture = ThreadingHTTPServer(('127.0.0.1', 0), Fixture)
    threading.Thread(target=fixture.serve_forever, daemon=True).start()
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    environment = {
        'PATH': os.environ['PATH'], 'HOME': str(tmp_path), 'TMPDIR': str(tmp_path),
        'PYTHONPATH': str(ROOT / 'backend'), 'DATABASE_URL': f'sqlite:///{tmp_path}/probe.sqlite3',
        'MERCURY_CHECKPOINT_PATH': str(tmp_path / 'checkpoints.sqlite3'),
        'OPENAI_BASE_URL': f'http://127.0.0.1:{fixture.server_port}/v1',
        'KEV_BASE_URL': f'http://127.0.0.1:{fixture.server_port}',
        'OPENAI_API_KEY': 'offline-fixture-key', 'LLM_MODEL': 'restart-pi-fixture',
        'LLM_MODE': 'live', 'MEMORY_EXTRACTION_MODEL': 'restart-memory-fixture',
        'MEMORY_DREAM_MODEL': 'restart-memory-fixture', 'HUMAN_OPERATOR_TOKEN': '',
        'SHOPPING_WRITES_PAUSED': 'false', 'BUSINESS_DATA_MODE': 'demo',
        'NO_PROXY': '127.0.0.1,localhost,::1', 'no_proxy': '127.0.0.1,localhost,::1',
    }
    client = httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=4, trust_env=False)

    def launch():
        log_path = tmp_path / f'process-{len(children)}.log'
        log = log_path.open('w')
        logs.append((log, log_path))
        process = subprocess.Popen([sys.executable, '-c', CHILD, str(listener.fileno())],
                                   cwd=tmp_path, env=environment, pass_fds=(listener.fileno(),),
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        children.append(process)
        transcript.append({'launch_pid': process.pid})
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            assert process.poll() is None, log_path.read_text()
            try:
                if client.get('/health', timeout=.3).status_code == 200:
                    return process
            except httpx.TransportError:
                pass
            time.sleep(.05)
        raise AssertionError('Isolated subprocess did not become ready')

    def request(method, path, body=None, expected=200):
        response = client.request(method, path, json=body)
        transcript.append({'method': method, 'path': path, 'body': body,
                           'status': response.status_code, 'response': response.json()})
        assert response.status_code == expected, response.text
        return response.json()

    try:
        first = launch()
        bootstrap = request('GET', '/api/v1/bootstrap')
        cart = request('GET', '/api/v1/cart')
        cart = request('POST', '/api/v1/cart/items', {'sku_id': 'demo:flour-all-purpose-500g',
                       'quantity': 2, 'expected_cart_version': cart['version']})
        preview = request('POST', '/api/v1/checkout/preview', {'expected_cart_version': cart['version']})
        confirmation = {'preview_id': preview['preview_id'], 'idempotency_key': 'restart-checkout', 'confirmed': True}
        receipt = request('POST', '/api/v1/checkout/confirm', confirmation)
        session = request('POST', '/api/v1/guide/sessions', {'entry_context': {
            'page': 'home', 'store_id': bootstrap['store_id'], 'delivery_zone_id': bootstrap['delivery_zone_id']}})
        base = '/api/v1/guide/sessions/' + session['session_id']
        body = {'request_id': 'interrupted-by-real-process-death', 'message': '帮我选可乐包装',
                'expected_task_id': session['task_id'], 'expected_state_version': session['state_version'],
                'expected_session_version': session['session_version']}
        admitted = request('POST', base + '/runs', body, 202)
        assert entered.wait(15), 'The real Pi worker never reached the loopback fixture'
        assert request('GET', base + '/turns/' + body['request_id'])['status'] == 'running'
        os.killpg(first.pid, signal.SIGKILL)
        assert first.wait(timeout=5) == -signal.SIGKILL
        transcript.append({'killed_pid': first.pid, 'returncode': first.returncode})
        release.set()
        before_relaunch = len(calls)
        second = launch()
        assert second.pid != first.pid
        recovered = request('GET', base + '/turns/' + body['request_id'])
        assert recovered['status'] == 'interrupted'
        assert recovered['result']['code'] == 'RUN_INTERRUPTED'
        events_path = base + '/runs/' + admitted['run_id'] + '/events'
        events = request('GET', events_path)
        assert events['events'][-1]['payload']['code'] == 'RUN_INTERRUPTED'
        assert request('POST', base + '/runs', body, 202)['run_id'] == admitted['run_id']
        assert request('GET', events_path) == events
        assert len(calls) == before_relaunch, 'Recovery/replay unexpectedly invoked a provider'
        assert request('POST', '/api/v1/checkout/confirm', confirmation) == receipt
        assert request('GET', '/api/v1/orders/' + receipt['order']['order_id']) == receipt['order']
        assert len(request('GET', '/api/v1/orders')['items']) == 1
        assert request('GET', '/api/v1/cart')['items'] == []
        current = request('GET', base)
        resumed_body = {**body, 'request_id': 'explicit-new-turn-after-restart',
                        'expected_task_id': current['task_id'], 'expected_state_version': current['state_version'],
                        'expected_session_version': current['session_version']}
        request('POST', base + '/runs', resumed_body, 202)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            resumed = request('GET', base + '/turns/' + resumed_body['request_id'])
            if resumed['status'] != 'running':
                break
            time.sleep(.1)
        assert resumed['status'] == 'waiting_clarification', resumed
        assert len(request('GET', '/api/v1/orders')['items']) == 1
        assert request('GET', '/api/v1/cart')['items'] == []
    finally:
        release.set()
        client.close()
        for process in children:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        listener.close()
        fixture.shutdown()
        fixture.server_close()
        print(json.dumps({'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                          'transcript': transcript, 'fixture_requests': calls}, ensure_ascii=False))
        for log, path in logs:
            log.close()
            print(path.name + '\n' + path.read_text())

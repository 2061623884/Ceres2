"""The isolated Kev baseline launcher is observable through public HTTP only."""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_DIR = ROOT / 'work/local-followup/04/kev-followup-20261009'


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        return listener.getsockname()[1]


def test_kev_baseline_launcher_uses_isolated_seed_and_selected_config_via_public_http(tmp_path):
    source_env = tmp_path / 'approved-fields.env'
    source_env.write_text(
        'OPENAI_BASE_URL=http://127.0.0.1:9/v1\n'
        'OPENAI_API_KEY=synthetic-source-key\n'
        'LLM_MODEL=synthetic-source-model\n'
        'LLM_MODE=live\n'
        'MEMORY_EXTRACTION_MODEL=synthetic-memory-extract\n'
        'MEMORY_DREAM_MODEL=synthetic-memory-dream\n',
        encoding='utf-8',
    )

    legacy_database = tmp_path / 'legacy.sqlite3'
    legacy_checkpoint = tmp_path / 'legacy-checkpoints.sqlite3'
    legacy_database.write_bytes(b'synthetic legacy database sentinel')
    legacy_checkpoint.write_bytes(b'synthetic legacy checkpoint sentinel')
    legacy_database_before = legacy_database.read_bytes()
    legacy_checkpoint_before = legacy_checkpoint.read_bytes()

    kev_calls = []

    class ControlledKevHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            kev_calls.append(payload)
            purpose = next(iter(payload['questions']))
            answer = {
                'model': 'kev-latest',
                'answers': {purpose: {
                    'type': 'choice',
                    'choice': 'yes',
                    'probabilities': {'yes': 1.0, 'no': 0.0, 'uncertain': 0.0},
                }},
            }
            body = json.dumps(answer).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format, *_args):
            return

    kev_server = ThreadingHTTPServer(('127.0.0.1', 0), ControlledKevHandler)
    kev_thread = threading.Thread(target=kev_server.serve_forever, daemon=True)
    kev_thread.start()

    api_port = _free_port()
    isolated_runtime = tmp_path / 'runtime' / 'baseline'
    child_source = '''
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import serve_baseline as launcher
launcher.SOURCE_ENV = Path(sys.argv[2])
launcher.RUNTIME = Path(sys.argv[3])
launcher.API_PORT = int(sys.argv[4])
launcher.KEV_BASE_URL = sys.argv[5]
raise SystemExit(launcher.main())
'''
    child_env = {
        'PATH': os.environ.get('PATH', ''),
        'HOME': os.environ['HOME'],
        'LANG': 'C.UTF-8',
        'NO_PROXY': '127.0.0.1,localhost,::1',
        'no_proxy': '127.0.0.1,localhost,::1',
        'DATABASE_URL': f'sqlite:///{legacy_database}',
        'MERCURY_CHECKPOINT_PATH': str(legacy_checkpoint),
        'KEV_BASE_URL': 'http://127.0.0.1:1',
        'OPENAI_BASE_URL': 'http://127.0.0.1:1/v1',
        'OPENAI_API_KEY': 'inherited-host-key-sentinel',
        'LLM_MODEL': 'inherited-host-model-sentinel',
        'LLM_MODE': 'invalid-host-mode',
        'HUMAN_OPERATOR_TOKEN': 'inherited-operator-token-sentinel',
        'SHOPPING_WRITES_PAUSED': 'true',
    }
    process = subprocess.Popen(
        [sys.executable, '-c', child_source, str(LAUNCHER_DIR), str(source_env),
         str(isolated_runtime), str(api_port),
         f'http://127.0.0.1:{kev_server.server_port}'],
        cwd=ROOT,
        env=child_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    client = httpx.Client(timeout=0.5)
    captured_output = ''
    try:
        base_url = f'http://127.0.0.1:{api_port}'
        ready_by = time.monotonic() + 12
        health = None
        while time.monotonic() < ready_by:
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                captured_output += stdout + stderr
                pytest.fail(f'isolated launcher exited before HTTP readiness: {stderr or stdout}')
            try:
                response = client.get(base_url + '/health')
                if response.status_code == 200:
                    health = response.json()
                    break
            except httpx.TransportError:
                time.sleep(0.05)
            else:
                time.sleep(0.05)
        assert health is not None, 'isolated launcher did not become ready on its public API'
        assert health['llm_configured'] is True
        assert health['business_data_mode'] == 'demo'

        bootstrap = client.get(base_url + '/api/v1/bootstrap')
        assert bootstrap.status_code == 200, bootstrap.text
        assert bootstrap.json()['store_id'] == 'store-demo-01'
        assert bootstrap.json()['llm_mode'] == 'live'

        catalog = client.get(base_url + '/api/v1/products', params={'page_size': 500})
        assert catalog.status_code == 200, catalog.text
        assert any(item['sku_id'] == 'demo:cn-coke-original-330ml-can'
                   for item in catalog.json()['items'])

        protected = client.get(
            base_url + '/api/v1/mercury/operator/tickets',
            headers={'X-Internal-Token': 'inherited-operator-token-sentinel'},
        )
        assert protected.status_code == 403

        context = {
            'page': 'home', 'store_id': bootstrap.json()['store_id'],
            'delivery_zone_id': bootstrap.json()['delivery_zone_id'],
        }
        guide = client.post('/'.join((base_url, 'api/v1/guide/sessions')),
                            json={'entry_context': context})
        assert guide.status_code == 200, guide.text
        session_id = guide.json()['session_id']
        route_base = f'{base_url}/api/v1/navigation/sessions/{session_id}'
        opening = client.post(route_base + '/opening', json={'role': 'keke'})
        assert opening.status_code == 200, opening.text
        routed = client.post(route_base + '/routes', json={
            'request_id': 'kev-launcher-public-route',
            'opening_id': opening.json()['opening_id'],
            'role': 'keke',
            'message': '查询这笔订单退款资格',
        })
        assert routed.status_code == 200, routed.text
        assert routed.json()['status'] == 'switch'
        assert len(kev_calls) == 1
        assert kev_calls[0]['state']['message'] == '查询这笔订单退款资格'
        assert next(iter(kev_calls[0]['questions'])) == 'service'
    finally:
        client.close()
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                stdout, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            captured_output += stdout + stderr
        else:
            stdout, stderr = process.communicate()
            captured_output += stdout + stderr
        kev_server.shutdown()
        kev_server.server_close()
        kev_thread.join(timeout=5)
    assert not kev_thread.is_alive()
    assert 'synthetic-source-key' not in captured_output
    assert 'inherited-host-key-sentinel' not in captured_output
    assert legacy_database.read_bytes() == legacy_database_before
    assert legacy_checkpoint.read_bytes() == legacy_checkpoint_before

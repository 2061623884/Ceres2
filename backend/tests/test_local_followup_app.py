"""Public baseline CLI against the real FastAPI app and controlled Pi HTTP model."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time

import httpx
import uvicorn
from sqlalchemy.orm import sessionmaker

from test_runtime_pi_product_query import pi_client


def test_baseline_cli_captures_real_public_waiting_run_with_controlled_pi(tmp_path, pi_client):
    _test_client, model_requests = pi_client
    from app.core.database import get_db
    from app.services.seed_service import seed_catalog

    sessions = sessionmaker(bind=model_requests.engine)
    with sessions.begin() as db:
        seed_catalog(db)

    def fixture_database():
        with sessions() as db:
            yield db

    application = _test_client.app
    application.dependency_overrides[get_db] = fixture_database

    cases = {
        'schema_version': 'ceres-local-followup-dev-cases-v1',
        'version': 'controlled-real-app-smoke-v1',
        'cases': [{
            'case_id': 'public-cola-packaging',
            'category': 'product_selection',
            'core': False,
            'message': '帮我选可乐包装',
        }],
    }
    cases_path = tmp_path / 'cases.json'
    cases_path.write_text(json.dumps(cases, ensure_ascii=False), encoding='utf-8')
    output_path = tmp_path / 'batch.json'

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(('127.0.0.1', 0))
    listener.listen()
    port = listener.getsockname()[1]
    app_server = uvicorn.Server(uvicorn.Config(application, log_level='error', lifespan='off'))
    server_thread = threading.Thread(
        target=lambda: app_server.run(sockets=[listener]), daemon=True,
    )
    server_thread.start()
    try:
        startup_deadline = time.monotonic() + 5
        while not app_server.started and time.monotonic() < startup_deadline:
            time.sleep(0.01)
        assert app_server.started, 'The fixture-backed FastAPI TCP server did not start.'

        command = [
            sys.executable, '-m', 'app.evaluation.run_baseline',
            '--api-base', f'http://127.0.0.1:{port}',
            '--cases', str(cases_path), '--output', str(output_path),
        ]
        process = subprocess.run(
            command,
            cwd=Path(__file__).resolve().parents[1],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=45,
        )
        assert process.returncode == 0, process.stderr

        batch = json.loads(output_path.read_text(encoding='utf-8'))
        assert batch['schema_version'] == 'ceres-local-followup-batch-v1'
        assert len(batch['cases']) == 1
        record = batch['cases'][0]
        capture = record['capture']
        request_id = 'public-cola-packaging:trial:1'
        assert record['outcome'] == 'guide_run'
        assert capture['schema_version'] == 'ceres-eval-capture-v2'
        assert capture['request_id'] == request_id
        assert capture['status'] == 'waiting_clarification'
        assert capture['owner_id'] not in {'pi-owner-a', 'pi-owner-b'}
        assert capture['runtime_version'] is not None
        assert len(model_requests) == 1
        assert model_requests[0]['model'] == 'controlled-pi'
        assert any(
            '帮我选可乐包装' in str(message['content'])
            for message in model_requests[0]['messages']
            if message['role'] == 'user'
        )

        with httpx.Client(
            base_url=f'http://127.0.0.1:{port}',
            cookies={'sg_owner_id': capture['owner_id']},
            timeout=10,
        ) as public_client:
            bootstrap = public_client.get('/api/v1/bootstrap')
            assert bootstrap.status_code == 200
            assert bootstrap.json()['owner_id'] == capture['owner_id']
            assert bootstrap.json()['store_id'] == 'store-demo-01'

            session = public_client.get(f"/api/v1/guide/sessions/{capture['session_id']}")
            assert session.status_code == 200
            assert session.json()['session_id'] == capture['session_id']
            assert session.json()['pending_clarifications']

            cart = public_client.get('/api/v1/cart')
            assert cart.status_code == 200
            assert cart.json()['items'] == []

            receipt = public_client.get(
                f"/api/v1/guide/sessions/{capture['session_id']}/turns/{request_id}"
            )
            assert receipt.status_code == 200
            public_version = receipt.json()['result']['runtime_version']
            version_fields = (
                'source_revision', 'build_revision', 'prompt_revision',
                'source_scope', 'build_scope', 'captured_at_ms', 'loaded_code_equivalence',
            )
            assert capture['runtime_version'] == {
                key: public_version[key] for key in version_fields if key in public_version
            }
    finally:
        app_server.should_exit = True
        server_thread.join(timeout=5)
        listener.close()

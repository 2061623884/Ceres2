"""Public CLI contract for the human-operated comparison, never real providers."""
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import textwrap
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest


HERE = Path(__file__).resolve().parents[1]
CLI = HERE / 'live_compare.py'


def test_default_cli_is_inert_without_settings_or_network(tmp_path):
    # The dedicated Tester's sitecustomize forbids all dotenv reads and
    # non-loopback sockets. This sentinel additionally proves no local config
    # is needed by the public no-argument entrypoint.
    (tmp_path / '.env').write_text('MUST_NOT_BE_READ=preview-sentinel\n')
    guard_dir = tmp_path / 'preview-guard'
    guard_dir.mkdir()
    (guard_dir / 'sitecustomize.py').write_text(
        'import runpy, sys\n'
        f'runpy.run_path({str(HERE / "guards" / "sitecustomize.py")!r})\n'
        'def no_network(event, args):\n'
        '    if event.startswith("socket.") or event == "subprocess.Popen":\n'
        '        raise RuntimeError("Preview must not use network or child processes")\n'
        'sys.addaudithook(no_network)\n'
    )
    environment = {**os.environ, 'PYTHONPATH': str(guard_dir),
                   'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run(
        [sys.executable, str(CLI)], cwd=tmp_path, env=environment,
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    preview = json.loads(result.stdout)
    assert preview['status'] == 'preview'
    assert preview['execution_enabled'] is False
    assert preview['configuration_loaded'] is False
    assert preview['provider_requests'] == 'not_attempted'
    assert {path.name for path in tmp_path.iterdir()} == {'.env', 'preview-guard'}


@pytest.mark.parametrize(('override', 'code'), [
    ({}, 'invalid_total_time_seconds'),
    ({'total_time_seconds': None}, 'invalid_total_time_seconds'),
    ({'total_time_seconds': 0}, 'invalid_total_time_seconds'),
    ({'total_time_seconds': float('inf')}, 'invalid_total_time_seconds'),
    ({'total_time_seconds': True}, 'invalid_total_time_seconds'),
    ({'total_time_seconds': 1, 'repeats': 0}, 'invalid_repeats'),
    ({'total_time_seconds': 1, 'repeats': True}, 'invalid_repeats'),
    ({'total_time_seconds': 1, 'order': ['baseline', 'baseline']}, 'invalid_order'),
    ({'total_time_seconds': 1, 'cases': ['arbitrary-private-prompt']}, 'invalid_cases'),
    ({'total_time_seconds': 1}, 'missing_provenance'),
])
def test_execution_rejects_unbounded_or_incomplete_plan_before_settings(tmp_path, override, code):
    manifest = tmp_path / 'plan.json'
    # Sources intentionally do not exist. An invalid authorized budget or
    # incomplete provenance must fail without loading configuration or starting.
    plan = {'cases': ['policy'], 'repeats': 1,
            'order': ['baseline', 'candidate'], **override}
    manifest.write_text(json.dumps(plan))
    output = tmp_path / 'must-not-exist.jsonl'
    result = subprocess.run(
        [sys.executable, str(CLI), '--execute', '--manifest', str(manifest),
         '--output', str(output)], cwd=tmp_path, env=os.environ.copy(),
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 2, result.stdout
    assert json.loads(result.stdout)['status'] == 'invalid_plan'
    assert json.loads(result.stdout)['code'] == code
    assert not output.exists()


def comparison_source(tmp_path):
    """A synthetic checkout; describing it must never import its settings."""
    root = tmp_path / 'source'
    root.mkdir(parents=True)
    files = {
        'backend/app/__init__.py': '',
        'backend/app/core/config.py': 'raise RuntimeError("SETTINGS_MUST_NOT_BE_IMPORTED")\n',
        'backend/app/api/guide.py': '# deadline = time.monotonic() + 30.0\n',
        'backend/app/services/pi_product_runtime.py': 'MAX_TOOL_ROUNDS = 5\n',
        'backend/app/services/kev_provider.py': '# httpx.Client(timeout=3.0)\n',
        'backend/app/services/memory_model.py': '# timeout=20, max_retries=0, temperature=0\n',
        'backend/app/mercury/policy.py': (
            'POLICIES = [("P-01", "return", "Synthetic", "Synthetic rule", "return")]\n'
            'def search_policies(query, category=None):\n'
            '    return {"source": {"name": "Synthetic policy", "version": "v1", "policy_id": "P-01"}}\n'
        ),
        'runtime/pi/src/worker.ts': '// maxTokens:1536; maxTokens:256\n',
        'runtime/pi/src/result-expression.ts': '// maxTokens:512; maxTokens:256\n',
        'runtime/pi/src/prompt-modules.ts': '// synthetic-prompt\n',
        'runtime/pi/package-lock.json': '{}\n',
        'backend/requirements.lock': 'synthetic-dependencies\n',
        'data/fixtures/products.json': '{"products":[]}\n',
        '.gitignore': '.env\n.venv/\ndist/\n__pycache__/\n',
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    for command in (['init', '-q'], ['add', '.'],
                    ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                     'commit', '-qm', 'synthetic source']):
        subprocess.run(['git', *command], cwd=root, check=True, capture_output=True)
    dist = root / 'runtime/pi/dist'
    dist.mkdir()
    (dist / 'worker.js').write_text('// synthetic build\n')
    (dist / 'result-expression.js').write_text('// synthetic build\n')
    return root


def test_source_description_is_read_only_and_rejects_dirty_product_source(tmp_path):
    source = comparison_source(tmp_path)
    (source / '.env').write_text('OPENAI_API_KEY=DO_NOT_READ_OR_PRINT\n')
    command = [sys.executable, str(CLI), '--describe', str(source)]
    result = subprocess.run(command, env=os.environ.copy(), capture_output=True,
                            text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)
    assert record['status'] == 'source_description'
    description = record['source']
    assert len(description['revision']) == 40
    assert len(description['tree']) == 40
    assert description['build_revision'] is None, 'Build provenance needs the human build record'
    for field in ('source_sha256', 'runtime_source_sha256', 'dist_sha256',
                  'facts_sha256', 'prompts_sha256', 'budget_sha256', 'locks_sha256'):
        assert len(description[field]) == 64
    assert 'DO_NOT_READ_OR_PRINT' not in result.stdout + result.stderr
    assert 'SETTINGS_MUST_NOT_BE_IMPORTED' not in result.stdout + result.stderr
    assert not list(source.rglob('*.sqlite*'))
    (source / 'runtime/pi/src/worker.ts').write_text('// changed after freeze\n')
    changed = subprocess.run(command, env=os.environ.copy(), capture_output=True,
                             text=True, timeout=10)
    assert changed.returncode == 2
    assert json.loads(changed.stdout)['code'] == 'dirty_source'


def source_record(source):
    result = subprocess.run([sys.executable, str(CLI), '--describe', str(source)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(result.stdout)['source']
    return {**record, 'build_revision': record['revision'],
            'build_source_sha256': record['runtime_source_sha256'],
            'build_dist_sha256': record['dist_sha256']}


def comparison_plan(tmp_path):
    return {
        'total_time_seconds': 30,
        'cases': ['chat'], 'repeats': 1, 'order': ['baseline', 'candidate'],
        'models': {'main': 'fixture-main', 'memory_extraction': 'fixture-extract',
                   'memory_dream': 'fixture-dream'},
        'sources': {side: source_record(comparison_source(tmp_path / side))
                    for side in ('baseline', 'candidate')},
    }


def test_frozen_plan_preview_checks_provenance_and_never_overwrites_output(tmp_path):
    plan = comparison_plan(tmp_path)
    manifest = tmp_path / 'plan.json'
    manifest.write_text(json.dumps(plan))
    command = [sys.executable, str(CLI), '--manifest', str(manifest)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    preview = json.loads(result.stdout)
    assert preview['manifest_valid'] is True
    assert preview['planned_samples'] == 2
    assert preview['configuration_loaded'] is False
    existing = tmp_path / 'existing.jsonl'
    existing.write_text('preserve previous evidence\n')
    refused = subprocess.run(command + ['--execute', '--output', str(existing)],
                             capture_output=True, text=True, timeout=10)
    assert refused.returncode == 2
    assert json.loads(refused.stdout)['code'] == 'output_exists'
    assert existing.read_text() == 'preserve previous evidence\n'
    plan['sources']['candidate']['build_revision'] = '0' * 40
    manifest.write_text(json.dumps(plan))
    mismatch = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert mismatch.returncode == 2
    assert json.loads(mismatch.stdout)['code'] == 'build_provenance_mismatch'
    plan['sources']['candidate']['build_revision'] = plan['sources']['candidate']['revision']
    plan['sources']['candidate']['source_sha256'] = '0' * 64
    manifest.write_text(json.dumps(plan))
    mismatch = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert mismatch.returncode == 2
    assert json.loads(mismatch.stdout)['code'] == 'source_provenance_mismatch'


def test_policy_fact_freeze_accepts_literal_extraction_but_rejects_changed_facts(tmp_path):
    plan = comparison_plan(tmp_path)
    candidate = Path(plan['sources']['candidate']['directory'])
    policy = candidate / 'backend/app/mercury/policy.py'
    content = policy.read_text()
    policy.write_text('POLICY_SOURCE_NAME = "Synthetic policy"\nPOLICY_SOURCE_VERSION = "v1"\n'
                      + content.replace('"name": "Synthetic policy", "version": "v1"',
                                        '"name": POLICY_SOURCE_NAME, "version": POLICY_SOURCE_VERSION'))
    def freeze_candidate():
        subprocess.run(['git', 'add', 'backend/app/mercury/policy.py'], cwd=candidate, check=True)
        subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'policy fixture change'], cwd=candidate, check=True)
        plan['sources']['candidate'] = source_record(candidate)
        manifest = tmp_path / 'plan.json'
        manifest.write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(CLI), '--manifest', str(manifest)],
                              capture_output=True, text=True, timeout=10)
    refactored = freeze_candidate()
    assert refactored.returncode == 0, refactored.stdout + refactored.stderr
    assert json.loads(refactored.stdout)['manifest_valid'] is True
    policy.write_text(policy.read_text().replace('Synthetic rule', 'Different eligibility rule'))
    changed = freeze_candidate()
    assert changed.returncode == 2
    assert json.loads(changed.stdout)['code'] == 'static_facts_mismatch'


def executable_plan(tmp_path, delay):
    plan = comparison_plan(tmp_path)
    probes = tmp_path / 'owned-child-probes'
    probes.mkdir()
    for side in plan['order']:
        source = Path(plan['sources'][side]['directory'])
        modules = {
            'backend/app/core/config.py': '''
                import os
                from pathlib import Path
                from types import SimpleNamespace
                print('offline-fixture-key PRIVATE_PROVIDER_BODY')
                def get_settings():
                    return SimpleNamespace(
                        root_dir=Path(__file__).resolve().parents[3],
                        database_url=os.environ['DATABASE_URL'],
                        mercury_checkpoint_path=Path(os.environ['MERCURY_CHECKPOINT_PATH']),
                        llm_mode='live', openai_api_key='offline-fixture-key',
                        openai_base_url='http://127.0.0.1:9/v1', kev_base_url='http://127.0.0.1:9',
                        llm_model='fixture-main', memory_extraction_model='fixture-extract',
                        memory_dream_model='fixture-dream')
            ''',
            'backend/app/core/database.py': '''
                import contextlib
                def init_db(): pass
                class SessionLocal:
                    @staticmethod
                    def begin(): return contextlib.nullcontext(None)
            ''',
            'backend/app/services/seed_service.py': '''
                def seed_catalog(db): pass
            ''',
            'backend/app/main.py': f'''
                import json, os, sqlite3, subprocess, sys, time
                from pathlib import Path
                from uuid import uuid4
                from fastapi import FastAPI, Request
                app = FastAPI()
                def state():
                    return dict(session_id='session-' + uuid4().hex, task_id=None,
                                state_version=0, session_version=0)
                @app.get('/api/v1/bootstrap')
                def bootstrap():
                    with sqlite3.connect(os.environ['DATABASE_URL'].removeprefix('sqlite:///')) as db:
                        db.execute('CREATE TABLE IF NOT EXISTS owner (id TEXT)')
                        row = db.execute('SELECT id FROM owner').fetchone()
                        owner = row[0] if row else 'owner-' + uuid4().hex
                        if not row: db.execute('INSERT INTO owner VALUES (?)', (owner,))
                    return dict(owner_id=owner, store_id='fixture', delivery_zone_id='fixture')
                @app.post('/api/v1/guide/sessions')
                def create_session(): return state()
                @app.get('/api/v1/guide/sessions/{{session}}')
                def get_session(session): return {{**state(), 'session_id': session}}
                @app.post('/api/v1/navigation/sessions/{{session}}/opening')
                def opening(session): return dict(opening_id='opening-' + uuid4().hex)
                @app.post('/api/v1/navigation/sessions/{{session}}/routes')
                async def route(session, request: Request):
                    body = await request.json()
                    return dict(status='ready', target_role='keke', routing_request_id=body['request_id'])
                @app.post('/api/v1/guide/sessions/{{session}}/runs')
                def run(session):
                    if {delay!r}:
                        marker = str(Path({str(probes)!r}) / ('escaped-' + uuid4().hex))
                        code = 'import time; from pathlib import Path; time.sleep(8); Path(' + repr(marker) + ').write_text("escaped")'
                        child = subprocess.Popen([sys.executable, '-c', code])
                        (Path({str(probes)!r}) / ('child-' + uuid4().hex + '.json')).write_text(
                            json.dumps(dict(pid=child.pid, pgid=os.getpgrp())))
                        time.sleep({delay!r})
                    return dict(run_id='run-' + uuid4().hex)
                @app.get('/api/v1/guide/sessions/{{session}}/runs/{{run_id}}/events')
                def events(session, run_id):
                    return dict(status='completed', events=[dict(sequence=1, type='turn.completed',
                        payload=dict(runtime_status='completed', answer_status='accepted', tool_rounds=0,
                                     answer_kind='general_explanation', runtime_events=[]))])
            ''',
        }
        for name, content in modules.items():
            (source / name).write_text(textwrap.dedent(content))
        subprocess.run(['git', 'add', 'backend/app'], cwd=source, check=True)
        subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'synthetic public application'], cwd=source, check=True)
        # Keep pyvenv.cfg and site-packages, not only the Python executable;
        # source imports are still the independent copied app package.
        (source / 'backend/.venv').symlink_to(Path(sys.prefix), target_is_directory=True)
        plan['sources'][side] = source_record(source)
    plan['repeats'] = 2
    return plan, probes


@pytest.mark.parametrize('outcome', ['completed', 'deadline', 'cancelled'])
def test_bounded_public_execution_isolates_samples_and_stops_owned_descendants(tmp_path, outcome):
    plan, probes = executable_plan(tmp_path, 0 if outcome == 'completed' else 60)
    plan['total_time_seconds'] = 5 if outcome == 'deadline' else 30
    manifest, output = tmp_path / 'plan.json', tmp_path / 'run.jsonl'
    manifest.write_text(json.dumps(plan))
    process = subprocess.Popen(
        [sys.executable, str(CLI), '--manifest', str(manifest), '--execute', '--output', str(output)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
    )
    try:
        if outcome == 'cancelled':
            until = time.monotonic() + 12
            while time.monotonic() < until:
                if output.exists() and '"call_stage": "guide"' in output.read_text():
                    # The source fixture proves an owned descendant really
                    # exists before cancellation; no unrelated PID is touched.
                    if list(probes.glob('child-*.json')):
                        break
                assert process.poll() is None, 'Runner exited before the cancel seam'
                time.sleep(.02)
            else:
                pytest.fail('No bounded guide stage reached')
            process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=15)
        assert output.exists(), stdout + stderr
        records = [json.loads(line) for line in output.read_text().splitlines()]
        summary = records[-1]
        assert summary['type'] == 'summary'
        assert summary['status'] == outcome
        assert summary['provider_http_requests'] == 'unknown'
        assert summary['usage'] == 'unknown'
        assert summary['cost'] == 'unknown'
        samples = [row for row in records if row['type'] == 'sample']
        assert len(samples) == (4 if outcome == 'completed' else 1)
        assert summary['unstarted_samples'] == (0 if outcome == 'completed' else 3)
        if outcome == 'completed':
            assert all(row['status'] == 'completed' for row in samples)
            isolated = [row for row in records if row['type'] == 'isolation']
            for field in ('database', 'owner', 'session'):
                assert len({row[field] for row in isolated}) == 4
            assert all(not Path(row['database']).exists() for row in isolated)
        else:
            children = [json.loads(path.read_text()) for path in probes.glob('child-*.json')]
            assert children, 'Cancellation test must reach an actual owned child'
            for child in children:
                status = Path(f'/proc/{child["pid"]}/stat')
                assert not status.exists() or status.read_text().split()[2] == 'Z'
            assert not list(probes.glob('escaped-*'))
        assert 'offline-fixture-key' not in stdout + stderr + output.read_text()
        assert 'PRIVATE_PROVIDER_BODY' not in stdout + stderr + output.read_text()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        # Failure-only cleanup is restricted to process groups written by the
        # synthetic children created during this test, never a global kill.
        for path in probes.glob('child-*.json'):
            child = json.loads(path.read_text())
            try:
                os.killpg(child['pgid'], signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.mark.parametrize('outcome', ['deadline', 'cancelled'])
def test_total_limit_and_cancel_cover_source_metadata_waits(tmp_path, outcome):
    plan = comparison_plan(tmp_path)
    plan['total_time_seconds'] = .2 if outcome == 'deadline' else 30
    manifest, output = tmp_path / 'plan.json', tmp_path / 'run.jsonl'
    manifest.write_text(json.dumps(plan))
    binary = tmp_path / 'slow-git-bin'
    binary.mkdir()
    probe = tmp_path / 'git-started.json'
    wrapped_git = binary / 'git'
    wrapped_git.write_text(
        f'#!{sys.executable}\nimport json, os, time\nfrom pathlib import Path\n'
        f'Path({str(probe)!r}).write_text(json.dumps(dict(pid=os.getpid(), pgid=os.getpgrp())))\n'
        'time.sleep(30)\n'
    )
    wrapped_git.chmod(0o755)
    started = time.monotonic()
    process = subprocess.Popen(
        [sys.executable, str(CLI), '--execute', '--manifest', str(manifest), '--output', str(output)],
        env={**os.environ, 'PATH': str(binary) + os.pathsep + os.environ['PATH']},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
    )
    try:
        if outcome == 'cancelled':
            until = time.monotonic() + 1
            while not probe.exists() and time.monotonic() < until:
                time.sleep(.01)
            assert probe.exists(), 'The source metadata wait must actually start'
            process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=2)
        assert time.monotonic() - started < 1.5
        assert output.exists(), stdout + stderr
        summary = json.loads(output.read_text().splitlines()[-1])
        assert summary['status'] == outcome
        assert summary['attempted_samples'] == 0
        assert summary['unstarted_samples'] == 2
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        if probe.exists():
            owned = json.loads(probe.read_text())
            command = Path(f'/proc/{owned["pid"]}/cmdline')
            if command.exists() and os.fsencode(str(wrapped_git)) in command.read_bytes():
                try:
                    os.killpg(owned['pgid'], signal.SIGKILL)
                except ProcessLookupError:
                    pass


@pytest.mark.parametrize('environment_case', ['upper', 'lower'])
def test_current_application_and_actual_pi_sdk_use_only_loopback_fixture(tmp_path, monkeypatch, environment_case):
    root = HERE.parents[1]
    # This deliberately exercises the complete current source description too;
    # it cannot inherit synthetic metadata success for an unsupported real API.
    origin = source_record(root)
    sys.path.insert(0, str(root / 'backend/tests'))
    from test_guide_semantics import hook
    calls = []

    class Provider(BaseHTTPRequestHandler):
        def log_message(self, *_args): pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            try:
                if self.path.endswith('/systemone'):
                    calls.append({'kind': 'kev', 'questions': sorted(body['questions'])})
                    response = {'model': 'kev-latest', 'answers': {
                        name: {'type': 'choice', 'choice': 'no', 'probabilities': {
                            key: float(key == 'no') for key in question['criteria']}}
                        for name, question in body['questions'].items()}}
                elif not body.get('stream'):
                    calls.append({'kind': 'memory', 'model': body['model']})
                    response = {'id': 'memory-fixture', 'object': 'chat.completion',
                                'created': 1, 'model': body['model'], 'choices': [{
                                    'index': 0, 'message': {'role': 'assistant', 'content': '{"records":[]}'},
                                    'finish_reason': 'stop'}]}
                else:
                    calls.append({'kind': 'pi', 'model': body['model']})
                    delta, finish = hook(body)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.end_headers()
                    for part, reason in ((delta, None), ({}, finish)):
                        chunk = {'id': 'pi-fixture', 'object': 'chat.completion.chunk',
                                 'created': 1, 'model': body['model'], 'choices': [{
                                     'index': 0, 'delta': part, 'finish_reason': reason}]}
                        self.wfile.write(('data: ' + json.dumps(chunk) + '\n\n').encode())
                    self.wfile.write(b'data: [DONE]\n\n')
                    return
                encoded = json.dumps(response).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
            except (BrokenPipeError, ConnectionResetError):
                pass

    source_paths = ('backend/app', 'runtime/pi/src', 'data/fixtures',
                    'backend/requirements.lock', 'runtime/pi/package-lock.json',
                    'runtime/pi/package.json', 'runtime/pi/tsconfig.json')
    names = subprocess.check_output(['git', 'ls-files', '-z', '--', *source_paths], cwd=root).decode().split('\0')
    sources = {}
    for side in ('baseline', 'candidate'):
        source = tmp_path / side
        source.mkdir()
        for name in filter(None, names):
            destination = source / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / name, destination)
        shutil.copyfile(root / '.gitignore', source / '.gitignore')
        for command in (['init', '-q'], ['add', '.'],
                        ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                         'commit', '-qm', 'controlled copy of current product sources']):
            subprocess.run(['git', *command], cwd=source, check=True, capture_output=True)
        shutil.copytree(root / 'runtime/pi/dist', source / 'runtime/pi/dist')
        (source / 'runtime/pi/node_modules').symlink_to(root / 'runtime/pi/node_modules', target_is_directory=True)
        (source / 'backend/.venv').symlink_to(Path(sys.prefix), target_is_directory=True)
        sources[side] = source_record(source)
        assert sources[side]['source_sha256'] == origin['source_sha256']
        assert sources[side]['dist_sha256'] == origin['dist_sha256']

    with ThreadingHTTPServer(('127.0.0.1', 0), Provider) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            configuration = {
                'OPENAI_API_KEY': 'offline-fixture-key',
                'OPENAI_BASE_URL': f'http://127.0.0.1:{server.server_port}/v1',
                'KEV_BASE_URL': f'http://127.0.0.1:{server.server_port}',
                'LLM_MODE': 'live', 'LLM_MODEL': 'fixture-main',
                'MEMORY_EXTRACTION_MODEL': 'fixture-extract',
                'MEMORY_DREAM_MODEL': 'fixture-dream',
            }
            for key in tuple(os.environ):
                if key.upper() in configuration:
                    monkeypatch.delenv(key)
            for key, value in configuration.items():
                monkeypatch.setenv(key if environment_case == 'upper' else key.lower(), value)
            plan = {'total_time_seconds': 30, 'repeats': 1, 'cases': ['chat'],
                    'order': ['baseline', 'candidate'], 'sources': sources,
                    'models': {'main': 'fixture-main', 'memory_extraction': 'fixture-extract',
                               'memory_dream': 'fixture-dream'}}
            manifest, output = tmp_path / 'plan.json', tmp_path / 'run.jsonl'
            manifest.write_text(json.dumps(plan))
            result = subprocess.run([sys.executable, str(CLI), '--manifest', str(manifest),
                                     '--execute', '--output', str(output)],
                                    capture_output=True, text=True, timeout=40)
            records = [json.loads(line) for line in output.read_text().splitlines()]
            assert result.returncode == 0, result.stdout + result.stderr + output.read_text()
            samples = [row for row in records if row['type'] == 'sample']
            assert len(samples) == 2
            assert all(row['status'] == 'completed' for row in samples)
            for sample in samples:
                observed = sample['runtime_summary']
                assert observed['primary_pi_turns'] > 0
                assert observed['tool_starts'] > 0
                assert observed['policy_lookups'] == 0
                assert observed['policy_judgment']['outcome'] == 'no'
                assert sample['provider_http_requests'] == sample['usage'] == sample['cost'] == 'unknown'
            assert any(call['kind'] == 'pi' for call in calls)
            assert any(call.get('questions') == ['policy'] for call in calls)
            assert all(call['model'] == 'fixture-main' for call in calls if call['kind'] == 'pi')
            assert 'offline-fixture-key' not in result.stdout + result.stderr + output.read_text()
        finally:
            server.shutdown()
            thread.join()


def test_kev_timeout_literal_extraction_matches_but_a_changed_budget_does_not(tmp_path):
    plan = comparison_plan(tmp_path)
    relative = 'backend/app/services/kev_provider.py'
    root = HERE.parents[1]
    baseline = subprocess.check_output(['git', 'show',
        '4bed9c891261e382122d424825b649989ea92c92:' + relative], cwd=root).decode()
    current = (root / relative).read_text()
    assert 'KEV_TIMEOUT_SECONDS = 3.0' in current
    def freeze(side, content):
        source = Path(plan['sources'][side]['directory'])
        (source / relative).write_text(content)
        subprocess.run(['git', 'add', relative], cwd=source, check=True)
        subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'timeout fixture change'], cwd=source, check=True)
        plan['sources'][side] = source_record(source)
    def preview():
        manifest = tmp_path / 'plan.json'
        manifest.write_text(json.dumps(plan))
        return subprocess.run([sys.executable, str(CLI), '--manifest', str(manifest)],
                              capture_output=True, text=True, timeout=10)
    # Actual original/current provider source, read as literals only, surrounded
    # by identical synthetic data/build scaffolding. No provider is imported.
    freeze('baseline', baseline)
    freeze('candidate', current)
    unchanged = preview()
    assert unchanged.returncode == 0, unchanged.stdout + unchanged.stderr
    freeze('candidate', current.replace('KEV_TIMEOUT_SECONDS = 3.0', 'KEV_TIMEOUT_SECONDS = 4.0', 1))
    changed = preview()
    assert changed.returncode == 2
    assert json.loads(changed.stdout)['code'] == 'numeric_budget_mismatch'

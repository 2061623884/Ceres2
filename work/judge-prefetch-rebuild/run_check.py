"""Dedicated Tester capture: fresh source hashes, isolated configuration, local-only IO."""
from pathlib import Path
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sources():
    result = {}
    files = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z', 'backend', 'runtime', 'frontend', 'data'], cwd=ROOT).decode().split('\0')
    for name in files:
        if name:
            path = ROOT / name
            if path.is_file():
                result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


label, folder, *command = sys.argv[1:]
destination = HERE / 'evidence' / label
destination.mkdir(parents=True, exist_ok=True)
temporary = HERE / 'tmp' / label
temporary.mkdir(parents=True, exist_ok=True)
# Product subprocesses deliberately filter NODE_OPTIONS. Their supported PATH
# lookup still goes through this test-only launcher, so the SDK itself receives
# the local-only guard without changing production environment propagation.
node_binary = shutil.which('node')
if node_binary is None:
    raise RuntimeError('Controlled verification requires an installed Node runtime')
launchers = temporary / 'guarded-bin'
launchers.mkdir(exist_ok=True)
node_launcher = launchers / 'node'
node_launch_log = destination / 'node-launches.log'
node_guard_log = destination / 'node-guard-events.jsonl'
node_launcher.write_text('#!/bin/sh\nexport CERES_NODE_GUARD_AUDIT=' + shlex.quote(str(node_guard_log)) +
                         '\nprintf \'%s %s\\n\' "$$" "$1" >> ' + shlex.quote(str(node_launch_log)) +
                         '\nexec ' + shlex.quote(node_binary) + ' --require=' +
                         shlex.quote(str(HERE / 'guards' / 'node-local-only.cjs')) + ' "$@"\n')
node_launcher.chmod(0o755)
environment = {
    'PATH': str(launchers) + os.pathsep + os.environ['PATH'],
    'HOME': str(temporary),
    'TMPDIR': str(temporary),
    'PYTHONPATH': str(HERE / 'guards') + os.pathsep + str(ROOT / 'backend'),
    'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
    'NODE_OPTIONS': '--require=' + str(HERE / 'guards' / 'node-local-only.cjs'),
    'CERES_NODE_GUARD_AUDIT': str(node_guard_log),
    'OPENAI_API_KEY': 'offline-fixture-key',
    'OPENAI_BASE_URL': 'http://127.0.0.1:9/v1',
    'KEV_BASE_URL': '',
    'LLM_MODEL': 'controlled-test',
    'LLM_MODE': 'live',
    'DATABASE_URL': 'sqlite:///:memory:',
    'MERCURY_CHECKPOINT_PATH': str(temporary / 'checkpoints.sqlite3'),
    'HUMAN_OPERATOR_TOKEN': '',
    'SHOPPING_WRITES_PAUSED': 'false',
    'BUSINESS_DATA_MODE': 'demo',
    'NO_PROXY': '127.0.0.1,localhost,::1',
    'no_proxy': '127.0.0.1,localhost,::1',
    'UV_CACHE_DIR': str(HERE / 'tmp' / 'uv-cache'),
    'npm_config_cache': str(HERE / 'tmp' / 'npm-cache'),
    'npm_config_update_notifier': 'false',
    'npm_config_audit': 'false',
}
before = sources()
record = {'label': label, 'command': command, 'cwd': str(ROOT / folder),
          'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
          'before_source_sha256': before, 'safety': 'Sanitized environment; fake key; dotenv reads forbidden; Python/Node socket connections restricted to loopback; pytest conftest disables dotenv before app settings.'}
record['harness_sha256'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), *sorted((HERE / 'guards').glob('*.py')), *sorted((HERE / 'guards').glob('*.cjs')), *sorted((HERE / 'verification_tests').glob('*.py'))]}
record['node_guard_launcher'] = {'path': str(node_launcher.relative_to(ROOT)),
                                 'sha256': hashlib.sha256(node_launcher.read_bytes()).hexdigest(),
                                 'runtime': node_binary}
start = time.monotonic()
with (destination / 'output.log').open('w') as output:
    process = subprocess.Popen(command, cwd=ROOT / folder, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end='', flush=True)
        output.write(line)
        output.flush()
    record['exit_code'] = process.wait()
record['elapsed_seconds'] = round(time.monotonic() - start, 3)
after = sources()
record['source_changes_during_run'] = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
record['after_source_sha256'] = after
record['after_harness_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() if (ROOT / name).is_file() else None for name in record['harness_sha256']}
record['harness_changes_during_run'] = sorted(name for name, digest in record['harness_sha256'].items() if record['after_harness_sha256'][name] != digest)
record['node_guard_launcher']['after_sha256'] = hashlib.sha256(node_launcher.read_bytes()).hexdigest()
record['node_guard_launcher']['invocations'] = node_launch_log.read_text().splitlines() if node_launch_log.exists() else []
record['node_guard_events'] = [json.loads(line) for line in node_guard_log.read_text().splitlines()] if node_guard_log.exists() else []
(destination / 'record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: record[k] for k in ['label', 'exit_code', 'elapsed_seconds', 'source_changes_during_run', 'harness_changes_during_run']}))
raise SystemExit(record['exit_code'])

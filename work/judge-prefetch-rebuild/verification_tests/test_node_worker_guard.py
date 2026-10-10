"""Tester-only harness regression through the real public Pi worker path."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'backend' / 'tests'))

# Install the existing controlled settings before the application's imports.
from conftest import controlled_kev_transport
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn


def test_node_launcher_guards_child_without_node_options():
    code = '''
const net = require('node:net'), fs = require('node:fs');
let blocked = 0;
try { new net.Socket().connect({host:'guard-probe.invalid', port:443}); }
catch (error) { if (error.message === 'Controlled verification forbids non-loopback Node sockets') blocked++; }
try { fs.readFileSync('unused-guard-probe/.env'); }
catch (error) { if (error.message === 'Controlled verification forbids dotenv reads') blocked++; }
// Reload the guard over a sentinel transport so this malformed-host probe can
// never perform DNS or network IO even if the predicate regresses.
const guard = process.execArgv.find(value => value.startsWith('--require=')).slice('--require='.length);
net.Socket.prototype.connect = function () { throw new Error('unexpected transport delegation'); };
delete require.cache[require.resolve(guard)];
require(guard);
try { new net.Socket().connect({host:'127.guard-probe.invalid', port:443}); }
catch (error) { if (error.message === 'Controlled verification forbids non-loopback Node sockets') blocked++; }
if (blocked !== 3) process.exit(1);
'''
    environment = {key: os.environ[key] for key in ('PATH', 'HOME', 'NO_PROXY')}
    assert 'NODE_OPTIONS' not in environment
    subprocess.run(['node', '-e', code], env=environment, check=True)


def test_actual_pi_worker_blocks_non_loopback_transport(pi_client, monkeypatch):
    client, requests = pi_client
    from app.core.config import get_settings
    monkeypatch.setenv('OPENAI_BASE_URL', 'http://guard-probe.invalid:18080/v1')
    get_settings.cache_clear()
    events = turn(client, '受控非回环传输探针', 'verification-node-guard')
    assert events[-1]['type'] == 'error', events
    assert requests == []
    audit_path = Path(os.environ['CERES_NODE_GUARD_AUDIT'])
    audit = [json.loads(line) for line in audit_path.read_text().splitlines()]
    launches = (audit_path.parent / 'node-launches.log').read_text().splitlines()
    worker_pids = {int(line.split(' ', 1)[0]) for line in launches
                   if line.endswith('/runtime/pi/dist/worker.js')}
    assert worker_pids
    assert any(row['event'] == 'loaded' and row['pid'] in worker_pids for row in audit)
    assert any(row['event'] == 'blocked_non_loopback_socket' and row['pid'] in worker_pids for row in audit)

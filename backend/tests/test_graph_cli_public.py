"""Public explicit graph CLI/JSONL boundary; no model or network required."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

BACKEND = Path(__file__).resolve().parents[1]


def invoke(*args, payload=None):
    return subprocess.run([sys.executable, '-m', 'app.knowledge.cli', *args],
                          cwd=BACKEND, input=payload, text=True, capture_output=True,
                          timeout=5, env={**os.environ, 'OPENAI_API_KEY': 'offline-fixture-key'})


@pytest.mark.parametrize('method', ['local', 'global'])
def test_explicit_graph_cli_missing_index_is_not_an_empty_success(tmp_path, method):
    result = invoke('graph', '--graph-root', str(tmp_path), '--query', '鸡蛋关系', '--method', method)
    assert result.returncode == 0, result.stderr
    body = json.loads(result.stdout)
    assert body['error'] == 'GRAPH_INDEX_MISSING'
    assert body['graph_status'] == 'not_executed'
    assert body['method'] == method


def test_real_jsonl_worker_graph_missing_index_then_invalid_action(tmp_path):
    requests = [dict(action='graph', query='鸡蛋关系', method='global',
                     deadline=time.monotonic() + 2, graph_query_id='query-1'),
                dict(action='not-supported')]
    result = invoke('serve', '--graph-root', str(tmp_path),
                    payload=''.join(json.dumps(row) + '\n' for row in requests))
    assert result.returncode == 0, result.stderr
    first, second = map(json.loads, result.stdout.splitlines())
    assert first['error'] == 'GRAPH_INDEX_MISSING'
    assert first['graph_query_id'] == 'query-1'
    assert first['graph_status'] == 'not_executed'
    assert second['error'] == 'KNOWLEDGE_UNAVAILABLE'


def test_graph_service_keeps_original_deadline_and_cancel_callback(monkeypatch):
    from app.services.knowledge_service import KnowledgeService
    service = KnowledgeService()
    captured = {}
    def query(request, **kwargs):
        captured.update(request=request, **kwargs)
        return {'captured': True}
    monkeypatch.setattr(service, '_query', query)
    deadline, stop = time.monotonic() + .5, lambda: False
    assert service.graph('鸡蛋关系', method='global', deadline=deadline, should_stop=stop) == {'captured': True}
    assert captured['deadline'] == captured['request']['deadline'] == deadline
    assert captured['should_stop'] is stop
    assert captured['request']['method'] == 'global'
    assert captured['request']['graph_query_id']


@pytest.mark.parametrize('interrupted', [False, True])
def test_cli_graph_kills_blocked_embedding_thread(monkeypatch, capsys, tmp_path, interrupted):
    import asyncio
    from app.knowledge import cli, graph
    original = subprocess.Popen
    children = []
    def launch(command, **kwargs):
        child = original([sys.executable, '-c',
            'import concurrent.futures,time; pool=concurrent.futures.ThreadPoolExecutor(); pool.submit(time.sleep,3)'], **kwargs)
        children.append(child)
        if interrupted:
            def stop(*args, **kwargs):
                raise KeyboardInterrupt
            monkeypatch.setattr(child, 'communicate', stop)
        return child
    async def blocked(*args, **kwargs):
        await asyncio.to_thread(time.sleep, .5)
        return {'late': True}
    monkeypatch.setattr(cli, 'subprocess', subprocess, raising=False)
    monkeypatch.setattr(subprocess, 'Popen', launch)
    monkeypatch.setattr(graph, 'search', blocked)
    monkeypatch.setattr(sys, 'argv', ['knowledge', 'graph', '--query', 'PRIVATE_QUERY_DO_NOT_ECHO',
        '--graph-root', str(tmp_path), '--deadline', str(time.monotonic() + .1)])
    started = time.monotonic()
    cli.main()
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result['error'] == ('KNOWLEDGE_CANCELLED' if interrupted else 'KNOWLEDGE_TIMEOUT')
    assert ('KeyboardInterrupt' if interrupted else 'TimeoutExpired') in captured.err
    assert 'PRIVATE_QUERY_DO_NOT_ECHO' not in captured.out + captured.err
    assert time.monotonic() - started < .45
    assert children
    children[0].wait(timeout=1)
    assert children[0].returncode != 0


def test_cli_offline_build_has_explicit_finite_budget_and_removes_partial_manifest(monkeypatch, capsys, tmp_path):
    from app.knowledge import cli
    original = subprocess.Popen
    marker = tmp_path / 'manifest.json'
    marker.write_text('{"old":true}')
    def launch(command, **kwargs):
        # A simulated blocking encoder leaves partial output, then ignores asyncio cancellation.
        program = ('import concurrent.futures,time,pathlib; '
                   f'pathlib.Path({str(tmp_path / "partial.parquet")!r}).write_bytes(b"partial"); '
                   'pool=concurrent.futures.ThreadPoolExecutor(); pool.submit(time.sleep,3)')
        return original([sys.executable, '-c', program], **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', launch)
    monkeypatch.setattr(sys, 'argv', ['knowledge', 'build-graph', '--graph-root', str(tmp_path),
                                    '--timeout-seconds', '.2'])
    started = time.monotonic()
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert result['error'] == 'KNOWLEDGE_TIMEOUT'
    assert time.monotonic() - started < .6
    assert not marker.exists()

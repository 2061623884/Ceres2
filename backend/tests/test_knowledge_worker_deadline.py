"""Shared retrieval worker budget and cancellation at its public query seam."""
import time
from types import SimpleNamespace

import pytest

from app.core.errors import AppError


@pytest.mark.parametrize('cancelled,code', [(False, 'KNOWLEDGE_TIMEOUT'), (True, 'KNOWLEDGE_CANCELLED')])
def test_queued_query_obeys_its_budget_without_interrupting_another_request(cancelled, code):
    from app.services.knowledge_service import KnowledgeService
    service = KnowledgeService()
    active = SimpleNamespace(kill=lambda: pytest.fail('Queued request killed the active worker'))
    service.child = active
    service.lock.acquire()
    started = time.monotonic()
    try:
        with pytest.raises(AppError) as failure:
            service.search('配送政策', 'policy', deadline=started + 0.05, should_stop=lambda: cancelled)
        assert failure.value.detail['error']['code'] == code
        assert time.monotonic() - started < 0.4
        assert service.child is active
    finally:
        service.lock.release()
        service.child = None


@pytest.fixture
def controlled_worker(tmp_path, monkeypatch):
    import subprocess
    import sys
    from app.services import knowledge_service
    original = subprocess.Popen
    monkeypatch.setattr(knowledge_service, 'ROOT_DIR', tmp_path)
    (tmp_path / 'backend').mkdir()

    def install(program):
        def launch(command, **kwargs):
            return original([sys.executable, '-u', '-c', program], **kwargs)
        monkeypatch.setattr(knowledge_service.subprocess, 'Popen', launch)
        return knowledge_service.KnowledgeService()
    return install


def test_worker_stale_index_error_is_not_returned_as_success(controlled_worker):
    service = controlled_worker("import sys,json\nfor line in sys.stdin:\n print(json.dumps({'error': 'KNOWLEDGE_STALE'}), flush=True)")
    try:
        with pytest.raises(AppError) as failure:
            service.search('退款', 'policy', deadline=time.monotonic() + 1)
        assert failure.value.detail['error']['code'] == 'KNOWLEDGE_STALE'
    finally:
        service.close()


def test_real_worker_rejects_wrong_index_revision_before_loading_models(tmp_path, monkeypatch):
    import json
    import sqlite3
    import subprocess
    import sys
    from app.services import knowledge_service
    index = tmp_path / 'hybrid.sqlite3'
    with sqlite3.connect(index) as db:
        db.execute('CREATE TABLE manifest (content TEXT)')
        db.execute('INSERT INTO manifest VALUES (?)', (json.dumps({'controlled': 'manifest-v1'}),))
    original = subprocess.Popen
    root = knowledge_service.ROOT_DIR

    def launch(command, **kwargs):
        kwargs['cwd'] = root / 'backend'
        return original([sys.executable, '-m', 'app.knowledge.cli', 'serve', '--index', str(index)], **kwargs)

    monkeypatch.setattr(knowledge_service, 'ROOT_DIR', tmp_path)
    monkeypatch.setattr(knowledge_service.subprocess, 'Popen', launch)
    service = knowledge_service.KnowledgeService()
    try:
        with pytest.raises(AppError) as failure:
            service.search('退款', 'policy', expected_index_revision='different-index-revision',
                           deadline=time.monotonic() + 1)
        assert failure.value.detail['error']['code'] == 'KNOWLEDGE_STALE'
        diagnostic = (tmp_path / 'data/indexes/knowledge-worker.log').read_text()
        assert 'StaleIndexError' in diagnostic
        assert 'The index changed after source validation' in diagnostic
    finally:
        service.close()


def test_worker_missing_dependency_is_explicitly_unavailable(controlled_worker):
    service = controlled_worker("import sys,json\nfor line in sys.stdin:\n print(json.dumps({'error':'KNOWLEDGE_UNAVAILABLE'}), flush=True)")
    try:
        with pytest.raises(AppError) as failure:
            service.search('退款', 'policy', deadline=time.monotonic() + 1)
        assert failure.value.detail['error']['code'] == 'KNOWLEDGE_UNAVAILABLE'
    finally:
        service.close()


def test_partial_worker_line_is_bounded_and_next_request_cannot_receive_old_output(controlled_worker):
    service = controlled_worker("import sys,json,time\nfor line in sys.stdin:\n r=json.loads(line)\n if r['query']=='slow':\n  sys.stdout.write('{');sys.stdout.flush();time.sleep(5)\n else:\n  print(json.dumps({'hits':[],'manifest':{},'query':r['query']}),flush=True)")
    try:
        started = time.monotonic()
        with pytest.raises(AppError) as failure:
            service.search('slow', 'policy', deadline=started + 0.15)
        assert failure.value.detail['error']['code'] == 'KNOWLEDGE_TIMEOUT'
        assert time.monotonic() - started < 0.5
        result = service.search('next', 'policy', deadline=time.monotonic() + 1)
        assert result['query'] == 'next'
    finally:
        service.close()


def test_cancelled_queue_does_not_interrupt_a_real_active_worker(controlled_worker):
    from concurrent.futures import ThreadPoolExecutor
    service = controlled_worker("import sys,json,time\nfor line in sys.stdin:\n time.sleep(.15)\n print(json.dumps({'hits':[],'manifest':{},'query':json.loads(line)['query']}),flush=True)")
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            active = pool.submit(service.search, 'active', 'policy', deadline=time.monotonic() + 1)
            with pytest.raises(AppError) as failure:
                service.search('cancelled', 'policy', deadline=time.monotonic() + 1, should_stop=lambda: True)
            assert failure.value.detail['error']['code'] == 'KNOWLEDGE_CANCELLED'
            assert active.result(timeout=1)['query'] == 'active'
    finally:
        service.close()


def test_real_worker_missing_local_dependencies_does_not_fake_empty_hits(tmp_path, monkeypatch, controlled_policy_source):
    import json
    import sqlite3
    import subprocess
    import sys
    from app.knowledge.corpus import manifest_revision
    from app.services import knowledge_service
    index = tmp_path / 'hybrid.sqlite3'
    manifest = controlled_policy_source['manifest']
    with sqlite3.connect(index) as db:
        db.execute('CREATE TABLE manifest (content TEXT)')
        db.execute('INSERT INTO manifest VALUES (?)', (json.dumps(manifest),))
    original = subprocess.Popen
    root = knowledge_service.ROOT_DIR

    def launch(command, **kwargs):
        kwargs['cwd'] = root / 'backend'
        # Block only the required import; keep sitecustomize/network guards active.
        program = "import sys; sys.modules['numpy']=None; from app.knowledge.cli import main; sys.argv=['cli','serve','--index',sys.argv[1],'--fixtures',sys.argv[2]]; main()"
        return original([sys.executable, '-c', program, str(index), str(controlled_policy_source['root'] / 'data/fixtures')], **kwargs)

    monkeypatch.setattr(knowledge_service, 'ROOT_DIR', tmp_path)
    monkeypatch.setattr(knowledge_service.subprocess, 'Popen', launch)
    service = knowledge_service.KnowledgeService()
    try:
        with pytest.raises(AppError) as failure:
            service.search('退款', 'policy', expected_index_revision=manifest_revision(manifest),
                           deadline=time.monotonic() + 1)
        assert failure.value.detail['error']['code'] == 'KNOWLEDGE_UNAVAILABLE'
    finally:
        service.close()


@pytest.mark.parametrize('change,namespace', [('policy_version', 'policy'), ('add_product', 'product'), ('remove_product', 'product')])
def test_real_worker_rejects_changed_live_corpus_before_model_recall(tmp_path, monkeypatch, controlled_policy_source, change, namespace):
    import json
    import subprocess
    import sys
    from app.services import knowledge_service
    root = controlled_policy_source['root']
    fixtures = root / 'data/fixtures'
    if change == 'policy_version':
        path = fixtures / 'policies.json'
        data = json.loads(path.read_text())
        data['version'] = 'unindexed-policy-version'
    else:
        path = fixtures / 'products.json'
        data = json.loads(path.read_text())
        if change == 'add_product':
            data['products'].append({**data['products'][0], 'sku_id': 'new-unindexed-product'})
        else:
            data['products'].pop(0)
    path.write_text(json.dumps(data, ensure_ascii=False))
    original = subprocess.Popen
    checkout = knowledge_service.ROOT_DIR

    def launch(command, **kwargs):
        kwargs['cwd'] = checkout / 'backend'
        return original([sys.executable, '-m', 'app.knowledge.cli', 'serve',
                         '--index', str(root / 'data/indexes/hybrid.sqlite3'), '--fixtures', str(fixtures)], **kwargs)

    monkeypatch.setattr(knowledge_service, 'ROOT_DIR', tmp_path)
    monkeypatch.setattr(knowledge_service.subprocess, 'Popen', launch)
    service = knowledge_service.KnowledgeService()
    try:
        with pytest.raises(AppError) as failure:
            service.search('查询', namespace, deadline=time.monotonic() + 1)
        assert failure.value.detail['error']['code'] == 'KNOWLEDGE_STALE'
    finally:
        service.close()


def test_worker_pipe_backpressure_uses_the_same_deadline(controlled_worker):
    service = controlled_worker('import time; time.sleep(5)')
    try:
        started = time.monotonic()
        with pytest.raises(AppError) as failure:
            service.search('x' * 1000000, 'policy', deadline=started + 0.15)
        assert failure.value.detail['error']['code'] == 'KNOWLEDGE_TIMEOUT'
        assert time.monotonic() - started < 0.5
    finally:
        service.close()

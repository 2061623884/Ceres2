"""Serialized local retrieval with one caller-owned deadline and worker lease."""
import atexit
import json
import os
import selectors
import subprocess
import threading
import time
from uuid import uuid4

from app.core.config import ROOT_DIR
from app.core.errors import AppError


def check_budget(deadline, should_stop):
    if should_stop is not None and should_stop():
        raise AppError(409, 'KNOWLEDGE_CANCELLED', '已停止本次知识检索')
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise AppError(503, 'KNOWLEDGE_TIMEOUT', '知识检索已达到本次处理时限')
    return remaining


class KnowledgeService:
    def __init__(self):
        self.child = None
        self.lock = threading.Lock()

    def _close_owned(self):
        child, self.child = self.child, None
        if child is not None:
            child.kill()
            # Reaping cannot extend an expired caller budget.
            threading.Thread(target=child.wait, daemon=True).start()
            child.stdin.close()
            child.stdout.close()

    def close(self):
        with self.lock:
            self._close_owned()

    def _query(self, request, *, deadline=None, should_stop=None):
        # Standalone APIs retain a budget; run callers pass their original deadline.
        if deadline is None:
            deadline = time.monotonic() + 30
        while not self.lock.acquire(timeout=min(0.05, check_budget(deadline, should_stop))):
            pass
        try:
            check_budget(deadline, should_stop)
            if self.child is None:
                folder = ROOT_DIR / 'data/indexes'
                folder.mkdir(parents=True, exist_ok=True)
                with (folder / 'knowledge-worker.log').open('ab') as log:
                    self.child = subprocess.Popen(
                        [str(ROOT_DIR / '.venv-graphrag/bin/python'), '-m', 'app.knowledge.cli', 'serve'],
                        cwd=ROOT_DIR / 'backend', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
                os.set_blocking(self.child.stdin.fileno(), False)
                os.set_blocking(self.child.stdout.fileno(), False)
            pending = memoryview((json.dumps(request, ensure_ascii=False) + '\n').encode())
            with selectors.DefaultSelector() as selector:
                selector.register(self.child.stdin, selectors.EVENT_WRITE)
                while pending:
                    if selector.select(timeout=min(0.05, check_budget(deadline, should_stop))):
                        pending = pending[os.write(self.child.stdin.fileno(), pending):]
                selector.unregister(self.child.stdin)
                selector.register(self.child.stdout, selectors.EVENT_READ)
                response = b''
                while b'\n' not in response:
                    if selector.select(timeout=min(0.05, check_budget(deadline, should_stop))):
                        chunk = os.read(self.child.stdout.fileno(), 65536)
                        if not chunk:
                            raise AppError(503, 'KNOWLEDGE_UNAVAILABLE', '知识索引或模型不可用，请检查本地检索构建记录')
                        response += chunk
            check_budget(deadline, should_stop)
            result = json.loads(response)
            if request['action'] == 'graph':
                if not isinstance(result, dict) or result.get('graph_query_id') != request['graph_query_id'] or result.get('method') != request['method']:
                    raise AppError(503, 'GRAPH_UNAVAILABLE', '图查询结果无法归属于本次请求')
                if result.get('error'):
                    code = result['error'] if result['error'] in ('GRAPH_INDEX_MISSING', 'KNOWLEDGE_STALE', 'KNOWLEDGE_TIMEOUT', 'GRAPH_UNAVAILABLE') else 'GRAPH_UNAVAILABLE'
                    raise AppError(503, code, '本次图查询未取得有效证据', graph_observation=result)
                if (result.get('graph_status') != 'success' or not isinstance(result.get('canonical_facts'), list)
                        or not isinstance(result.get('selection'), dict) or not isinstance(result.get('manifest'), dict)):
                    raise AppError(503, 'GRAPH_UNAVAILABLE', '图查询未返回可核对证据')
                check_budget(deadline, should_stop)
                return result
            if isinstance(result, dict) and result.get('error') == 'KNOWLEDGE_STALE':
                raise AppError(503, 'KNOWLEDGE_STALE', '知识索引与本次来源快照不一致，请重新查询')
            if not isinstance(result, dict) or result.get('error') or not isinstance(result.get('hits'), list) or not isinstance(result.get('manifest'), dict):
                raise AppError(503, 'KNOWLEDGE_UNAVAILABLE', '知识索引或模型不可用，请检查本地检索构建记录')
            return result
        except AppError:
            self._close_owned()
            raise
        except (OSError, ValueError) as error:
            self._close_owned()
            raise AppError(503, 'KNOWLEDGE_UNAVAILABLE', '知识索引或模型不可用，请检查本地检索构建记录') from error
        finally:
            self.lock.release()

    def search(self, query, namespace, *, limit=10, allowed_ids=None, category=None,
               deadline=None, should_stop=None, expected_index_revision=None):
        from app.services.runtime_observation import retrieval_observer
        from app.knowledge.corpus import manifest_revision
        observer = retrieval_observer()
        identity, started = uuid4().hex, time.monotonic()
        event = {'retrieval_id': identity, 'namespace': namespace}
        if observer is not None:
            event['run_id'] = observer[0]
            observer[1]({'type': 'retrieval_start', **event})
        result = None
        try:
            result = self._query({'action': 'hybrid', 'query': query, 'namespace': namespace,
                            'limit': limit, 'allowed_ids': allowed_ids, 'category': category,
                            'expected_index_revision': expected_index_revision},
                           deadline=deadline, should_stop=should_stop)
            return result
        finally:
            if observer is not None:
                observer[1]({'type': 'retrieval_end', **event,
                    'outcome': 'error' if result is None else 'success' if result['hits'] else 'empty',
                    'elapsed_ms': (time.monotonic() - started) * 1000,
                    'source_revision': result['manifest'].get('corpus_revision') if result is not None else None,
                    'index_revision': manifest_revision(result['manifest']) if result is not None else None})

    def graph(self, query, method='local', *, deadline, should_stop=None):
        if method not in ('local', 'global'):
            raise AppError(422, 'GRAPH_METHOD_INVALID', '图查询方法必须为 local 或 global')
        identity, started = uuid4().hex, time.monotonic()
        try:
            return self._query({'action': 'graph', 'query': query, 'method': method,
                                'deadline': deadline, 'graph_query_id': identity},
                               deadline=deadline, should_stop=should_stop)
        except AppError as error:
            if 'graph_observation' not in error.detail:
                # Killing a worker can hide actual provider calls. Unknown is not zero.
                error.detail['graph_observation'] = {
                    'graph_query_id': identity, 'method': method, 'graph_status': 'unobserved',
                    'error': error.detail['error']['code'], 'official_graph_calls': None,
                    'calls': None, 'call_counts': None, 'duration_ms': (time.monotonic()-started)*1000}
            raise



knowledge = KnowledgeService()
atexit.register(knowledge.close)

"""Serialized local retrieval with one caller-owned deadline and worker lease."""
import atexit
import json
import os
import selectors
import subprocess
import threading
import time

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
            return json.loads(response)
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
        return self._query({'action': 'hybrid', 'query': query, 'namespace': namespace,
                            'limit': limit, 'allowed_ids': allowed_ids, 'category': category,
                            'expected_index_revision': expected_index_revision},
                           deadline=deadline, should_stop=should_stop)


knowledge = KnowledgeService()
atexit.register(knowledge.close)

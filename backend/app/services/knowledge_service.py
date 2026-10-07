"""One lazy local retrieval worker, with no business DB or mutation authority."""
import atexit
import json
import selectors
import subprocess
import threading
from app.core.config import ROOT_DIR
from app.core.errors import AppError


class KnowledgeService:
    def __init__(self):
        self.child = None
        self.lock = threading.Lock()

    def close(self):
        if self.child is not None:
            self.child.kill()
            self.child.wait()
            self.child.stdin.close()
            self.child.stdout.close()
            self.child = None

    def _query(self, request):
        with self.lock:
            if self.child is None:
                folder = ROOT_DIR/'data/indexes'
                folder.mkdir(parents=True, exist_ok=True)
                with (folder/'knowledge-worker.log').open('ab') as log:
                    self.child = subprocess.Popen([str(ROOT_DIR/'.venv-graphrag/bin/python'), '-m', 'app.knowledge.cli', 'serve'],
                        cwd=ROOT_DIR/'backend', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True)
            self.child.stdin.write(json.dumps(request, ensure_ascii=False)+'\n')
            self.child.stdin.flush()
            with selectors.DefaultSelector() as selector:
                selector.register(self.child.stdout, selectors.EVENT_READ)
                if not selector.select(timeout=30):
                    self.close()
                    raise AppError(503, 'KNOWLEDGE_TIMEOUT', '知识检索超过当前运行的 30 秒处理预算')
            line = self.child.stdout.readline()
            if not line:
                self.close()
                raise AppError(503, 'KNOWLEDGE_UNAVAILABLE', '知识索引或模型不可用，请检查本地检索构建记录')
            return json.loads(line)

    def search(self, query, namespace, *, limit=10, allowed_ids=None, category=None):
        return self._query({'action': 'hybrid', 'query': query, 'namespace': namespace,
            'limit': limit, 'allowed_ids': allowed_ids, 'category': category})

    def graph(self, query, method='local'):
        return self._query({'action': 'graph', 'query': query, 'method': method})


knowledge = KnowledgeService()
atexit.register(knowledge.close)

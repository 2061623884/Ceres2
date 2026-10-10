"""One query's deadline and bounded, attributable observations; never global usage."""
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
import time
import threading
from uuid import uuid4

_ACTIVE = ContextVar('graph_operation', default=None)


class GraphDeadlineError(TimeoutError):
    pass


class GraphOperation:
    def __init__(self, identity, deadline):
        self.identity, self.deadline = identity, deadline
        self._lock = threading.Lock()
        self.calls = deque(maxlen=64)
        self.official_graph_calls = 0
        self.counts = {'completion': 0, 'embedding': 0}

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise GraphDeadlineError('Graph query reached its caller deadline')
        return remaining

    def begin_call(self, kind, model):
        self.remaining()
        row = {'call_id': uuid4().hex, 'graph_query_id': self.identity,
               'kind': kind, 'model': model, 'status': 'started',
               'duration_ms': None, 'usage': None, 'cost': None,
               'usage_source': 'provider' if kind == 'completion' else 'local_tokenizer',
               'response_model': None}
        with self._lock:
            self.counts[kind] += 1
            self.calls.append(row)
        return row

    def observations(self):
        with self._lock:
            return {'official_graph_calls': self.official_graph_calls,
                    'calls': [dict(row) for row in self.calls], 'call_counts': dict(self.counts),
                    'calls_truncated': sum(self.counts.values()) > len(self.calls)}


@contextmanager
def operation(identity, deadline):
    active = GraphOperation(identity, deadline)
    token = _ACTIVE.set(active)
    try:
        yield active
    finally:
        _ACTIVE.reset(token)


def current_operation():
    active = _ACTIVE.get()
    if active is None:
        raise RuntimeError('Graph provider requires an explicit operation scope')
    return active

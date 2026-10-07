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

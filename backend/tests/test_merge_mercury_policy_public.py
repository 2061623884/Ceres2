"""Mercury HTTP consumes the shared policy categories and original query budget."""
import json
import time
from types import SimpleNamespace
import pytest
from test_aftersales_public import web
from app.mercury.router import get_query_model

QUERIES = [('price', '价格'), ('stock', '库存'), ('delivery', '配送'),
    ('order', '订单修改'), ('refund', '退款'), ('fulfillment', '漏送'),
    ('quality', '质量'), ('return', '退货'), ('safety', '食品安全'), ('human', '人工')]


class PolicyModel:
    def __init__(self, category, query, delay=0):
        self.category, self.query, self.delay = category, query, delay
        self.calls = 0
        self.started = None
        self.categories = None

    def chat(self, messages, tools=None):
        self.calls += 1
        if self.calls > 1:
            return SimpleNamespace(content='', tool_calls=[])
        self.started = time.monotonic()
        self.categories = next(t['function']['parameters']['properties']['category']['enum']
            for t in tools if t['function']['name'] == 'search_after_sales_policy')
        time.sleep(self.delay)
        return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='policy',
            function=SimpleNamespace(name='search_after_sales_policy', arguments=json.dumps(
                {'query': self.query, 'category': self.category})))])

    def cancel(self):
        pass


@pytest.mark.parametrize('category,query', QUERIES)
def test_mercury_policy_http_supports_all_ten_source_categories(web, controlled_policy_source, category, query):
    client, _, url = web
    model = PolicyModel(category, query)
    client.app.dependency_overrides[get_query_model] = lambda: model
    response = client.post(url + '/turns/stream', json={'message': query, 'request_id': 'all-categories'})
    assert response.status_code == 200, response.text
    assert controlled_policy_source['calls'] == [(query, category)]
    assert set(model.categories) == {item[0] for item in QUERIES}
    assert client.get(url + '/aftersales').json()['receipts'] == []


def test_mercury_policy_worker_gets_original_budget_after_model_time(web, monkeypatch):
    from app.services.knowledge_service import knowledge
    client, _, url = web
    model = PolicyModel('return', '退货', delay=0.2)
    client.app.dependency_overrides[get_query_model] = lambda: model
    observed = []
    original = knowledge.search
    def recording_worker(*args, **kwargs):
        observed.append(kwargs['deadline'])
        return original(*args, **kwargs)
    monkeypatch.setattr(knowledge, 'search', recording_worker)
    response = client.post(url + '/turns/stream', json={'message': '退货政策', 'request_id': 'original-budget'})
    assert response.status_code == 200, response.text
    assert len(observed) == 1
    # Query acceptance precedes the first model call. Its time cannot be reset
    # by a later retrieval, nor replaced by the standalone 30-second fallback.
    assert observed[0] <= model.started + 15
    assert 'completed' in response.text
    assert client.get(url + '/aftersales').json()['receipts'] == []

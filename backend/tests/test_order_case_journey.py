"""TASK13 fresh checkout-to-canonical-query public journey."""
import json
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.core.database import create_db_engine, get_db, init_db
from app.core.config import get_settings
from app.main import create_app
from app.mercury.router import get_query_model
from app.services.seed_service import seed_catalog


@pytest.fixture
def journey(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), 'mercury_checkpoint_path', tmp_path / 'checkpoint.sqlite3')
    engine = create_db_engine(f"sqlite:///{tmp_path / 'business.sqlite3'}")
    init_db(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions.begin() as db:
        seed_catalog(db)
    def make_client():
        app = create_app(database_engine=engine)
        def database():
            with sessions() as db:
                yield db
        app.dependency_overrides[get_db] = database
        return TestClient(app)
    with make_client() as client:
        client.get('/api/v1/bootstrap')
        yield client, make_client
    engine.dispose()


def checkout(client):
    cart = client.get('/api/v1/cart').json()
    cart = client.post('/api/v1/cart/items', json={'sku_id': 'demo:flour-all-purpose-500g', 'quantity': 2,
        'expected_cart_version': cart['version']}).json()
    preview = client.post('/api/v1/checkout/preview', json={'expected_cart_version': cart['version']}).json()
    response = client.post('/api/v1/checkout/confirm', json={'preview_id': preview['preview_id'],
        'idempotency_key': preview['preview_id'], 'confirmed': True})
    assert response.status_code == 200, response.text
    return response.json()['order']


def test_checkout_metadata_selection_read_and_restart(journey):
    client, make_client = journey
    order = checkout(client)
    row = client.get('/api/v1/mercury/orders').json()['orders'][0]
    assert row['order_id'] == order['order_id']
    assert row['store_id'] == order['store_id']
    assert row['version'] == order['version']
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = '/api/v1/mercury/sessions/' + sid
    selected = client.put(url + '/order', json={'order_id': order['order_id'], 'selection_version': 0})
    assert selected.status_code == 200
    assert selected.json()['messages'] == []
    class Model:
        def chat(self, messages, tools=None):
            if messages[-1]['role'] == 'tool':
                return SimpleNamespace(content='查询完毕', tool_calls=[])
            return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='read', function=SimpleNamespace(
                name='check_refund_eligibility', arguments=json.dumps({'order_id': order['order_id']})))])
        def cancel(self):
            pass
    client.app.dependency_overrides[get_query_model] = Model
    response = client.post(url + '/turns/stream', json={'message': '查询退款资格', 'request_id': 'query'})
    assert response.status_code == 200 and '模拟整单退款' in response.text
    assert client.get('/api/v1/orders/' + order['order_id']).json() == order
    saved = client.get(url).json()
    with make_client() as restarted:
        restarted.cookies.set('sg_owner_id', client.cookies.get('sg_owner_id'))
        assert restarted.get(url).json() == saved
        assert restarted.get('/api/v1/mercury/orders').json()['orders'][0] == row


def test_empty_and_cross_owner_order_case_boundaries(journey):
    client, _ = journey
    assert client.get('/api/v1/mercury/orders').json()['orders'] == []
    order = checkout(client)
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = '/api/v1/mercury/sessions/' + sid
    assert client.put(url + '/order', json={'order_id': order['order_id'], 'selection_version': 0}).status_code == 200
    assert client.put(url + '/order', json={'order_id': order['order_id'], 'selection_version': 0}).status_code == 409
    client.cookies.clear()
    client.get('/api/v1/bootstrap')
    assert client.get('/api/v1/mercury/orders').json()['orders'] == []
    assert client.get(url).status_code == 404
    assert client.put(url + '/order', json={'order_id': order['order_id'], 'selection_version': 1}).status_code == 404
    assert client.post(url + '/turns/stream', json={'message': '查看订单', 'request_id': 'foreign'}).status_code == 404
    own = client.post('/api/v1/mercury/sessions').json()['session_id']
    assert client.put('/api/v1/mercury/sessions/' + own + '/order', json={'order_id': order['order_id'], 'selection_version': 0}).status_code == 404

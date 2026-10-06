"""TASK12 fresh public contract: isolated canonical database only."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.core.database import create_db_engine, get_db, init_db
from app.main import create_app
from app.models.store import Offer
from app.services.seed_service import seed_catalog

SKU = 'demo:flour-all-purpose-500g'

@pytest.fixture
def web(tmp_path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'checkout.sqlite3'}")
    init_db(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions.begin() as db:
        seed_catalog(db)
    app = create_app(database_engine=engine)
    def database():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app, raise_server_exceptions=False) as client:
        client.get('/api/v1/bootstrap')
        yield client, sessions
    engine.dispose()


def prepared(client):
    cart = client.get('/api/v1/cart')
    assert cart.status_code == 200
    added = client.post('/api/v1/cart/items', json={'sku_id': SKU, 'quantity': 2, 'expected_cart_version': cart.json()['version']})
    assert added.status_code == 200
    preview = client.post('/api/v1/checkout/preview', json={'expected_cart_version': added.json()['version']})
    assert preview.status_code == 200
    return added.json(), preview.json()


def confirm(client, preview, key='key-1', **extra):
    return client.post('/api/v1/checkout/confirm', json={'preview_id': preview['preview_id'], 'idempotency_key': key, 'confirmed': True, **extra})


def test_shelf_checkout_explicit_confirm_replay_owner_and_snapshot(web):
    client, sessions = web
    cart, preview = prepared(client)
    assert client.get('/api/v1/orders').json() == {'items': []}
    assert confirm(client, preview, confirmed=False).status_code == 422
    response = confirm(client, preview)
    assert response.status_code == 200, response.text
    receipt = response.json()
    assert receipt['order']['items'] == preview['items']
    assert receipt['order']['status'] == 'submitted'
    assert receipt['order']['version'] == 1
    assert client.get('/api/v1/cart').json()['items'] == []
    assert confirm(client, preview).json() == receipt
    assert confirm(client, preview, key='new-key').status_code == 409
    order_id = receipt['order']['order_id']
    with sessions.begin() as db:
        offer = db.query(Offer).filter_by(sku_id=SKU).one()
        offer.price_fen += 100
    assert client.get('/api/v1/orders/' + order_id).json() == receipt['order']
    owner_cookie = client.cookies.get('sg_owner_id')
    client.cookies.clear()
    client.get('/api/v1/bootstrap')
    assert client.get('/api/v1/orders').json() == {'items': []}
    assert client.get('/api/v1/orders/' + order_id).status_code == 404
    assert confirm(client, preview).status_code == 404
    client.cookies.clear()
    client.cookies.set('sg_owner_id', owner_cookie)
    assert len(client.get('/api/v1/orders').json()['items']) == 1


def test_changed_cart_and_offer_require_new_preview(web):
    client, sessions = web
    cart, preview = prepared(client)
    with sessions.begin() as db:
        offer = db.query(Offer).filter_by(sku_id=SKU).one()
        offer.price_fen += 100
        offer.offer_version += 1
    assert confirm(client, preview).status_code == 409
    preview = client.post('/api/v1/checkout/preview', json={'expected_cart_version': cart['version']}).json()
    added = client.post('/api/v1/cart/items', json={'sku_id': SKU, 'quantity': 1, 'expected_cart_version': cart['version']})
    assert added.status_code == 200
    assert confirm(client, preview).status_code == 409
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 3
    assert client.get('/api/v1/orders').json() == {'items': []}


def test_shopping_write_hold_preserves_reads_and_facts(web, monkeypatch):
    from app.core.config import get_settings
    client, _ = web
    cart, preview = prepared(client)
    monkeypatch.setenv('SHOPPING_WRITES_PAUSED', 'true')
    get_settings.cache_clear()
    assert confirm(client, preview).status_code == 503
    assert client.post('/api/v1/checkout/preview', json={'expected_cart_version': cart['version']}).status_code == 503
    assert client.post('/api/v1/cart/items', json={'sku_id': SKU, 'quantity': 1, 'expected_cart_version': cart['version']}).status_code == 503
    assert client.patch('/api/v1/cart/items/' + SKU, json={'quantity': 1, 'expected_cart_version': cart['version']}).status_code == 503
    assert client.delete('/api/v1/cart/items/' + SKU, params={'expected_cart_version': cart['version']}).status_code == 503
    assert client.get('/api/v1/cart').json() == cart
    assert client.get('/api/v1/orders').json() == {'items': []}
    monkeypatch.delenv('SHOPPING_WRITES_PAUSED')
    get_settings.cache_clear()


def test_precommit_failure_rolls_back_and_postcommit_loss_replays(web, monkeypatch):
    from sqlalchemy.orm import Session
    from app.models.checkout import CheckoutReceipt
    client, sessions = web
    cart, preview = prepared(client)
    original = Session.commit
    def fail_before(db):
        if any(isinstance(row, CheckoutReceipt) for row in db.new):
            raise RuntimeError('controlled before business commit')
        return original(db)
    with monkeypatch.context() as patch:
        patch.setattr(Session, 'commit', fail_before)
        assert confirm(client, preview).status_code == 500
    assert client.get('/api/v1/cart').json() == cart
    assert client.get('/api/v1/orders').json() == {'items': []}
    def lose_after(db):
        checkout = any(isinstance(row, CheckoutReceipt) for row in db.new)
        original(db)
        if checkout:
            raise RuntimeError('controlled lost committed response')
    with monkeypatch.context() as patch:
        patch.setattr(Session, 'commit', lose_after)
        assert confirm(client, preview).status_code == 500
    replay = confirm(client, preview)
    assert replay.status_code == 200
    assert len(client.get('/api/v1/orders').json()['items']) == 1
    assert client.get('/api/v1/cart').json()['items'] == []
    with sessions() as db:
        assert db.query(CheckoutReceipt).count() == 1


def test_concurrent_same_key_and_cart_add_never_lose_items(web):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    client, _ = web
    cart, preview = prepared(client)
    barrier = Barrier(2)
    cookie = client.cookies.get('sg_owner_id')
    def submit():
        with TestClient(client.app) as other:
            other.cookies.set('sg_owner_id', cookie)
            barrier.wait(timeout=10)
            return confirm(other, preview)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: submit(), range(2)))
    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    cart, preview = prepared(client)
    barrier = Barrier(2)
    def compete(checkout):
        with TestClient(client.app) as other:
            other.cookies.set('sg_owner_id', cookie)
            barrier.wait(timeout=10)
            if checkout:
                return confirm(other, preview, key='competing-checkout')
            return other.post('/api/v1/cart/items', json={'sku_id': SKU, 'quantity': 1, 'expected_cart_version': cart['version']})
    with ThreadPoolExecutor(max_workers=2) as pool:
        checkout, addition = list(pool.map(compete, [True, False]))
    assert sorted([checkout.status_code, addition.status_code]) == [200, 409]
    remaining = client.get('/api/v1/cart').json()
    if addition.status_code == 200:
        assert remaining['items'][0]['quantity'] == 3
    else:
        retry = client.post('/api/v1/cart/items', json={'sku_id': SKU, 'quantity': 1, 'expected_cart_version': remaining['version']})
        assert retry.status_code == 200
        assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 1


def test_key_is_bound_to_preview_and_order_survives_new_app(web):
    client, sessions = web
    _, preview = prepared(client)
    receipt = confirm(client, preview).json()
    _, next_preview = prepared(client)
    assert confirm(client, next_preview).status_code == 409
    app = create_app(database_engine=sessions.kw['bind'])
    def database():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as restarted:
        restarted.cookies.set('sg_owner_id', client.cookies.get('sg_owner_id'))
        assert restarted.get('/api/v1/orders/' + receipt['order']['order_id']).json() == receipt['order']
        assert confirm(restarted, preview).json() == receipt


def test_nonempty_p02_snapshot_migrates_to_complete_public_projection_without_rewriting(tmp_path):
    import json
    from sqlalchemy import text
    engine = create_db_engine(f"sqlite:///{tmp_path / 'nonempty-old.sqlite3'}")
    snapshot = '{"items": [{"sku_id":"old-sku","name":"旧订单杯子","quantity":2,"unit_price_fen":1234,"returnable":true,"return_policy_source":"synthetic-p02"}]}'
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE owners (id VARCHAR(64) PRIMARY KEY, created_at DATETIME NOT NULL)'))
        conn.execute(text("INSERT INTO owners VALUES ('owner-old', '2026-10-01 00:00:00')"))
        conn.execute(text('CREATE TABLE simulated_orders (order_id VARCHAR(64) PRIMARY KEY, owner_id VARCHAR(64) NOT NULL, status VARCHAR(32) NOT NULL, snapshot_json TEXT NOT NULL, total_fen INTEGER NOT NULL, created_at DATETIME NOT NULL, delivered_at DATETIME)'))
        conn.execute(text("INSERT INTO simulated_orders VALUES ('old-nonempty', 'owner-old', 'delivered', :snapshot, 2468, '2026-10-01 00:00:00', NULL)"), {'snapshot': snapshot})
    init_db(engine)
    init_db(engine)
    sessions = sessionmaker(bind=engine)
    app = create_app(database_engine=engine)
    def database():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        client.cookies.set('sg_owner_id', 'owner-old')
        response = client.get('/api/v1/orders/old-nonempty')
        assert response.status_code == 200
        order = response.json()
        expected = {**json.loads(snapshot)['items'][0], 'line_total_fen': 2468,
                    'image_path': None, 'offer_version': None}
        assert order['items'] == [expected]
        assert order['store_id'] is None
        assert order['version'] == 1
        assert client.get('/api/v1/orders').json()['items'] == [order]
        from pathlib import Path
        artifact = Path(__file__).resolve().parents[2] / 'work/clean-rebuild/12/order-projection.json'
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(json.dumps(order, ensure_ascii=False))
    with engine.connect() as conn:
        assert conn.execute(text('SELECT snapshot_json FROM simulated_orders')).scalar_one() == snapshot
    engine.dispose()

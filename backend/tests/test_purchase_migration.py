"""Additive purchase schema and fixture-backed delivery provenance."""
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.core.database import create_db_engine, init_db
from app.models.store import Store
from app.services.seed_service import seed_catalog
from test_runtime_pi_product_query import pi_client


def test_synthetic_old_delivery_stays_unknown_and_upgrade_is_repeatable(tmp_path):
    engine = create_db_engine(f'sqlite:///{tmp_path}/old.sqlite3')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE stores (store_id VARCHAR(64) PRIMARY KEY, name VARCHAR(128), is_demo BOOLEAN, delivery_zone_id VARCHAR(64))'))
        connection.execute(text("INSERT INTO stores VALUES ('old-store','原模拟店',1,'old-zone')"))
    init_db(engine)
    init_db(engine)
    with engine.connect() as connection:
        assert tuple(connection.execute(text('SELECT name,delivery_zone_id,delivery_reachable,delivery_version FROM stores')).one()) == ('原模拟店','old-zone',None,1)
        assert connection.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='0004_purchase_confirmation'")).scalar_one() == 1
        assert {'purchase_confirmations','purchase_ledger'} <= set(inspect(connection).get_table_names())
        # Additive rollback: previous store readers preserve original facts.
        assert connection.execute(text('SELECT name FROM stores')).scalar_one() == '原模拟店'
    engine.dispose()


def test_fresh_seed_delivery_is_explicit_and_repeated_seed_preserves_changes(tmp_path):
    engine = create_db_engine(f'sqlite:///{tmp_path}/fresh.sqlite3')
    init_db(engine)
    with Session(engine) as db:
        seed_catalog(db)
        db.commit()
        store = db.get(Store,'store-demo-01')
        assert store.delivery_reachable is True
        assert store.delivery_version == 1
        store.delivery_reachable = False
        store.delivery_version = 2
        db.commit()
        seed_catalog(db)
        db.commit()
        db.refresh(store)
        assert store.delivery_reachable is False
        assert store.delivery_version == 2
    engine.dispose()


def test_confirmed_cart_ledger_receipt_survive_repeated_upgrade_and_hold(pi_client, monkeypatch):
    from test_purchase_public import prepare, confirmation_body
    from test_guide_lifecycle import BASE
    from app.core.config import get_settings
    client, requests = pi_client
    state = prepare(client, requests)
    url = '/api/v1/guide/tasks/' + state['task_id'] + '/confirm'
    body = confirmation_body(state)
    receipt = client.post(url,json=body,headers={'Idempotency-Key':'durable-purchase'}).json()
    init_db(requests.engine)
    init_db(requests.engine)
    monkeypatch.setenv('SHOPPING_WRITES_PAUSED','true')
    get_settings.cache_clear()
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2
    restored = client.get(BASE).json()
    assert restored['plan']['items'][0]['added_quantity'] == 2
    assert restored['confirmation_result'] == receipt
    assert client.post(url,json=body,headers={'Idempotency-Key':'durable-purchase'}).json() == receipt

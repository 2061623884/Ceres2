"""Public retained frontend bootstrap/catalog contract on a fresh database."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, create_db_engine, get_db, init_db
from app.main import create_app
from app.models.store import Offer
from app.services.seed_service import seed_catalog


@pytest.fixture
def web(tmp_path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'business.sqlite3'}")
    init_db(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        seed_catalog(db)
        db.commit()
    app = create_app(database_engine=engine)
    def database():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        yield client, sessions
    engine.dispose()


def test_bootstrap_uses_persistent_server_identity(web):
    client, _ = web
    response = client.get('/api/v1/bootstrap')
    assert response.status_code == 200
    first = response.json()
    assert first['owner_id'].startswith('owner-')
    assert first['store_id'] == 'store-demo-01'
    assert first['business_data_mode'] == 'demo'
    assert 'httponly' in response.headers['set-cookie'].lower()
    assert client.get('/api/v1/bootstrap').json()['owner_id'] == first['owner_id']
    client.cookies.clear()
    client.cookies.set('sg_owner_id', 'untrusted-owner')
    second = client.get('/api/v1/bootstrap').json()
    assert second['owner_id'] not in (first['owner_id'], 'untrusted-owner')


def test_catalog_returns_real_seeded_products_and_current_offer(web):
    client, sessions = web
    categories = client.get('/api/v1/categories').json()
    assert sum(c['product_count'] for c in categories) == 71
    listing = client.get('/api/v1/products', params={'page_size': 500}).json()
    assert listing['total'] == 71
    assert len(listing['items']) == 71  # existing70 + demo shrimp for the selected recipe fixture
    assert 'demo:snack-original-potato-chips-35g-bag' in {p['sku_id'] for p in listing['items']}
    assert all(p['price_fen'] > 0 for p in listing['items'])
    sku = 'demo:flour-all-purpose-500g'
    with sessions() as db:
        offer = db.scalar(select(Offer).where(Offer.sku_id == sku))
        offer.price_fen = 1234
        db.commit()
        seed_catalog(db)
        db.commit()
    detail = client.get(f'/api/v1/products/{sku}').json()
    assert detail['price_fen'] == 1234  # repeated seed must not reset business facts
    assert detail['spec_quantity'] == 500
    assert detail['spec_unit'] == 'g'
    assert detail['image_path'] == '/media/images/demo-flour-all-purpose-500g.jpg'
    image = client.get(detail['image_path'])
    assert image.status_code == 200
    assert image.headers['content-type'] == 'image/jpeg'
    assert image.content.startswith(b'\xff\xd8')
    filtered = client.get('/api/v1/products', params={'q': '中筋面粉'}).json()
    assert sku in [p['sku_id'] for p in filtered['items']]
    missing = client.get('/api/v1/products/unknown')
    assert missing.status_code == 404
    assert missing.json()['error']['code'] == 'PRODUCT_NOT_FOUND'


def test_schema_initialization_is_repeatable(tmp_path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'new.sqlite3'}")
    init_db(engine)
    init_db(engine)
    assert 'owners' in Base.metadata.tables
    engine.dispose()


def test_repeat_seed_corrects_chips_procurement_without_resetting_offer(web):
    import json
    from app.models.catalog import CatalogProduct
    client, sessions = web
    sku = 'demo:snack-original-potato-chips-70g-bag'
    with sessions.begin() as db:
        product = db.get(CatalogProduct, sku)
        product.ingredient_ids = json.dumps(['potato'])
        offer = db.scalar(select(Offer).where(Offer.sku_id == sku))
        offer.price_fen, offer.available_qty, offer.offer_version = 777, 2, 3
    with sessions.begin() as db:
        seed_catalog(db)
    with sessions() as db:
        assert 'potato' not in json.loads(db.get(CatalogProduct, sku).ingredient_ids)
        offer = db.scalar(select(Offer).where(Offer.sku_id == sku))
        assert (offer.price_fen, offer.available_qty, offer.offer_version) == (777, 2, 3)
    assert client.get('/api/v1/products/'+sku).json()['price_fen'] == 777


def test_schema_initialization_preserves_unrelated_existing_facts(tmp_path):
    from sqlalchemy import text
    engine = create_db_engine(f"sqlite:///{tmp_path / 'older.sqlite3'}")
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE retained_fact (id INTEGER PRIMARY KEY, content TEXT NOT NULL)'))
        connection.execute(text("INSERT INTO retained_fact VALUES (1, 'keep exactly')"))
    init_db(engine)
    init_db(engine)
    with engine.connect() as connection:
        assert connection.execute(text('SELECT content FROM retained_fact')).scalar_one() == 'keep exactly'
        assert connection.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='0001_clean_query_baseline'")).scalar_one() == 1
    engine.dispose()

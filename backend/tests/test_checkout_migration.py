"""Incremental TASK12 schema upgrade preserves synthetic P02 business facts."""
from sqlalchemy import text
from app.core.database import create_db_engine, init_db


def test_existing_query_order_gets_no_invented_store_and_keeps_snapshot(tmp_path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'p02.sqlite3'}")
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE owners (id VARCHAR(64) PRIMARY KEY, created_at DATETIME NOT NULL)'))
        connection.execute(text("INSERT INTO owners VALUES ('owner-old', '2026-10-01 00:00:00')"))
        connection.execute(text('CREATE TABLE simulated_orders (order_id VARCHAR(64) PRIMARY KEY, owner_id VARCHAR(64) NOT NULL, status VARCHAR(32) NOT NULL, snapshot_json TEXT NOT NULL, total_fen INTEGER NOT NULL, created_at DATETIME NOT NULL, delivered_at DATETIME)'))
        connection.execute(text("INSERT INTO simulated_orders VALUES ('old-order', 'owner-old', 'delivered', :snapshot, 100, '2026-10-01 00:00:00', NULL)"), {'snapshot': '{"items":[],"preserve":"exact bytes"}'})
    init_db(engine)
    init_db(engine)
    with engine.connect() as connection:
        row = connection.execute(text('SELECT owner_id, snapshot_json, total_fen, store_id, version FROM simulated_orders')).one()
        assert tuple(row) == ('owner-old', '{"items":[],"preserve":"exact bytes"}', 100, None, 1)
        assert connection.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='0012_checkout_orders'")).scalar_one() == 1
    engine.dispose()

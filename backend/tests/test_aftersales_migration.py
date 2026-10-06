"""Additive TASK14 schema and backup rollback preserve canonical facts."""
import sqlite3
from sqlalchemy import inspect, text
from app.core.database import create_db_engine, init_db


def test_additive_upgrade_repeat_and_safe_backup_rollback(tmp_path):
    path=tmp_path/'prior.sqlite'; backup=tmp_path/'before.sqlite'
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE owners (id VARCHAR(64) PRIMARY KEY, created_at DATETIME NOT NULL);
        INSERT INTO owners VALUES ('synthetic', '2026-10-01');
        CREATE TABLE simulated_orders (order_id VARCHAR(64) PRIMARY KEY, owner_id VARCHAR(64) NOT NULL,
          status VARCHAR(32) NOT NULL, snapshot_json TEXT NOT NULL, total_fen INTEGER NOT NULL,
          created_at DATETIME NOT NULL, delivered_at DATETIME);
        INSERT INTO simulated_orders VALUES ('prior','synthetic','submitted','{"items":[],"preserve":"exact bytes"}',1234,'2026-10-01',NULL);
        """)
        db.commit()
        with sqlite3.connect(backup) as saved: db.backup(saved)
    engine=create_db_engine(f'sqlite:///{path}')
    init_db(engine);init_db(engine)
    with engine.connect() as db:
        assert set(('aftersales_proposals','aftersales_applications','aftersales_receipts')) <= set(inspect(db).get_table_names())
        assert db.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='0014_confirmed_aftersales'")).scalar_one()==1
        assert tuple(db.execute(text('SELECT owner_id,status,snapshot_json,total_fen FROM simulated_orders')).one()) == ('synthetic','submitted','{"items":[],"preserve":"exact bytes"}',1234)
        for table in ('aftersales_proposals','aftersales_applications','aftersales_receipts'):
            assert db.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one()==0
    engine.dispose()
    # Recovery is restoring the pre-upgrade backup with writers stopped, not
    # destructive downgrade of a database containing new application receipts.
    with sqlite3.connect(backup) as old:
        assert old.execute('SELECT status,total_fen FROM simulated_orders').fetchone()==('submitted',1234)
        assert old.execute("SELECT count(*) FROM sqlite_master WHERE name='aftersales_receipts'").fetchone()==(0,)

"""Incremental memory schema preserves synthetic pre-memory business data."""
from sqlalchemy import text
from app.core.database import create_db_engine, init_db


def test_memory_upgrade_is_additive_repeatable_and_safe_for_old_readers(tmp_path):
    engine = create_db_engine(f"sqlite:///{tmp_path/'pre-memory.sqlite3'}")
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE synthetic_order_fact (id TEXT PRIMARY KEY, total_fen INTEGER)'))
        connection.execute(text("INSERT INTO synthetic_order_fact VALUES ('preserved-order', 1234)"))
    init_db(engine)
    init_db(engine)
    with engine.connect() as connection:
        assert tuple(connection.execute(text('SELECT id,total_fen FROM synthetic_order_fact')).one()) == ('preserved-order',1234)
        assert connection.execute(text('SELECT COUNT(*) FROM shopping_memories')).scalar_one() == 0
        assert connection.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='0009_explicit_role_memory'")).scalar_one() == 1
    engine.dispose()

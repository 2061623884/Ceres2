"""Public initialization seam, synthetic pre-upgrade rows, no copied state."""
from sqlalchemy import inspect, text
from app.core.database import create_db_engine, init_db


def test_photo_and_event_time_upgrade_preserves_legacy_facts_and_unknown_time(tmp_path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'synthetic-prior.sqlite'}")
    with engine.begin() as db:
        db.execute(text('CREATE TABLE guide_run_events (run_id TEXT, sequence INTEGER, type TEXT, payload_json TEXT, PRIMARY KEY(run_id, sequence))'))
        db.execute(text("INSERT INTO guide_run_events VALUES ('synthetic-old-run', 1, 'completed', :payload)"), {'payload': '{"original":"unchanged"}'})
        db.execute(text('CREATE TABLE simulated_orders (order_id TEXT PRIMARY KEY, owner_id TEXT, status TEXT, snapshot_json TEXT, total_fen INTEGER, created_at DATETIME, delivered_at DATETIME)'))
        db.execute(text("INSERT INTO simulated_orders VALUES ('synthetic-order','synthetic-owner','submitted',:snapshot,1234,'2026-10-01',NULL)"), {'snapshot': '{"items":[],"original":"unchanged"}'})
    init_db(engine)
    init_db(engine)
    with engine.connect() as db:
        assert 'aftersales_photos' in inspect(db).get_table_names()
        assert db.execute(text('SELECT COUNT(*) FROM aftersales_photos')).scalar_one() == 0
        assert tuple(db.execute(text('SELECT recorded_at_ms,payload_json FROM guide_run_events')).one()) == (None, '{"original":"unchanged"}')
        assert tuple(db.execute(text('SELECT status,snapshot_json,total_fen FROM simulated_orders')).one()) == ('submitted', '{"items":[],"original":"unchanged"}', 1234)
        for marker in ('integration_aftersales_photos_v1', 'optimization_run_event_time_v1'):
            assert db.execute(text('SELECT COUNT(*) FROM schema_migrations WHERE version=:version'), {'version': marker}).scalar_one() == 1
    engine.dispose()


def test_existing_applications_get_nullable_ticket_link_without_invented_association(tmp_path):
    import pytest
    from sqlalchemy.exc import IntegrityError
    engine = create_db_engine(f"sqlite:///{tmp_path / 'synthetic-applications.sqlite'}")
    with engine.begin() as db:
        db.execute(text('''CREATE TABLE aftersales_applications (
            application_id TEXT PRIMARY KEY, owner_id TEXT, case_id TEXT, proposal_id TEXT,
            order_id TEXT, kind TEXT, item_scope TEXT, amount_fen INTEGER, status TEXT)'''))
        db.execute(text("INSERT INTO aftersales_applications VALUES ('old-app','owner','case','proposal','order','return','sku',617,'requested')"))
    init_db(engine)
    init_db(engine)
    with engine.connect() as db:
        assert tuple(db.execute(text('SELECT application_id,kind,amount_fen,status,human_ticket_id FROM aftersales_applications')).one()) == ('old-app', 'return', 617, 'requested', None)
        assert db.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='integration_ticket_application_link_v1'")).scalar_one() == 1
        links = inspect(db).get_foreign_keys('aftersales_applications')
        assert any(link['constrained_columns'] == ['human_ticket_id'] and link['referred_table'] == 'human_tickets' for link in links)
    with engine.begin() as db:
        with pytest.raises(IntegrityError):
            db.execute(text("UPDATE aftersales_applications SET human_ticket_id='nonexistent'"))
    engine.dispose()

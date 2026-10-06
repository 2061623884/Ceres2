"""Review-time additive proposal lifecycle upgrade retains immutable payloads."""
from sqlalchemy import text
from app.core.database import create_db_engine, init_db


def test_existing_proposal_gets_default_lifecycle_without_payload_rewrite(tmp_path):
    engine=create_db_engine(f"sqlite:///{tmp_path/'prior-proposal.sqlite'}")
    with engine.begin() as db:
        db.execute(text('''CREATE TABLE aftersales_proposals (
            proposal_id VARCHAR(64) PRIMARY KEY, owner_id VARCHAR(64) NOT NULL,
            case_id VARCHAR(64) NOT NULL, order_id VARCHAR(64) NOT NULL,
            revision INTEGER NOT NULL, selection_version INTEGER NOT NULL,
            responsibility_generation INTEGER NOT NULL, facts_hash VARCHAR(64) NOT NULL,
            preview_json TEXT NOT NULL)'''))
        db.execute(text('''INSERT INTO aftersales_proposals VALUES
            ('prior-preview','fixture-owner','fixture-case','fixture-order',1,1,1,'fixture-hash',:preview)'''),
            {'preview':'{"reason":"原始原因","preserve":"exact bytes"}'})
    init_db(engine);init_db(engine)
    with engine.connect() as db:
        result=tuple(db.execute(text('SELECT invalidated,preview_json,revision,facts_hash FROM aftersales_proposals')).one())
        assert result==(0,'{"reason":"原始原因","preserve":"exact bytes"}',1,'fixture-hash')
        assert db.execute(text("SELECT count(*) FROM schema_migrations WHERE version='0014_confirmed_aftersales'")).scalar_one()==1
    engine.dispose()


def test_existing_case_gets_intent_anchor_without_changing_history(tmp_path):
    engine=create_db_engine(f"sqlite:///{tmp_path/'prior-case.sqlite'}")
    with engine.begin() as db:
        db.execute(text('''CREATE TABLE mercury_cases (
            case_id VARCHAR(64) PRIMARY KEY, owner_id VARCHAR(64) NOT NULL,
            order_id VARCHAR(64), created_at DATETIME NOT NULL,
            selection_version INTEGER NOT NULL, responsibility VARCHAR(16) NOT NULL,
            responsibility_generation INTEGER NOT NULL, active_run_id VARCHAR(64),
            active_until FLOAT, messages_json TEXT NOT NULL, query_status VARCHAR(32) NOT NULL,
            tool_rounds INTEGER NOT NULL)'''))
        db.execute(text('''INSERT INTO mercury_cases VALUES
            ('prior-case','fixture-owner',NULL,'2026-10-05',3,'agent',7,NULL,NULL,:history,'ready',0)'''),
            {'history':'[{"role":"user","content":"保留原始历史"}]'})
    init_db(engine);init_db(engine)
    with engine.connect() as db:
        result=tuple(db.execute(text('SELECT aftersales_intent_version,selection_version,responsibility_generation,messages_json FROM mercury_cases')).one())
        assert result==(0,3,7,'[{"role":"user","content":"保留原始历史"}]')
    engine.dispose()

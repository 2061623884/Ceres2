"""TASK03 synthetic pre-upgrade preservation and restart recovery."""
from sqlalchemy import text
from app.core.database import create_db_engine, init_db


def test_guide_upgrade_is_additive_repeatable_and_old_readers_keep_history(tmp_path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'p01.sqlite3'}")
    with engine.begin() as c:
        c.execute(text('CREATE TABLE guide_tasks (task_id VARCHAR(80) PRIMARY KEY, session_id VARCHAR(80), owner_id VARCHAR(80), state_version INTEGER, current_step VARCHAR(40), status VARCHAR(40), plan_json TEXT)'))
        c.exec_driver_sql("INSERT INTO guide_tasks VALUES ('old-task', 'old-session', 'old-owner', 7, 'understanding', 'active', '{\"preserve\":true}')")
        c.execute(text('CREATE TABLE guide_turn_receipts (run_id VARCHAR(80) PRIMARY KEY, session_id VARCHAR(80), owner_id VARCHAR(80), request_id VARCHAR(100), digest VARCHAR(64), status VARCHAR(30), result_json TEXT)'))
        c.execute(text("INSERT INTO guide_turn_receipts VALUES ('old-run', 'old-session', 'old-owner', 'old-request', 'old-digest', 'completed', '{\"message\":\"旧结果\"}')"))
    init_db(engine)
    init_db(engine)
    with engine.connect() as c:
        assert tuple(c.execute(text('SELECT state_version, plan_json, goal, conditions_json FROM guide_tasks')).one()) == (7, '{"preserve":true}', None, '{}')
        assert tuple(c.execute(text('SELECT status, result_json, input_json, anchor_json, execution_id FROM guide_turn_receipts')).one()) == ('completed', '{"message":"旧结果"}', '{}', '{}', None)
        # Safe application rollback is additive: old-column reads still work.
        assert c.execute(text('SELECT plan_json FROM guide_tasks')).scalar_one() == '{"preserve":true}'
        assert c.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='0003_responsive_runs'")).scalar_one() == 1
    engine.dispose()

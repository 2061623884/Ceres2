"""Clean baseline and ticket-scoped additive business migrations."""
from sqlalchemy import inspect, text
from app.core.database import Base


def initialize_schema(bind) -> None:
    with bind.begin() as connection:
        Base.metadata.create_all(connection)
        connection.execute(text('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)'))
        connection.execute(text("INSERT INTO schema_migrations(version) SELECT '0001_clean_query_baseline' WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '0001_clean_query_baseline')"))
        # P12 keeps P02 synthetic order facts; unknown prior stores stay unknown.
        columns = {column['name'] for column in inspect(connection).get_columns('simulated_orders')}
        if 'store_id' not in columns:
            connection.execute(text('ALTER TABLE simulated_orders ADD COLUMN store_id VARCHAR(64)'))
        if 'version' not in columns:
            connection.execute(text('ALTER TABLE simulated_orders ADD COLUMN version INTEGER NOT NULL DEFAULT 1'))
        connection.execute(text("INSERT INTO schema_migrations(version) SELECT '0012_checkout_orders' WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '0012_checkout_orders')"))
        # P03 introduces durable run metadata without rewriting prior history.
        task_columns = {column['name'] for column in inspect(connection).get_columns('guide_tasks')}
        if 'goal' not in task_columns:
            connection.execute(text('ALTER TABLE guide_tasks ADD COLUMN goal TEXT'))
        if 'conditions_json' not in task_columns:
            connection.execute(text("ALTER TABLE guide_tasks ADD COLUMN conditions_json TEXT NOT NULL DEFAULT '{}'"))
        receipt_columns = {column['name'] for column in inspect(connection).get_columns('guide_turn_receipts')}
        for name, definition in (
            ('input_json', "TEXT NOT NULL DEFAULT '{}'"),
            ('anchor_json', "TEXT NOT NULL DEFAULT '{}'"),
            ('execution_id', 'VARCHAR(200)'),
            ('started_at', 'FLOAT'),
        ):
            if name not in receipt_columns:
                connection.execute(text(f'ALTER TABLE guide_turn_receipts ADD COLUMN {name} {definition}'))
        connection.execute(text("INSERT INTO schema_migrations(version) SELECT '0003_responsive_runs' WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '0003_responsive_runs')"))
        # P15 tables are additive and share the canonical business transaction.
        connection.execute(text("INSERT INTO schema_migrations(version) SELECT '0015_async_human_tickets' WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '0015_async_human_tickets')"))
        # P14 proposal/application/receipt tables preserve canonical case/order rows.
        case_columns = {column['name'] for column in inspect(connection).get_columns('mercury_cases')}
        if 'aftersales_intent_version' not in case_columns:
            connection.execute(text('ALTER TABLE mercury_cases ADD COLUMN aftersales_intent_version INTEGER NOT NULL DEFAULT 0'))
        proposal_columns = {column['name'] for column in inspect(connection).get_columns('aftersales_proposals')}
        if 'invalidated' not in proposal_columns:
            connection.execute(text('ALTER TABLE aftersales_proposals ADD COLUMN invalidated BOOLEAN NOT NULL DEFAULT 0'))
        connection.execute(text("INSERT INTO schema_migrations(version) SELECT '0014_confirmed_aftersales' WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '0014_confirmed_aftersales')"))
        # P04 prior stores retain unknown reachability; only fresh fixture seed
        # can attest the matching delivery zone, never this schema migration.
        store_columns = {column['name'] for column in inspect(connection).get_columns('stores')}
        if 'delivery_reachable' not in store_columns:
            connection.execute(text('ALTER TABLE stores ADD COLUMN delivery_reachable BOOLEAN'))
        if 'delivery_version' not in store_columns:
            connection.execute(text('ALTER TABLE stores ADD COLUMN delivery_version INTEGER NOT NULL DEFAULT 1'))
        connection.execute(text("INSERT INTO schema_migrations(version) SELECT '0004_purchase_confirmation' WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '0004_purchase_confirmation')"))
        # P09 canonical memory is a new additive table, with no legacy import.
        connection.execute(text("INSERT INTO schema_migrations(version) SELECT '0009_explicit_role_memory' WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '0009_explicit_role_memory')"))
        # P10 MemoryJob is additive; existing memories and tombstones stay intact.
        connection.execute(text("INSERT INTO schema_migrations(version) SELECT '0010_recoverable_memory' WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '0010_recoverable_memory')"))
        # P08 persists the current scoped comparison display, without changing plans.
        connection.execute(text("INSERT INTO schema_migrations(version) SELECT '0008_category_comparison' WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '0008_category_comparison')"))

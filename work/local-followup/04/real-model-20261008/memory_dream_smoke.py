"""One real Dream-worker call over isolated synthetic memory rows."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from harness_config import (
    MEMORY_DREAM_REQUIRED_FIELDS, SOURCE_ENV, apply_harness_environment,
    missing_fields, read_source_values,
)


WORKTREE = Path(__file__).resolve().parents[4]
DB_PATH = WORKTREE / "data/runtime/real-model-20261008/memory-dream-smoke.sqlite3"
CHECKPOINT_PATH = WORKTREE / "data/runtime/real-model-20261008/memory-dream-smoke-checkpoints.sqlite3"
MODEL_KEYS = MEMORY_DREAM_REQUIRED_FIELDS


def main() -> int:
    values = read_source_values(SOURCE_ENV)
    missing = missing_fields(values, MODEL_KEYS)
    if missing:
        print(json.dumps({"status": "not_run", "missing_fields": missing}, sort_keys=True))
        return 2

    # Only the current Settings model fields cross into this process; never emit them.
    selected_environment = {key: str(values[key]).strip() for key in MODEL_KEYS}
    selected_environment.update({
        "DATABASE_URL": f"sqlite:///{DB_PATH}",
        "MERCURY_CHECKPOINT_PATH": str(CHECKPOINT_PATH),
        "PYTHON_DOTENV_DISABLED": "1",
    })
    apply_harness_environment(selected_environment)

    # The application settings object must not consult a worktree .env in this harness.
    from app.core import config

    config.get_settings = lambda: config.Settings(_env_file=None)

    from app.core.database import Base, create_db_engine
    from app.models.identity import Owner
    from app.models.memory import MemoryJob, ShoppingMemory
    from app.services.memory_background import MemoryWorker
    from sqlalchemy.orm import Session

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        print(json.dumps({"status": "not_run", "reason": "isolated_database_already_exists"}, sort_keys=True))
        return 2
    engine = create_db_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine, tables=[Owner.__table__, ShoppingMemory.__table__, MemoryJob.__table__])
    now = time.time()
    owner_id = "synthetic-dream-smoke-owner"
    with Session(engine) as db:
        db.add(Owner(id=owner_id))
        for index in range(10):
            db.add(ShoppingMemory(
                memory_id=f"synthetic-memory-{index:02d}",
                owner_id=owner_id,
                category="user",
                domain="shopping",
                key=f"synthetic-preference-{index:02d}",
                content=f"Synthetic durable preference number {index}.",
                source="automatic",
                origin_role="keke",
                source_id=f"synthetic-source-{index:02d}",
                source_quote=f"Synthetic durable preference number {index}.",
                reference_url=None,
                revision=1,
                created_at=now,
                updated_at=now,
                expires_at=now + 30 * 86400,
                deleted_at=None,
            ))
        db.commit()

    worker = MemoryWorker(engine)
    try:
        processed = worker.run_once()
    except Exception as error:
        print(json.dumps({"status": "worker_error", "error_type": type(error).__name__}, sort_keys=True))
        return 1

    with Session(engine) as db:
        jobs = list(db.query(MemoryJob.kind, MemoryJob.status, MemoryJob.error_code).all())
        active = db.query(ShoppingMemory.memory_id).filter(
            ShoppingMemory.owner_id == owner_id,
            ShoppingMemory.source == "automatic",
            ShoppingMemory.deleted_at.is_(None),
            ShoppingMemory.expires_at > time.time(),
        ).count()
    statuses: dict[str, int] = {}
    errors: dict[str, int] = {}
    for kind, status, error_code in jobs:
        status_key = f"{kind}:{status}"
        statuses[status_key] = statuses.get(status_key, 0) + 1
        if error_code:
            errors[error_code] = errors.get(error_code, 0) + 1
    print(json.dumps({
        "status": "processed" if processed else "no_job",
        "model_id": str(values["MEMORY_DREAM_MODEL"]),
        "synthetic_input_records": 10,
        "job_statuses": statuses,
        "job_error_codes": errors,
        "active_synthetic_memory_rows": active,
        "usage_persisted": False,
        "database_path": str(DB_PATH.relative_to(WORKTREE)),
    }, sort_keys=True))
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

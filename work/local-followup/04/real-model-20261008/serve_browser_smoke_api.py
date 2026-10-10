"""Start production API on an isolated demo database for the browser smoke."""
from __future__ import annotations

import json
from pathlib import Path

from provider_job import BACKEND, RUNTIME, _apply_server_environment, _configure

DB_PATH = RUNTIME / "browser-smoke-final.sqlite3"
CHECKPOINT_PATH = RUNTIME / "browser-smoke-final-checkpoints.sqlite3"


def main() -> int:
    if DB_PATH.exists() or CHECKPOINT_PATH.exists():
        raise SystemExit("isolated browser database already exists")
    RUNTIME.mkdir(parents=True, exist_ok=True)
    env = _configure()
    env["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
    env["MERCURY_CHECKPOINT_PATH"] = str(CHECKPOINT_PATH)
    _apply_server_environment(env)
    import sys
    sys.path.insert(0, str(BACKEND))
    from app.core.config import get_settings
    from app.core.database import SessionLocal, engine, init_db
    init_db(engine)
    from app.services.seed_service import seed_catalog
    with SessionLocal.begin() as session:
        seed_catalog(session)
    from app.main import app
    import uvicorn
    print(json.dumps({
        "stage": "browser_api_seeded",
        "status": "ready_to_bind",
        "database_path": str(DB_PATH),
        "checkpoint_path": str(CHECKPOINT_PATH),
        "model_id": get_settings().llm_model,
        "business_data_mode": get_settings().business_data_mode,
    }, sort_keys=True), flush=True)
    uvicorn.run(app, host="127.0.0.1", port=8015, log_level="warning", access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Start the Kev-enabled Ceres baseline API on fresh, isolated runtime paths."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / 'backend'
HARNESS_CONFIG_DIR = ROOT / 'work/local-followup/04/real-model-20261008'
RUNTIME = ROOT / 'data/runtime/kev-followup-20261009/baseline'
API_HOST = '127.0.0.1'
API_PORT = 8017
KEV_BASE_URL = 'http://127.0.0.1:8009'

sys.path.insert(0, str(HARNESS_CONFIG_DIR))
from harness_config import (
    MEMORY_DREAM_REQUIRED_FIELDS,
    SOURCE_ENV,
    apply_harness_environment,
    missing_fields,
    read_source_values,
)


def _configure() -> dict[str, str]:
    values = read_source_values(SOURCE_ENV)
    if missing_fields(values, MEMORY_DREAM_REQUIRED_FIELDS):
        raise RuntimeError('approved provider and Memory fields incomplete')

    RUNTIME.mkdir(parents=True, exist_ok=True)
    temporary = RUNTIME / 'tmp'
    temporary.mkdir(parents=True, exist_ok=True)
    os.chmod(temporary, 0o700)

    return {
        'DATABASE_URL': 'sqlite:///' + str(RUNTIME / 'ceres2.sqlite3'),
        'MERCURY_CHECKPOINT_PATH': str(RUNTIME / 'mercury-checkpoints.sqlite3'),
        'BUSINESS_DATA_MODE': 'demo',
        'OPENAI_BASE_URL': str(values['OPENAI_BASE_URL']).strip(),
        'OPENAI_API_KEY': str(values['OPENAI_API_KEY']).strip(),
        'LLM_MODEL': str(values['LLM_MODEL']).strip(),
        'LLM_MODE': str(values['LLM_MODE']).strip(),
        'MEMORY_EXTRACTION_MODEL': str(values['MEMORY_EXTRACTION_MODEL']).strip(),
        'MEMORY_DREAM_MODEL': str(values['MEMORY_DREAM_MODEL']).strip(),
        'KEV_BASE_URL': KEV_BASE_URL,
        'TMPDIR': str(temporary),
        'OMP_NUM_THREADS': '2',
        'MKL_NUM_THREADS': '2',
        'OPENBLAS_NUM_THREADS': '2',
        'TOKENIZERS_PARALLELISM': 'false',
    }


def _apply_server_environment(selected: dict[str, str]) -> None:
    apply_harness_environment(selected)
    from app.core.config import Settings, get_settings

    Settings.model_config['env_file'] = None
    get_settings.cache_clear()


def _serve() -> int:
    from app.core.config import get_settings
    from app.core.database import SessionLocal, engine, init_db

    init_db(engine)
    from app.services.seed_service import seed_catalog

    with SessionLocal.begin() as session:
        seed_catalog(session)

    from app.main import app
    import uvicorn

    # The application lifespan starts the production MemoryWorker. Hybrid and
    # GraphRAG indexes remain the already-built worktree indexes; this entrypoint
    # never rebuilds either index.
    settings = get_settings()
    print(json.dumps({
        'stage': 'kev_baseline_server',
        'status': 'ready_to_bind',
        'host': API_HOST,
        'port': API_PORT,
        'model_id': settings.llm_model,
        'database_path': str(RUNTIME / 'ceres2.sqlite3'),
        'checkpoint_path': str(RUNTIME / 'mercury-checkpoints.sqlite3'),
    }, ensure_ascii=False), flush=True)
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level='warning', access_log=False)
    return 0


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    selected = _configure()
    _apply_server_environment(selected)
    return _serve()


if __name__ == '__main__':
    raise SystemExit(main())

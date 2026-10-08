"""Controlled live-provider harness; never logs config values or generated text."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / 'backend'
SOURCE_ENV = Path('/data/amax/Documents/projects/Agent/Agent产品/Ceres2/.env')
EVIDENCE = ROOT / 'work/local-followup/04/real-model-20261008'
TMP = EVIDENCE / 'tmp'
BOOTSTRAP = EVIDENCE / 'runtime_bootstrap'
RUNTIME = ROOT / 'data/runtime/real-model-20261008'


def _configure() -> dict:
    from dotenv import dotenv_values
    values = dotenv_values(SOURCE_ENV, interpolate=False)
    required = ('OPENAI_BASE_URL', 'OPENAI_API_KEY', 'LLM_MODEL', 'LLM_MODE')
    if any(not str(values.get(k) or '').strip() for k in required):
        raise RuntimeError('approved main-provider fields incomplete')
    RUNTIME.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(BACKEND))
    from app.core.config import Settings, get_settings
    Settings.model_config['env_file'] = None
    get_settings.cache_clear()

    node = shutil.which('node')
    node_bin = str(Path(node).resolve().parent) if node else ''
    base_path = os.environ.get('PATH', '')
    env = {
        'PATH': node_bin + os.pathsep + base_path if node_bin else base_path,
        'HOME': os.environ['HOME'],
        'LANG': os.environ.get('LANG', 'C.UTF-8'),
        'LC_ALL': os.environ.get('LC_ALL', 'C.UTF-8'),
        'TMPDIR': str(TMP),
        'PYTHONPATH': os.pathsep.join((str(BACKEND), str(BOOTSTRAP))),
        'DATABASE_URL': 'sqlite:///' + str(RUNTIME / 'ceres2.sqlite3'),
        'MERCURY_CHECKPOINT_PATH': str(RUNTIME / 'mercury-checkpoints.sqlite3'),
        'BUSINESS_DATA_MODE': 'demo',
        'OPENAI_BASE_URL': str(values['OPENAI_BASE_URL']).strip(),
        'OPENAI_API_KEY': str(values['OPENAI_API_KEY']).strip(),
        'LLM_MODEL': str(values['LLM_MODEL']).strip(),
        'LLM_MODE': str(values['LLM_MODE']).strip(),
        'MEMORY_EXTRACTION_MODEL': str(values.get('MEMORY_EXTRACTION_MODEL') or '').strip(),
        'MEMORY_DREAM_MODEL': str(values.get('MEMORY_DREAM_MODEL') or '').strip(),
        'OMP_NUM_THREADS': '2',
        'MKL_NUM_THREADS': '2',
        'OPENBLAS_NUM_THREADS': '2',
        'TOKENIZERS_PARALLELISM': 'false',
    }
    if str(values.get('KEV_BASE_URL') or '').strip():
        env['KEV_BASE_URL'] = str(values['KEV_BASE_URL']).strip()
    for name in ('HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy', 'no_proxy',
                 'SSL_CERT_FILE', 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE', 'NODE_EXTRA_CA_CERTS'):
        if name in os.environ:
            env[name] = os.environ[name]
    os.chmod(TMP, 0o700)
    return env


def _host(base: str) -> str:
    return urlsplit(base).hostname or '<invalid-host>'


def _call_summary(calls) -> dict:
    from collections import Counter
    rows = list(calls or [])
    kinds = Counter((row.get('kind'), row.get('status')) for row in rows)
    tokens = Counter()
    for row in rows:
        usage = row.get('usage') or {}
        if row.get('usage_source') == 'provider':
            tokens[row.get('model') or '<unknown>'] += usage.get('total_tokens') or 0
    return {
        'count': len(rows),
        'kind_status': {f'{kind}:{status}': count for (kind, status), count in sorted(kinds.items())},
        'provider_total_tokens_by_model': dict(tokens),
    }


def provider_preflight(env: dict) -> int:
    from openai import OpenAI
    from app.core.deepseek_request import official_deepseek_thinking_body
    model, base = env['LLM_MODEL'], env['OPENAI_BASE_URL']
    client = OpenAI(api_key=env['OPENAI_API_KEY'], base_url=base, max_retries=0, timeout=25)
    started = time.monotonic()
    result = {'stage': 'main_provider_preflight', 'model_id': model, 'provider_host': _host(base)}
    try:
        response = client.chat.completions.create(model=model,
            messages=[{'role': 'user', 'content': '只回复：就绪'}], max_tokens=8,
            **({'extra_body': official_deepseek_thinking_body(base)} if official_deepseek_thinking_body(base) else {}))
        result.update(status='response_received', response_model=response.model,
            response_text_characters=len(response.choices[0].message.content or ''),
            usage=response.usage.model_dump() if response.usage is not None else None)
        code = 0
    except Exception as error:
        result.update(status='error', exception_type=type(error).__name__)
        code = 1
    result['duration_ms'] = round((time.monotonic() - started) * 1000, 1)
    print(json.dumps(result, ensure_ascii=False))
    return code


def graph_action(env: dict, action: str, *, query: str | None = None, method: str | None = None, timeout: int = 900) -> int:
    python = ROOT / '.venv-graphrag/bin/python'
    if action == 'build-graph':
        command = [str(python), '-m', 'app.knowledge.cli', 'build-graph', '--timeout-seconds', str(timeout)]
        output_name = 'graph-build'
    else:
        deadline = time.monotonic() + timeout
        command = [str(python), '-m', 'app.knowledge.cli', 'graph', '--query', query or '', '--method', method or 'local', '--deadline', str(deadline)]
        output_name = f'graph-{method}'
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=BACKEND, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout + 15, check=False)
        (TMP / f'{output_name}.stdout.json').write_bytes(result.stdout)
        (TMP / f'{output_name}.stderr.log').write_bytes(result.stderr)
        for name in (f'{output_name}.stdout.json', f'{output_name}.stderr.log'):
            os.chmod(TMP / name, 0o600)
    except subprocess.TimeoutExpired:
        print(json.dumps({'stage': output_name, 'status': 'outer_timeout', 'timeout_seconds': timeout}))
        return 124
    safe = {'stage': output_name, 'exit_code': result.returncode,
            'duration_ms': round((time.monotonic() - started) * 1000, 1),
            'stdout_bytes': len(result.stdout), 'stderr_bytes': len(result.stderr)}
    try:
        payload = json.loads(result.stdout)
        if isinstance(payload, dict):
            for key in ('error', 'graph_status', 'method', 'query_revision', 'official_graph_calls',
                        'call_counts', 'output_counts', 'graph_counts', 'provider_host',
                        'completion_model', 'graphrag', 'embedding_model', 'embedding_revision',
                        'dimensions', 'workflows', 'usage'):
                if key in payload:
                    safe[key] = payload[key]
            if 'calls' in payload:
                safe['call_summary'] = _call_summary(payload['calls'])
            if 'canonical_facts' in payload:
                safe['canonical_fact_count'] = len(payload['canonical_facts'])
                safe['selected_ids'] = [fact['id'] for fact in payload['canonical_facts']]
            if 'manifest' in payload:
                manifest = payload['manifest']
                for key in ('graph_revision', 'graphrag', 'completion_model', 'provider_host',
                            'embedding_model', 'embedding_revision', 'dimensions', 'workflows',
                            'output_counts', 'call_counts', 'official_graph_calls'):
                    if key in manifest:
                        safe.setdefault(key, manifest[key])
                if 'calls' in manifest and action == 'build-graph':
                    safe['call_summary'] = _call_summary(manifest['calls'])
    except (json.JSONDecodeError, UnicodeDecodeError):
        safe['stdout_json'] = False
    print(json.dumps(safe, ensure_ascii=False))
    return result.returncode


def serve(env: dict) -> int:
    from app.core.config import get_settings
    from app.core.database import SessionLocal, engine, init_db
    init_db(engine)
    from app.services.seed_service import seed_catalog
    with SessionLocal.begin() as session:
        seed_catalog(session)
    from app.main import app
    import uvicorn
    print(json.dumps({'stage': 'server_seeded', 'status': 'ready_to_bind',
        'database_path': str(RUNTIME / 'ceres2.sqlite3'), 'checkpoint_path': str(RUNTIME / 'mercury-checkpoints.sqlite3'),
        'model_id': get_settings().llm_model, 'operator_token_configured': bool(get_settings().human_operator_token),
        'business_data_mode': get_settings().business_data_mode}, ensure_ascii=False), flush=True)
    uvicorn.run(app, host='127.0.0.1', port=8015, log_level='warning', access_log=False)
    return 0


def main() -> int:
    mode = sys.argv[1]
    env = _configure()
    if mode == 'provider-preflight':
        return provider_preflight(env)
    if mode == 'build-graph':
        return graph_action(env, 'build-graph', timeout=int(sys.argv[2]) if len(sys.argv) > 2 else 900)
    if mode == 'graph-local':
        return graph_action(env, 'graph', query='番茄炒蛋需要哪些食材与商品', method='local', timeout=180)
    if mode == 'graph-global':
        return graph_action(env, 'graph', query='这批家常菜共有哪几类食材，哪些菜用鸡蛋', method='global', timeout=180)
    if mode == 'serve':
        os.environ.update(env)
        return serve(env)
    raise SystemExit('unsupported harness action')


if __name__ == '__main__':
    raise SystemExit(main())

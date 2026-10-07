"""Small execution-boundary fingerprints; never a claim about loaded code."""
import hashlib
import json
from pathlib import Path
import time
from contextvars import ContextVar

_RETRIEVAL = ContextVar('guide_retrieval_observation', default=None)


def begin_retrieval_observation(run_id, record):
    return _RETRIEVAL.set((run_id, record))


def end_retrieval_observation(token):
    _RETRIEVAL.reset(token)


def retrieval_observer():
    return _RETRIEVAL.get()


def retrieval_summary():
    return {'retrieval_calls': {namespace: {'started': 0, 'completed': 0, 'success': 0, 'empty': 0, 'error': 0}
                                for namespace in ('product', 'recipe', 'policy')}, 'retrieval_sources': []}


def record_retrieval(summary, event):
    counts = summary['retrieval_calls'][event['namespace']]
    if event['type'] == 'retrieval_start':
        counts['started'] += 1
    else:
        counts['completed'] += 1
        counts[event['outcome']] += 1
        source = {key: event[key] for key in ('namespace', 'source_revision', 'index_revision')}
        if source not in summary['retrieval_sources']:
            summary['retrieval_sources'].append(source)


def admission_version():
    root = Path(__file__).resolve().parents[3]
    files = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
             for folder in ('backend/app', 'runtime/pi/src', 'data/fixtures')
             for path in sorted((root / folder).rglob('*'))
             if path.is_file() and path.suffix in ('.py', '.ts', '.json')}
    return {'source_revision': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
            'source_scope': 'disk_at_admission', 'captured_at_ms': time.time() * 1000,
            'build_revision': None, 'build_scope': None, 'prompt_revision': None,
            'loaded_code_equivalence': 'unknown'}


def retained_observation(result_json):
    result = json.loads(result_json) if result_json else {}
    return {key: result[key] for key in ('runtime_version', 'entry_judgment', 'runtime_summary', 'runtime_events') if key in result}

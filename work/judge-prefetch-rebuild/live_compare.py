"""Inert-by-default preparation for a human-operated bounded comparison."""
import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import selectors
import signal
import subprocess
import tempfile
import time


CASES = {
    'policy': '一般退货需要满足哪些条件？',
    'mixed': '帮我选低糖饮品，顺便说明一般退货条件。',
    'chat': '你好。',
    'unmatched': '请查一下火星定制商品的退货条款。',
}
SOURCE_PATHS = ('backend/app', 'runtime/pi/src', 'data/fixtures',
                'backend/requirements.lock', 'runtime/pi/package-lock.json',
                'runtime/pi/package.json', 'runtime/pi/tsconfig.json')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     ensure_ascii=False).encode()).hexdigest()


def git(root, *args, limit=None):
    process = None
    try:
        if limit:
            limit()
        process = subprocess.Popen(
            ['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
             '-C', str(root), *args], stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, start_new_session=True,
        )
        local_deadline = time.monotonic() + 10
        while True:
            remaining = min(local_deadline-time.monotonic(), limit() if limit else 10)
            if remaining <= 0:
                raise InvalidPlan('source_git_unavailable')
            try:
                stdout, _ = process.communicate(timeout=min(.05, remaining))
                break
            except subprocess.TimeoutExpired:
                continue
        if limit:
            limit()
        if process.returncode != 0:
            raise InvalidPlan('source_git_unavailable')
        return stdout.decode().strip()
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise InvalidPlan('source_git_unavailable') from None
    finally:
        if process is not None:
            if process.returncode is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            process.stdout.close()


def file_hashes(root, names, limit=None):
    result = {}
    for name in sorted(names):
        if limit:
            limit()
        path = root / name
        if path.is_symlink() or path.name == '.env' or path.name.startswith('.env.'):
            raise InvalidPlan('unsupported_source_file')
        try:
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            raise InvalidPlan('source_file_unavailable') from None
    return result


def policy_facts(path):
    """Support the two reviewed static policy shapes without executing either."""
    try:
        module = ast.parse(path.read_text())
        assignments = {}
        for statement in module.body:
            if isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        assignments.setdefault(target.id, []).append(statement.value)

        def literal(expression):
            if isinstance(expression, ast.Name):
                values = assignments[expression.id]
                if len(values) != 1:
                    raise ValueError('ambiguous literal')
                expression = values[0]
            return ast.literal_eval(expression)

        functions = [node for node in module.body
                     if isinstance(node, ast.FunctionDef) and node.name == 'search_policies']
        if len(functions) != 1:
            raise ValueError('unsupported policy contract')
        sources = []
        for node in ast.walk(functions[0]):
            if not isinstance(node, ast.Dict):
                continue
            fields = {key.value: value for key, value in zip(node.keys, node.values)
                      if isinstance(key, ast.Constant) and isinstance(key.value, str)}
            if set(fields) == {'name', 'version', 'policy_id'}:
                sources.append({'name': literal(fields['name']), 'version': literal(fields['version'])})
        if len(sources) != 1:
            raise ValueError('unsupported source contract')
        return {'policies': literal(ast.Name(id='POLICIES')), 'source': sources[0]}
    except (OSError, UnicodeError, SyntaxError, ValueError, TypeError, KeyError):
        raise InvalidPlan('unsupported_policy_source') from None


def describe(root, limit=None):
    """Read files and Git metadata only; never import the selected application."""
    root = root.resolve()
    if limit:
        limit()
    if Path(git(root, 'rev-parse', '--show-toplevel', limit=limit)).resolve() != root:
        raise InvalidPlan('source_is_not_checkout_root')
    if git(root, 'status', '--porcelain', '--untracked-files=normal', '--', *SOURCE_PATHS, limit=limit):
        raise InvalidPlan('dirty_source')
    names = git(root, 'ls-files', '-z', '--', *SOURCE_PATHS, limit=limit).split('\0')
    names = [name for name in names if name]
    hashes = file_hashes(root, names, limit)
    dist = root / 'runtime/pi/dist'
    dist_names = [str(path.relative_to(root)) for path in dist.rglob('*') if path.is_file()]
    if not (dist / 'worker.js').is_file() or not (dist / 'result-expression.js').is_file():
        raise InvalidPlan('runtime_build_missing')
    # These existing numeric declarations are evidence, not new budgets. The
    # pair must match them; final payload alignment still needs manual review.
    patterns = {
        'backend/app/api/guide.py': [r'time\.monotonic\(\)\s*\+\s*(\d+(?:\.\d+)?)'],
        'backend/app/services/pi_product_runtime.py': [r'MAX_TOOL_ROUNDS\s*=\s*(\d+)'],
        'backend/app/services/kev_provider.py': [r'timeout\s*=\s*([A-Z_][A-Z_0-9]*|\d+(?:\.\d+)?)(?=[\s,)])'],
        'backend/app/services/memory_model.py': [r'timeout\s*=\s*(\d+)', r'max_retries\s*=\s*(\d+)', r'temperature\s*=\s*(\d+)'],
        'runtime/pi/src/worker.ts': [r'maxTokens\s*:\s*(\d+)'],
        'runtime/pi/src/result-expression.ts': [r'maxTokens\s*:\s*(\d+)'],
    }
    budgets = {}
    for name, expressions in patterns.items():
        if limit:
            limit()
        try:
            content = (root / name).read_text()
        except (OSError, UnicodeError):
            raise InvalidPlan('unsupported_budget_source') from None
        values = [re.findall(pattern, content) for pattern in expressions]
        if any(not matches for matches in values):
            raise InvalidPlan('unsupported_budget_source')
        if name == 'backend/app/services/kev_provider.py':
            # Accepted 02 names the unchanged entry timeout. Resolve that
            # literal declaration without importing configuration/provider code.
            try:
                module = ast.parse(content)
                for matches in values:
                    for index, token in enumerate(matches):
                        if not token[0].isalpha() and token[0] != '_':
                            continue
                        definitions = [node.value for node in module.body
                                       if isinstance(node, ast.Assign) and any(
                                           isinstance(target, ast.Name) and target.id == token
                                           for target in node.targets)]
                        if len(definitions) != 1:
                            raise ValueError('ambiguous timeout declaration')
                        value = ast.literal_eval(definitions[0])
                        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                            raise ValueError('unsupported timeout declaration')
                        matches[index] = str(value)
            except (SyntaxError, ValueError, TypeError, OverflowError):
                raise InvalidPlan('unsupported_budget_source') from None
        budgets[name] = values
    return {
        'directory': str(root),
        'revision': git(root, 'rev-parse', 'HEAD', limit=limit),
        'tree': git(root, 'rev-parse', 'HEAD^{tree}', limit=limit),
        'source_sha256': digest(hashes),
        'runtime_source_sha256': digest({k: v for k, v in hashes.items() if k.startswith('runtime/')}),
        'dist_sha256': digest(file_hashes(root, dist_names, limit)),
        'facts_sha256': digest({
            'fixtures': {k: v for k, v in hashes.items() if k.startswith('data/fixtures/')},
            'policy': policy_facts(root / 'backend/app/mercury/policy.py'),
        }),
        'prompts_sha256': digest({k: v for k, v in hashes.items() if '/prompts/' in k or k.endswith(('prompt-modules.ts', 'worker.ts', 'general-claim.ts', 'kev_provider.py', 'policy_prefetch_service.py'))}),
        'budget_sha256': digest(budgets),
        'locks_sha256': digest({k: v for k, v in hashes.items() if k.endswith(('requirements.lock', 'package-lock.json'))}),
        'build_revision': None,
    }


class InvalidPlan(Exception):
    """Carries only a safe code, never configuration or provider text."""


class RunStopped(Exception):
    """Shared terminal stop across source checks and application children."""


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        raise InvalidPlan('invalid_arguments')


def read_plan(path):
    if path is None:
        raise InvalidPlan('missing_manifest')
    if path.resolve().name == '.env' or path.resolve().name.startswith('.env.'):
        raise InvalidPlan('manifest_is_configuration')
    try:
        plan = json.loads(path.read_text())
    except (OSError, UnicodeError, ValueError):
        raise InvalidPlan('unreadable_manifest') from None
    if not isinstance(plan, dict):
        raise InvalidPlan('invalid_manifest')
    seconds = plan.get('total_time_seconds')
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0:
        raise InvalidPlan('invalid_total_time_seconds')
    if type(plan.get('repeats')) is not int or plan['repeats'] <= 0:
        raise InvalidPlan('invalid_repeats')
    if plan.get('order') not in (['baseline', 'candidate'], ['candidate', 'baseline']):
        raise InvalidPlan('invalid_order')
    cases = plan.get('cases')
    if (not isinstance(cases, list) or not cases
            or any(not isinstance(case, str) or case not in CASES for case in cases)
            or len(set(cases)) != len(cases)):
        raise InvalidPlan('invalid_cases')
    sources = plan.get('sources')
    if (not isinstance(sources, dict) or set(sources) != {'baseline', 'candidate'}
            or any(not isinstance(side, dict) for side in sources.values())):
        raise InvalidPlan('missing_provenance')
    return plan


def validate_shape(plan):
    if set(plan) != {'total_time_seconds', 'cases', 'repeats', 'order', 'models', 'sources'}:
        raise InvalidPlan('unsupported_manifest_fields')
    models = plan['models']
    if (not isinstance(models, dict) or set(models) != {'main', 'memory_extraction', 'memory_dream'}
            or any(not isinstance(model, str) or not model.strip() for model in models.values())):
        raise InvalidPlan('invalid_models')
    for source in plan['sources'].values():
        if (source.get('build_revision') is None
                or source.get('build_revision') != source.get('revision')
                or source.get('build_source_sha256') != source.get('runtime_source_sha256')
                or source.get('build_dist_sha256') != source.get('dist_sha256')):
            raise InvalidPlan('build_provenance_mismatch')
        if not isinstance(source.get('directory'), str):
            raise InvalidPlan('missing_provenance')
        expected = {'directory','revision','tree','source_sha256','runtime_source_sha256',
                    'dist_sha256','facts_sha256','prompts_sha256','budget_sha256','locks_sha256',
                    'build_revision','build_source_sha256','build_dist_sha256'}
        if set(source) != expected:
            raise InvalidPlan('unsupported_provenance_fields')
        for key in expected - {'directory'}:
            length = 40 if key in ('revision','tree','build_revision') else 64
            if not isinstance(source[key], str) or not re.fullmatch('[0-9a-f]{' + str(length) + '}', source[key]):
                raise InvalidPlan('missing_provenance')
    if plan['sources']['baseline']['directory'] == plan['sources']['candidate']['directory']:
        raise InvalidPlan('source_directories_must_differ')


def validate_provenance(plan, limit=None):
    for source in plan['sources'].values():
        if limit:
            limit()
        actual = describe(Path(source['directory']), limit)
        if any(source.get(key) != value for key, value in actual.items() if key != 'build_revision'):
            raise InvalidPlan('source_provenance_mismatch')
        for name in ('pi_product_runtime.py', 'result_expression_runtime.py'):
            if limit:
                limit()
            path = Path(source['directory']) / 'backend/app/services' / name
            if path.is_file() and any(token in path.read_text() for token in
                                       ('start_new_session', 'process_group', 'setsid(', 'setpgid(')):
                raise InvalidPlan('unsupported_process_topology')
    baseline, candidate = (plan['sources'][side] for side in ('baseline', 'candidate'))
    for field, code in [('facts_sha256', 'static_facts_mismatch'),
                        ('budget_sha256', 'numeric_budget_mismatch'),
                        ('locks_sha256', 'dependency_locks_mismatch')]:
        if baseline[field] != candidate[field]:
            raise InvalidPlan(code)


# There is deliberately no worker CLI flag. Only the validated supervisor
# launches this bounded program, with the same absolute deadline on every job.
# Product stdout/stderr go to /dev/null before its imports; this dedicated
# descriptor carries only the projections below, never raw response bodies.
WORKER = r'''
import hashlib, hmac, json, logging, math, os, re, sys, time
from pathlib import Path
from uuid import uuid4
wire = os.fdopen(os.dup(1), 'w', buffering=1)
with open(os.devnull, 'w') as sink:
    os.dup2(sink.fileno(), 1)
    os.dup2(sink.fileno(), 2)
logging.disable(logging.CRITICAL)
job = json.loads(sys.stdin.read())
def emit(kind, **values):
    wire.write(json.dumps(dict(type=kind, **values)) + '\n')
    wire.flush()
class Failed(Exception): pass
def check():
    if not math.isfinite(job['deadline']) or time.monotonic() >= job['deadline']:
        raise Failed('deadline')
def stage(name):
    check()
    emit('stage', call_stage=name)
def number(value):
    return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else 'unknown'
def count(value):
    return value if type(value) is int and value >= 0 else 'unknown'
def judgment(value):
    if not isinstance(value, dict): return 'unknown'
    outcome = value.get('outcome')
    return dict(outcome=outcome if outcome in ('yes','no','uncertain','timeout','error','not_attempted') else 'unknown',
                elapsed_ms=number(value.get('elapsed_ms')))
def summary(value):
    if not isinstance(value, dict): return 'unknown'
    result = {key: count(value.get(key)) for key in
              ('policy_lookups','policy_tool_lookups','policy_reuses','tool_starts','primary_pi_turns')}
    outcomes = value.get('policy_lookup_outcomes')
    result['policy_lookup_outcomes'] = {key: count(outcomes.get(key)) for key in ('success','empty','error')} if isinstance(outcomes, dict) else 'unknown'
    result['policy_judgment'] = judgment(value.get('policy_judgment'))
    result['events_truncated'] = value['events_truncated'] if type(value.get('events_truncated')) is bool else 'unknown'
    return result
def error_code(value):
    return value if isinstance(value, str) and re.fullmatch(r'(PI|KEV|POLICY|NAVIGATION|STALE|GUIDE|CATALOG|RUN|TURN)_[A-Z0-9_]{1,70}', value) else 'http_error'
try:
    check()
    source = Path(job['source'])
    sys.path.insert(0, str(source / 'backend'))
    os.chdir(source / 'backend')
    os.environ['DATABASE_URL'] = 'sqlite:///' + job['database']
    os.environ['MERCURY_CHECKPOINT_PATH'] = job['checkpoint']
    stage('configuration')
    from app.core.config import get_settings
    settings = get_settings()
    if (Path(settings.root_dir).resolve() != source
        or settings.database_url != os.environ['DATABASE_URL']
        or Path(settings.mercury_checkpoint_path).resolve() != Path(job['checkpoint'])):
        raise Failed('isolation_configuration_mismatch')
    models = dict(main=settings.llm_model, memory_extraction=settings.memory_extraction_model,
                  memory_dream=settings.memory_dream_model)
    if models != job['models']: raise Failed('model_configuration_mismatch')
    if settings.llm_mode != 'live' or not all((settings.openai_api_key, settings.openai_base_url, settings.kev_base_url)):
        raise Failed('provider_configuration_incomplete')
    config = json.dumps([models, settings.openai_base_url, settings.kev_base_url], sort_keys=True)
    fingerprint = hmac.new(job['nonce'].encode(), config.encode(), hashlib.sha256).hexdigest()
    if job['configuration'] is not None and fingerprint != job['configuration']:
        raise Failed('configuration_changed')
    check()
    if job['preflight']:
        emit('done', status='configured', configuration=fingerprint)
    else:
        stage('seed')
        from app.core.database import init_db, SessionLocal
        from app.services.seed_service import seed_catalog
        init_db()
        with SessionLocal.begin() as db:
            seed_catalog(db)
        stage('startup')
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as client:
            def request(method, path, **kwargs):
                check()
                response = client.request(method, path, **kwargs)
                check()
                if response.status_code >= 400:
                    emit('http_error', http_status=response.status_code)
                    raise Failed('public_api_error')
                return response.json()
            stage('bootstrap')
            bootstrap = request('GET', '/api/v1/bootstrap')
            state = request('POST', '/api/v1/guide/sessions', json={'entry_context': {
                'page':'home', 'store_id':bootstrap['store_id'],
                'delivery_zone_id':bootstrap['delivery_zone_id']}})
            session = state['session_id']
            base = '/api/v1/guide/sessions/' + session
            navigation = '/api/v1/navigation/sessions/' + session
            emit('isolation', database=job['database'],
                 owner=hashlib.sha256(bootstrap['owner_id'].encode()).hexdigest(),
                 session=hashlib.sha256(session.encode()).hexdigest())
            opening = request('POST', navigation + '/opening', json={'role':'keke'})
            request_id = 'compare-' + uuid4().hex
            stage('role_route')
            request_started = time.monotonic()
            route = request('POST', navigation + '/routes', json={
                'request_id':request_id, 'opening_id':opening['opening_id'],
                'role':'keke', 'message':job['message']})
            emit('route', route_status=route['status'] if route.get('status') in
                 ('ready','switch','clarify','unavailable','navigation') else 'unknown',
                 entry_judgment=judgment(route.get('entry_judgment')),
                 elapsed_seconds=time.monotonic()-request_started)
            if route.get('status') != 'ready' or route.get('target_role') != 'keke':
                emit('done', status='blocked', code='route_requires_human_or_is_unavailable',
                     request_elapsed_seconds=time.monotonic()-request_started)
            else:
                state = request('GET', base)
                stage('guide')
                run = request('POST', base + '/runs', json={
                    'request_id':request_id, 'message':job['message'],
                    'expected_task_id':state['task_id'],
                    'expected_state_version':state['state_version'],
                    'expected_session_version':state['session_version'],
                    'routing_request_id':route['routing_request_id']})
                sequence = 0
                while True:
                    data = request('GET', base + '/runs/' + run['run_id'] + '/events',
                                   params={'after_sequence':sequence})
                    terminal = False
                    for event in data['events']:
                        sequence = event['sequence']
                        if event['type'] not in ('turn.completed','turn.stopped','error'):
                            continue
                        payload = event['payload']
                        runtime_status = payload.get('runtime_status')
                        status = ('completed' if event['type'] == 'turn.completed' and runtime_status == 'completed'
                                  else 'blocked' if runtime_status == 'waiting' else 'failed')
                        emit('done', status=status,
                             code=error_code(payload.get('code')) if event['type'] == 'error' else 'unknown',
                             runtime_status=runtime_status if runtime_status in
                             ('completed','waiting','deadline','stopped','tool_budget') else 'unknown',
                             tool_rounds=count(payload.get('tool_rounds')),
                             runtime_summary=summary(payload.get('runtime_summary')),
                             request_elapsed_seconds=time.monotonic()-request_started)
                        terminal = True
                        break
                    if terminal: break
                    check()
                    time.sleep(min(.03, max(0, job['deadline']-time.monotonic())))
except Failed as error:
    emit('done', status='deadline' if str(error) == 'deadline' else 'blocked', code=str(error))
except Exception:
    emit('done', status='failed', code='worker_failed')
'''


def execute(plan, output, started):
    if os.name != 'posix':
        raise InvalidPlan('posix_process_groups_required')
    try:
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise InvalidPlan('output_exists') from None
    deadline = started + plan['total_time_seconds']
    stop = None
    attempted = completed = 0
    total = len(plan['cases']) * plan['repeats'] * 2
    nonce = secrets.token_hex(32)
    previous_handlers = {}

    def cancelled(_signum, _frame):
        nonlocal stop
        stop = stop or 'cancelled'

    def stopped():
        nonlocal stop
        if stop is None and time.monotonic() >= deadline:
            stop = 'deadline'
        return stop is not None

    def remaining():
        if stopped():
            raise RunStopped(stop)
        return max(0, deadline-time.monotonic())

    environment_names = (
        'PATH','HOME','SYSTEMROOT','HTTP_PROXY','HTTPS_PROXY','NO_PROXY',
        'http_proxy','https_proxy','no_proxy','NODE_EXTRA_CA_CERTS',
        'OPENAI_API_KEY','OPENAI_BASE_URL','LLM_MODEL','LLM_MODE','KEV_BASE_URL',
        'MEMORY_EXTRACTION_MODEL','MEMORY_DREAM_MODEL','BUSINESS_DATA_MODE',
        # Preserve the Tester's repaired hooks in controlled execution.
        'PYTHONPATH','NODE_OPTIONS','CERES_NODE_GUARD_AUDIT',
    )
    configuration_names = {
        'OPENAI_API_KEY','OPENAI_BASE_URL','LLM_MODEL','LLM_MODE','KEV_BASE_URL',
        'MEMORY_EXTRACTION_MODEL','MEMORY_DREAM_MODEL','BUSINESS_DATA_MODE',
    }
    # Settings folds these aliases case-insensitively. Keep original spelling
    # and iteration order so duplicate-case keys retain its normal precedence;
    # do not broaden forwarding to unrelated environment variables.
    environment = {key: value for key, value in os.environ.items()
                   if key in environment_names or key.upper() in configuration_names}
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    with os.fdopen(descriptor, 'w') as journal:
        def record(kind, **values):
            journal.write(json.dumps(dict(type=kind, elapsed_seconds=round(time.monotonic()-started, 6),
                                          **values), ensure_ascii=False) + '\n')
            journal.flush()

        def child(side, *, case=None, repetition=None, configuration=None):
            if stopped():
                return {'status':stop}
            source = Path(plan['sources'][side]['directory'])
            python = source / 'backend/.venv/bin/python'
            if not python.is_file():
                return {'status':'blocked', 'code':'source_python_missing'}
            with tempfile.TemporaryDirectory(prefix='ceres-compare-') as temporary:
                job = dict(source=str(source), database=str(Path(temporary)/'runtime.sqlite3'),
                           checkpoint=str(Path(temporary)/'checkpoints.sqlite3'),
                           deadline=deadline, nonce=nonce, models=plan['models'],
                           configuration=configuration, preflight=case is None,
                           message=CASES[case] if case else None)
                if stopped():
                    return {'status':stop}
                try:
                    process = subprocess.Popen([str(python), '-c', WORKER], cwd=source,
                                               env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                               stderr=subprocess.DEVNULL, start_new_session=True)
                except OSError:
                    return {'status':'blocked', 'code':'source_python_unavailable'}
                selector = selectors.DefaultSelector()
                selector.register(process.stdout, selectors.EVENT_READ)
                result = {'status':'failed', 'code':'worker_protocol_ended'}
                pending = b''
                try:
                    if stopped():
                        return {'status':stop}
                    process.stdin.write(json.dumps(job).encode())
                    process.stdin.close()
                    while not stopped():
                        ready = selector.select(timeout=min(.05, max(0, deadline-time.monotonic())))
                        if not ready:
                            continue
                        chunk = os.read(process.stdout.fileno(), 65536)
                        if not chunk:
                            break
                        pending += chunk
                        if len(pending) > 65536:
                            result = {'status':'failed', 'code':'worker_protocol_invalid'}
                            break
                        finished = False
                        while b'\n' in pending:
                            raw, pending = pending.split(b'\n', 1)
                            row = json.loads(raw)
                            if not isinstance(row, dict) or row.get('type') not in (
                                    'done', 'stage', 'isolation', 'http_error', 'route'):
                                raise ValueError('unsupported worker frame')
                            kind = row.pop('type')
                            if kind == 'done':
                                result = row
                                finished = True
                                break
                            # The worker produces only safe projections. Its
                            # stage duration has a separate name from run time.
                            if 'elapsed_seconds' in row:
                                row['stage_elapsed_seconds'] = row.pop('elapsed_seconds')
                            record(kind, side=side, case=case, repetition=repetition, **row)
                        if finished:
                            break
                    if stopped():
                        result = {'status':stop}
                except (OSError, ValueError, TypeError, KeyError):
                    result = {'status':'failed', 'code':'worker_protocol_invalid'}
                finally:
                    selector.close()
                    # Do not reap the leader before killing its owned group.
                    # Both reviewed Pi launchers inherit this group; no global
                    # process lookup, pkill, existing service or shared PID.
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
                    process.stdout.close()
                    if not process.stdin.closed:
                        process.stdin.close()
                return result

        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.signal(signum, cancelled)
        try:
            record('plan', planned_samples=total, cases=plan['cases'], repeats=plan['repeats'],
                   order=plan['order'], total_time_seconds=plan['total_time_seconds'],
                   comparison_kind=('same_source_smoke' if
                       plan['sources']['baseline']['source_sha256'] == plan['sources']['candidate']['source_sha256']
                       else 'bundled_old_new'),
                   source_provenance=plan['sources'], model_declarations_sha256=digest(plan['models']),
                   prompts_changed=plan['sources']['baseline']['prompts_sha256'] != plan['sources']['candidate']['prompts_sha256'],
                   thinking_transport='not_wire_verified', payload_settings_alignment='not_verified',
                   build_provenance='human_attested_pending_source_check')
            configured = {}
            try:
                validate_provenance(plan, remaining)
            except RunStopped as error:
                stop = stop or str(error)
            except InvalidPlan as error:
                stop = stop or 'blocked'
                record('blocked', code=str(error))
            else:
                record('source_check', status='matched', build_provenance='human_attested_hashes_matched')
            for side in plan['order']:
                if stopped():
                    break
                result = child(side)
                if result['status'] != 'configured':
                    stop = stop or result['status']
                    record('blocked', side=side, code=result.get('code', 'unknown'))
                    break
                configured[side] = result['configuration']
            if stop is None and len(set(configured.values())) != 1:
                stop = 'blocked'
                record('blocked', code='provider_configuration_mismatch')
            samples = ((case, repetition, side) for repetition in range(1, plan['repeats']+1)
                       for case in plan['cases'] for side in plan['order'])
            for case, repetition, side in samples:
                if stopped():
                    break
                try:
                    validate_provenance(plan, remaining)
                except RunStopped as error:
                    stop = stop or str(error)
                    break
                except InvalidPlan as error:
                    stop = stop or 'blocked'
                    record('blocked', code=str(error))
                    break
                if stopped():
                    break
                attempted += 1
                result = child(side, case=case, repetition=repetition, configuration=configured[side])
                record('sample', side=side, case=case, repetition=repetition,
                       quality='unknown', provider_http_requests='unknown', usage='unknown', cost='unknown',
                       render_timings='unknown', **result)
                completed += result['status'] == 'completed'
                if result.get('code') in ('configuration_changed', 'model_configuration_mismatch',
                                          'isolation_configuration_mismatch'):
                    stop = stop or 'blocked'
                if result['status'] in ('deadline','cancelled'):
                    stop = stop or result['status']
            if stop is None:
                try:
                    validate_provenance(plan, remaining)
                except RunStopped as error:
                    stop = stop or str(error)
                except InvalidPlan as error:
                    stop = stop or 'blocked'
                    record('blocked', code=str(error))
            status = stop or ('completed' if completed == total else 'completed_with_failures')
            result = dict(type='summary', status=status, attempted_samples=attempted,
                          completed_samples=completed, unstarted_samples=total-attempted,
                          provider_http_requests='unknown', usage='unknown', cost='unknown',
                          quality='unknown')
            record('summary', **{key:value for key,value in result.items() if key != 'type'})
            print(json.dumps(result))
            return {'completed':0, 'cancelled':130, 'deadline':124, 'blocked':2}.get(status, 1)
        finally:
            for signum, handler in previous_handlers.items():
                signal.signal(signum, handler)


def main():
    started = time.monotonic()
    parser = Parser(description=__doc__)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--describe', type=Path)
    try:
        args = parser.parse_args()
        if args.describe is not None:
            if args.manifest is not None or args.execute or args.output is not None:
                raise InvalidPlan('invalid_arguments')
            print(json.dumps({'status': 'source_description', 'source': describe(args.describe)}))
            return 0
        if args.output is not None and not args.execute:
            raise InvalidPlan('invalid_arguments')
        plan = None
        if args.manifest is not None or args.execute:
            plan = read_plan(args.manifest)
            validate_shape(plan)
        if args.execute:
            if args.output is None:
                raise InvalidPlan('missing_output')
            if args.output.exists() or args.output.is_symlink():
                raise InvalidPlan('output_exists')
            return execute(plan, args.output, started)
        if plan is not None:
            validate_provenance(plan)
    except InvalidPlan as exc:
        print(json.dumps({'status': 'invalid_plan', 'code': str(exc)}))
        return 2
    print(json.dumps({
        'status': 'preview',
        'execution_enabled': False,
        'configuration_loaded': False,
        'provider_requests': 'not_attempted',
        'synthetic_cases': CASES,
        'manifest_valid': plan is not None,
        'planned_samples': len(plan['cases']) * plan['repeats'] * 2 if plan else None,
    }))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

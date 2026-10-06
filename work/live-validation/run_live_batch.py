#!/usr/bin/env python3
"""USER-RUN ONLY. Importing this module is inert; main starts real model work.

See USER-RUN.md before launching. No provider/config imports at module scope.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
from uuid import uuid4

MODEL = 'qwen3.8-27b'
PROVIDER = 'https://discovery-api.intern-ai.org.cn/v1'
BATCH_SECONDS = 240
MEMORY_SECONDS = 35
TERMINAL = {'completed', 'waiting_clarification', 'waiting_confirmation', 'protected', 'stopped', 'failed', 'interrupted'}
# Positive field allowlist: unknown fields are counted, never serialized by name/value.
FIELDS = set('''stage status reason code error error_code diagnostic_id http_status result results
request response method path elapsed_seconds first_event_seconds utc type event events payload
upstream_http_status transport_phase transport_error_class transport_error_code
protocol_version sequence run_id request_id session_id task_id target_task_id owner_id store_id
delivery_zone_id session_version state_version expected_session_version expected_state_version
expected_task_id message messages content role kind text final_text answer_status answer_kind
runtime runtime_status runtime_events model_mode business_data_mode tool_rounds product_evidence
product_cards products ref sku_id name name_zh brand spec_quantity spec_unit price_fen unit_price_fen
quantity remaining_quantity added_quantity selected items items_added available_qty available_to_add
sellable offer_version image_path total_price_fen selected_total_fen line_total_fen total_fen
plan plan_id plan_version mode can_confirm plan_kind validation_status expires_at budget_quote
current_step task_status available_actions pending_clarifications slot question confirmation_result
confirmation_id operation_id committed plan_effect assistant_message_id trace_id status_before
status_after cart_version version order order_id order_version receipt_id preview_id confirmed
proposal proposal_id receipts application_id revision selection_version responsibility responsibility_generation
amount_fen item_id policy policy_id simulated action_results created_at updated_at completed_at
source source_id source_quote origin_role category domain key memory_id deleted_at records jobs job_id
count counts rows lease_until eligibility eligible fingerprint model_calls toolName tool_name phase
round stopReason packaging pack_count item_volume_ml total_volume_ml price_per_litre_yuan
has_active_task task_state conditions goal budget_fen query category_id errors retryable cancelled
root cause diagnostic model configured credential_present extraction_model dream_model endpoint
run_directory database_path checkpoint_path source_revision source_inventory inventory_sha256
sha256 dirty file_count coverage checks actual expected passed exit_code failure_class
summary transport provider_boundary_evidence started_at finished_at duration_seconds limits
pi_turns mercury_turns memory_observation_seconds batch_seconds note browser operator dream
extraction purchase_refund_replay redaction_count omitted_fields_count before after api_calls source_text role_count
catalog_products offers stores owners carts simulated_orders aftersales_applications aftersales_receipts
shopping_memories memory_jobs schema_versions evidence_schema scenarios model_ids
historical_repurchase supply_revision memory_correction_deletion_restart stale_consent browser_recovery independent_second_run
'''.split())
SENSITIVE = re.compile(r'authorization|cookie|token|api.?key|password|secret|credential', re.I)


def sanitize(value, secrets=()):
    """Allowlisted payload fields, exact secret removal, no arbitrary objects/repr."""
    if isinstance(value, dict):
        result = {}
        omitted = 0
        for key, item in value.items():
            if isinstance(key, str) and key in FIELDS and (not SENSITIVE.search(key) or key == 'credential_present'):
                result[key] = sanitize(item, secrets)
            else:
                omitted += 1
        if omitted:
            result['omitted_fields_count'] = omitted
        return result
    if isinstance(value, (tuple, list)):
        return [sanitize(item, secrets) for item in value]
    if isinstance(value, str):
        for secret in sorted((s for s in secrets if s), key=len, reverse=True):
            value = value.replace(secret, '[REDACTED]')
            value = value.replace(json.dumps(secret)[1:-1], '[REDACTED]')
        value = re.sub(r'(?i)bearer\s+[^\s"\'<>]+', 'Bearer [REDACTED]', value)
        value = re.sub(r'(?i)(?:sk-|key-)[A-Za-z0-9_-]{12,}', '[REDACTED]', value)
        # Never preserve embedded credential assignments, even in model prose.
        value = re.sub(r'(?i)(authorization|api[_ -]?key|password|access[_ -]?token|cookie)\s*[:=]\s*[^\s,;]+', r'\1=[REDACTED]', value)
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return '[OMITTED_NON_JSON]'


def utc():
    return datetime.now(timezone.utc).isoformat()


def create_run(root):
    base = Path(root) / 'work/live-validation/tmp'
    base.mkdir(parents=True, exist_ok=True)
    run = base / ('live-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:12])
    run.mkdir(mode=0o700)
    (run / 'private-state').mkdir(mode=0o700)
    (run / 'evidence').mkdir(mode=0o700)
    return run


def inventory(root):
    """Only known source/build/static-data extensions, never .env or runtime data."""
    root = Path(root)
    rows = []
    for folder in ('backend/app', 'runtime/pi/src', 'runtime/pi/dist', 'data/fixtures', 'frontend/src', 'work/live-validation'):
        for file in sorted((root / folder).rglob('*')):
            rel = file.relative_to(root)
            if any(part in ('tmp', '__pycache__', 'node_modules', '.git') for part in rel.parts):
                continue
            if file.is_symlink() or not file.is_file() or file.suffix not in ('.py', '.ts', '.tsx', '.js', '.json', '.md', '.css') or file.name.startswith('.env'):
                continue
            rows.append({'path': str(rel), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    for name in ('backend/requirements.lock', 'backend/pyproject.toml', 'runtime/pi/package-lock.json', 'runtime/pi/package.json', 'frontend/package-lock.json'):
        file = root / name
        if file.is_file() and not file.is_symlink():
            rows.append({'path': name, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    try:
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        dirty = subprocess.run(['git','diff','--quiet','HEAD','--','backend/app','runtime/pi/src','frontend/src','data/fixtures','work/live-validation'], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5).returncode != 0
    except (OSError, subprocess.SubprocessError):
        revision = 'unavailable'
        dirty = None
    return {'source_revision': revision, 'dirty':dirty, 'source_inventory': rows, 'inventory_sha256': hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(), 'file_count': len(rows)}


class BatchFailure(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class Evidence:
    def __init__(self, directory, secrets=()):
        self.directory = Path(directory)
        self.secrets = secrets
        self.started = time.monotonic()
        self.stage = 'startup'
        self.checks = []

    def write(self, name, value):
        path = self.directory / name
        data = json.dumps(sanitize(value, self.secrets), ensure_ascii=False, indent=2, allow_nan=False)
        path.write_text(data + '\n', encoding='utf-8')

    def event(self, **data):
        row = sanitize({'stage': self.stage, 'utc': utc(), 'elapsed_seconds': round(time.monotonic() - self.started, 4), **data}, self.secrets)
        with (self.directory / 'events.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
            stream.flush()

    def check(self, code, condition, actual=None, expected=None):
        row = {'code': code, 'passed': bool(condition), 'actual': actual, 'expected': expected}
        self.checks.append(row)
        self.event(**row)
        if not condition:
            raise BatchFailure(code)


class Journey:
    """All mutations use the released owner-scoped HTTP APIs."""
    def __init__(self, client, evidence, database_path=None):
        self.client, self.e = client, evidence
        self.database_path = database_path
        self.pi_turns = 0
        self.calls = 0

    def call(self, method, path, body=None, headers=None):
        self.calls += 1
        self.e.event(method=method, path=path, request=body)
        start = time.monotonic()
        response = self.client.request(method, path, json=body, headers=headers)
        try:
            result = response.json()
        except ValueError:
            self.e.event(http_status=response.status_code, code='NON_JSON_RESPONSE')
            raise BatchFailure('NON_JSON_RESPONSE') from None
        self.e.event(http_status=response.status_code, duration_seconds=time.monotonic()-start, response=result)
        if response.status_code >= 400:
            raise BatchFailure('HTTP_' + str(response.status_code))
        return result

    def turn(self, sid, prompt, *, stop=False):
        self.pi_turns += 1
        if self.pi_turns > 5:
            raise BatchFailure('PI_TURN_LIMIT')
        state = self.call('GET', f'/api/v1/guide/sessions/{sid}')
        body = {'request_id': 'live-' + uuid4().hex, 'message': prompt,
                'expected_task_id': state['task_id'], 'expected_state_version': state['state_version'],
                'expected_session_version': state['session_version'],
                'displayed_candidate_refs': [row['ref'] for row in state['product_cards']]}
        if state['plan']:
            body['displayed_plan'] = {key: state[key] for key in ('task_id', 'state_version', 'session_version')}
            body['displayed_plan'].update({key: state['plan'][key] for key in ('plan_id', 'plan_version')})
        started = time.monotonic()
        admitted = self.call('POST', f'/api/v1/guide/sessions/{sid}/runs', body)
        if stop:
            self.call('POST', f'/api/v1/guide/sessions/{sid}/turns/stop', {'request_id': body['request_id']})
        sequence = 0
        while time.monotonic() - started < 25:
            result = self.call('GET', f'/api/v1/guide/sessions/{sid}/runs/{admitted["run_id"]}/events?after_sequence={sequence}')
            if result['events']:
                if sequence == 0:
                    self.e.event(first_event_seconds=time.monotonic()-started)
                sequence = result['events'][-1]['sequence']
            if result['status'] in TERMINAL:
                receipt = self.call('GET', f'/api/v1/guide/sessions/{sid}/turns/{body["request_id"]}')
                # Additional journal read only, not disconnect/recovery coverage.
                self.call('GET', f'/api/v1/guide/sessions/{sid}/runs/{admitted["run_id"]}/events?after_sequence={sequence}')
                self.e.event(status=receipt['status'], duration_seconds=time.monotonic()-started)
                return receipt
            time.sleep(0.2)
        raise BatchFailure('PI_POLL_TIMEOUT')

    def presales(self):
        self.e.stage = 'bootstrap'
        health = self.call('GET', '/health')
        self.e.check('LIVE_HEALTH', health['llm_configured'] and health['business_data_mode'] == 'demo')
        boot = self.call('GET', '/api/v1/bootstrap')
        state = self.call('POST', '/api/v1/guide/sessions', {'entry_context': {'page':'home', 'store_id':boot['store_id'], 'delivery_zone_id':boot['delivery_zone_id']}})
        sid = state['session_id']
        cart0 = self.call('GET', '/api/v1/cart')
        self.e.check('FRESH_CART_EMPTY', not cart0['items'])
        self.e.stage = 'pi_comparison'
        receipt = self.turn(sid, '帮我比较几种当前可买的饮料，说明规格和价格差异。只比较，不要准备清单或加购。')
        self.e.check('COMPARISON_NATURAL_COMPLETION', receipt['status'] == 'completed', receipt['status'], 'completed')
        state = self.call('GET', f'/api/v1/guide/sessions/{sid}')
        self.e.check('REAL_COMPARISON_CANDIDATES', len(state['product_cards']) >= 2, len(state['product_cards']), '>=2')
        self.e.check('COMPARISON_CART_UNCHANGED', self.call('GET', '/api/v1/cart') == cart0)
        candidate = state['product_cards'][0]
        self.e.stage = 'pi_selected_plan'
        receipt = self.turn(sid, f'我选刚展示的第一款“{candidate["name"]}”，买1件，预算100元。请准备采购清单，但不要加购。')
        self.e.check('PLAN_MODEL_COMPLETION', receipt['status'] in ('completed','waiting_confirmation'), receipt['status'])
        state = self.call('GET', f'/api/v1/guide/sessions/{sid}')
        plan = state['plan']
        self.e.check('SELECTED_PLAN_PRESENT', bool(plan))
        self.e.check('PLAN_CART_UNCHANGED', self.call('GET', '/api/v1/cart') == cart0)
        if plan.get('budget_quote'):
            self.e.check('QUOTE_SCOPE_LIMIT', plan['selected_total_fen'] <= 10000, plan['selected_total_fen'], '<=10000')
            self.e.stage = 'explicit_quote_acceptance'
            self.call('POST', f'/api/v1/guide/tasks/{state["task_id"]}/plan-revisions', {
                'request_id':'quote-' + uuid4().hex, 'base_plan_id':plan['plan_id'], 'base_plan_version':plan['plan_version'],
                'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'], 'coverage_intent':'accept_quote', 'items':[]})
            self.e.check('QUOTE_CART_UNCHANGED', self.call('GET','/api/v1/cart') == cart0)
            state = self.call('GET', f'/api/v1/guide/sessions/{sid}')
            plan = state['plan']
        selected = [{'sku_id': row['sku_id'], 'quantity': row['remaining_quantity']} for row in plan['items'] if row['selected'] and row['remaining_quantity'] > 0]
        self.e.check('EXACT_SELECTION', selected == [{'sku_id':candidate['sku_id'], 'quantity':1}], selected, [{'sku_id':candidate['sku_id'], 'quantity':1}])
        self.e.check('PLAN_CONFIRMABLE', plan['can_confirm'])
        self.e.check('QUOTE_SCOPE_LIMIT', plan['selected_total_fen'] <= 10000, plan['selected_total_fen'], '<=10000')
        self.e.stage = 'explicit_cart_confirmation_replay'
        body = {'plan_id':plan['plan_id'], 'plan_version':plan['plan_version'], 'expected_state_version':state['state_version'], 'expected_session_version':state['session_version'], 'selected_items':selected}
        headers = {'Idempotency-Key':'cart-' + uuid4().hex}
        path = f'/api/v1/guide/tasks/{state["task_id"]}/confirm'
        first = self.call('POST', path, body, headers)
        cart1 = self.call('GET', '/api/v1/cart')
        replay = self.call('POST', path, body, headers)
        self.e.check('CART_RECEIPT_REPLAY', replay == first)
        self.e.check('CART_SINGLE_EFFECT', self.call('GET', '/api/v1/cart') == cart1 and [{'sku_id':r['sku_id'], 'quantity':r['quantity']} for r in cart1['items']] == selected)
        self.e.stage = 'simulated_checkout_replay'
        preview = self.call('POST', '/api/v1/checkout/preview', {'expected_cart_version':cart1['version']})
        expected_items = [{'sku_id':r['sku_id'], 'quantity':r['quantity'], 'unit_price_fen':r['unit_price_fen']} for r in cart1['items']]
        self.e.check('CHECKOUT_PREVIEW_MATCHES_CONSENT', [{'sku_id':r['sku_id'], 'quantity':r['quantity'], 'unit_price_fen':r['unit_price_fen']} for r in preview['items']] == expected_items and preview['total_fen'] == cart1['total_price_fen'])
        body = {'preview_id':preview['preview_id'], 'idempotency_key':'checkout-' + uuid4().hex, 'confirmed':True}
        first = self.call('POST', '/api/v1/checkout/confirm', body)
        replay = self.call('POST', '/api/v1/checkout/confirm', body)
        self.e.check('CHECKOUT_RECEIPT_REPLAY', first == replay)
        self.e.check('CHECKOUT_ORDER_MATCHES_PREVIEW', [{'sku_id':r['sku_id'], 'quantity':r['quantity'], 'unit_price_fen':r['unit_price_fen']} for r in first['order']['items']] == expected_items and first['order']['total_fen'] == preview['total_fen'])
        self.e.check('CHECKOUT_CART_DEDUCTED', self.call('GET', '/api/v1/cart')['items'] == [])
        self.e.check('ONE_SIMULATED_ORDER', len(self.call('GET', '/api/v1/orders')['items']) == 1)
        return sid, first['order']['order_id']

    def mercury(self, order_id):
        self.e.stage = 'mercury_refund_model_proposal'
        order = self.call('GET', f'/api/v1/orders/{order_id}')
        case = self.call('POST', '/api/v1/mercury/sessions')
        sid = case['session_id']
        self.call('PUT', f'/api/v1/mercury/sessions/{sid}/order', {'order_id':order_id, 'selection_version':case['selection_version']})
        body = {'message':'这笔未发货订单我不需要了，想整单退款。原因是买错了，请先生成具体方案，不要提交申请。', 'request_id':'refund-' + uuid4().hex}
        self.e.event(request=body)
        started = time.monotonic()
        response = self.client.post(f'/api/v1/mercury/sessions/{sid}/turns/stream', json=body)
        self.e.event(http_status=response.status_code, duration_seconds=time.monotonic()-started)
        if response.status_code != 200:
            raise BatchFailure('MERCURY_HTTP_' + str(response.status_code))
        # Actual SSE bodies only. Never persist arbitrary response headers or raw text.
        event_name = None
        complete = None
        for line in response.text.splitlines():
            if line.startswith('event:'):
                event_name = line[6:].strip()
            elif line.startswith('data:'):
                payload = json.loads(line[5:])
                self.e.event(event=event_name, payload=payload)
                if event_name == 'turn.completed':
                    complete = payload
        self.e.check('MERCURY_AWAITING_CONFIRMATION', complete is not None and complete['status'] == 'awaiting_confirmation', complete)
        before = self.call('GET', f'/api/v1/mercury/sessions/{sid}/aftersales')
        self.e.check('NO_APPLICATION_BEFORE_CONSENT', before['receipts'] == [])
        before_counts = snapshot(self.database_path)['counts']
        self.e.event(before={'counts':before_counts})
        self.e.check('NO_DURABLE_APPLICATION_BEFORE_CONSENT', before_counts['aftersales_applications'] == 0 and before_counts['aftersales_receipts'] == 0)
        proposal = before['proposal']
        self.e.check('MODEL_PROPOSAL_PRESENT', bool(proposal))
        self.e.check('REFUND_EXACT_ORDER', proposal['order_id'] == order_id and proposal['kind'] == 'refund' and proposal['simulated'])
        self.e.check('REFUND_MATCHES_ORDER_FACTS', proposal['amount_fen'] == order['total_fen'] and [{'item_id':r['item_id'],'quantity':r['quantity'],'amount_fen':r['amount_fen']} for r in proposal['items']] == [{'item_id':r['sku_id'],'quantity':r['quantity'],'amount_fen':r['line_total_fen']} for r in order['items']])
        self.e.stage = 'explicit_refund_confirmation_replay'
        body = {'proposal_id':proposal['proposal_id'], 'idempotency_key':'refund-confirm-' + uuid4().hex, 'confirmed':True}
        first = self.call('POST', f'/api/v1/mercury/sessions/{sid}/confirm', body)
        replay = self.call('POST', f'/api/v1/mercury/sessions/{sid}/confirm', body)
        after = self.call('GET', f'/api/v1/mercury/sessions/{sid}/aftersales')
        self.e.check('REFUND_REQUESTED_ONLY', first['status'] == 'requested', first['status'], 'requested')
        self.e.check('REFUND_SINGLE_RECEIPT', first == replay and len(after['receipts']) == 1)
        after_counts = snapshot(self.database_path)['counts']
        self.e.event(after={'counts':after_counts})
        self.e.check('REFUND_SINGLE_DURABLE_APPLICATION', after_counts['aftersales_applications'] == 1 and after_counts['aftersales_receipts'] == 1)
        return sid

    def additional(self, sid):
        self.e.stage = 'ordinary_question_preserves_cart'
        before = self.call('GET', '/api/v1/cart')
        receipt = self.turn(sid, '碳酸饮料为什么会冒泡？')
        self.e.check('ORDINARY_QUESTION_COMPLETED', receipt['status'] == 'completed', receipt['status'])
        self.e.check('ORDINARY_CART_UNCHANGED', self.call('GET', '/api/v1/cart') == before)
        self.e.stage = 'automatic_memory_source'
        receipt = self.turn(sid, '测试设定：我长期只选无糖饮料。今天预算30元，请重新比较适合我的饮料，不要加购。')
        self.e.check('MEMORY_SOURCE_COMMITTED', receipt['status'] in ('completed','waiting_confirmation'), receipt['status'])
        self.e.stage = 'stop_current_processing'
        before = self.call('GET', f'/api/v1/guide/sessions/{sid}')
        cart = self.call('GET','/api/v1/cart')
        receipt = self.turn(sid, '请继续详细比较这些饮料。', stop=True)
        self.e.check('STOP_OBSERVED', receipt['status'] == 'stopped', receipt['status'], 'stopped')
        after = self.call('GET', f'/api/v1/guide/sessions/{sid}')
        self.e.check('STOP_PRESERVES_PLAN_CART', after['plan'] == before['plan'] and self.call('GET','/api/v1/cart') == cart)


def snapshot(db_path):
    """Read-only, named tables and columns; no generic SQL/data dump."""
    with sqlite3.connect('file:' + str(db_path) + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        tables = ('catalog_products','offers','stores','owners','carts','simulated_orders','aftersales_applications','aftersales_receipts','shopping_memories','memory_jobs')
        counts = {table:db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0] for table in tables}
        jobs = [dict(row) for row in db.execute('SELECT job_id, kind, source_id, source_json, status, error_code, created_at, completed_at FROM memory_jobs ORDER BY created_at')]
        for row in jobs:
            source = json.loads(row.pop('source_json'))
            row['source_text'] = source.get('text')
            row['role'] = source.get('role')
        memories = [dict(row) for row in db.execute('SELECT memory_id,category,domain,key,content,source,origin_role,source_id,source_quote,revision,created_at,updated_at,expires_at,deleted_at FROM shopping_memories ORDER BY memory_id')]
        return {'counts': counts, 'jobs':jobs, 'records':memories}


def worker(run):
    # This function is reached ONLY by the user's explicit launch.
    run = Path(run).resolve()
    root = Path(__file__).resolve().parents[2]
    e = Evidence(run / 'evidence')
    summary = {'status':'failed', 'transport':'in-process ASGI HTTP/SSE; real app lifecycle, Pi SDK and LangGraph', 'coverage':{'browser':'untested', 'operator':'skipped', 'dream':'skipped_threshold_not_deliberately_generated', 'purchase_refund_replay':'not_reached', 'extraction':'not_reached', 'historical_repurchase':'untested', 'supply_revision':'untested', 'memory_correction_deletion_restart':'untested', 'stale_consent':'untested', 'browser_recovery':'untested', 'independent_second_run':'untested'}, 'provider_boundary_evidence':'Public app outputs only; no full raw provider exchanges or network call count.'}
    try:
        private = run / 'private-state'
        database = private / 'business.sqlite3'
        checkpoint = private / 'mercury-checkpoints.sqlite3'
        e.check('FRESH_DATABASE_PATHS', not database.exists() and not checkpoint.exists())
        # Only isolation overrides; root .env is loaded normally by Settings.
        os.environ['DATABASE_URL'] = 'sqlite:///' + str(database)
        os.environ['MERCURY_CHECKPOINT_PATH'] = str(checkpoint)
        sys.path.insert(0, str(root / 'backend'))
        from app.core.config import get_settings
        settings = get_settings()
        e.secrets = (settings.openai_api_key, settings.human_operator_token)
        models = (settings.llm_model, settings.memory_extraction_model, settings.memory_dream_model)
        e.check('EXACT_MODEL_GATE', all(model == MODEL for model in models))
        e.check('EXACT_PROVIDER_GATE', settings.openai_base_url.rstrip('/') == PROVIDER)
        e.check('LIVE_CONFIG_GATE', settings.llm_mode == 'live' and bool(settings.openai_api_key))
        e.check('DEMO_WRITES_GATE', settings.business_data_mode == 'demo' and not settings.shopping_writes_paused)
        e.check('ISOLATION_GATE', settings.database_url == 'sqlite:///' + str(database) and settings.mercury_checkpoint_path == checkpoint)
        manifest = {**inventory(root), 'started_at':utc(), 'model':MODEL, 'extraction_model':MODEL, 'dream_model':MODEL, 'endpoint':PROVIDER, 'credential_present':True, 'database_path':str(database), 'checkpoint_path':str(checkpoint), 'limits':{'pi_turns':5,'mercury_turns':1,'batch_seconds':BATCH_SECONDS,'memory_observation_seconds':MEMORY_SECONDS}, 'evidence_schema':1}
        e.write('manifest.json', manifest)
        from app.core.database import init_db, SessionLocal, engine
        from app.services.seed_service import seed_catalog
        init_db()
        with SessionLocal.begin() as db:
            seed_catalog(db)
        initial = snapshot(database)
        e.write('initial-state.json', initial)
        e.check('SEED_COUNTS', initial['counts']['catalog_products'] == 65 and initial['counts']['offers'] == 65 and initial['counts']['stores'] == 1)
        e.check('NO_IMPORTED_BUSINESS', all(initial['counts'][key] == 0 for key in ('owners','carts','simulated_orders','aftersales_applications','aftersales_receipts','shopping_memories','memory_jobs')))
        from app.main import app
        from fastapi.testclient import TestClient
        with TestClient(app, raise_server_exceptions=False) as client:
            journey = Journey(client, e, database)
            sid, order_id = journey.presales()
            journey.mercury(order_id)
            summary['coverage']['purchase_refund_replay'] = 'passed'
            journey.additional(sid)
            e.stage = 'memory_observation'
            started = time.monotonic()
            while True:
                state = snapshot(database)
                e.write('memory-state.json', state)
                if not any(row['status'] in ('pending','running') for row in state['jobs']) or time.monotonic()-started >= MEMORY_SECONDS:
                    break
                time.sleep(0.5)
            automatic = [r for r in state['records'] if r['source'] == 'automatic' and r['deleted_at'] is None]
            relevant = [r for r in automatic if '无糖' in r['source_quote']]
            summary['coverage']['extraction'] = 'observed' if relevant else 'blocked_no_matching_automatic_record'
            summary['coverage']['dream'] = 'observed_job_only' if any(j['kind'] == 'dream' for j in state['jobs']) else 'skipped_threshold_not_reached'
            e.check('ONE_OFF_BUDGET_NOT_DURABLE', not any('今天预算30元' in r['content'] or r['key'] == 'budget_fen' for r in automatic))
            summary['api_calls'] = journey.calls
        # Lifespan shutdown stops memory scheduling; snapshot is after normal cleanup.
        e.write('final-state.json', snapshot(database))
        engine.dispose()
        summary['status'] = 'api_batch_passed' if summary['coverage']['extraction'] == 'observed' else 'api_core_passed_memory_blocked'
        return_code = 0 if summary['status'] == 'api_batch_passed' else 2
    except BaseException as error:
        # Never format an exception, traceback, Pydantic error or provider body.
        summary.update(stage=e.stage, code=error.code if isinstance(error, BatchFailure) else 'UNEXPECTED_EXCEPTION', failure_class=type(error).__name__ if type(error).__name__ in {'BatchFailure','TimeoutError','ValueError','KeyError','ImportError','ModuleNotFoundError','KeyboardInterrupt','OSError','RuntimeError'} else 'OtherException')
        return_code = 1
    # Preserve final authoritative state after failed assertions too. This is a
    # named read-only snapshot, never an attempt to repair/restart a failed run.
    if 'database' in locals() and database.exists():
        try:
            e.write('final-state.json', snapshot(database))
        except Exception:
            e.event(code='FINAL_SNAPSHOT_UNAVAILABLE')
    summary.update(checks=e.checks, finished_at=utc(), elapsed_seconds=time.monotonic()-e.started, exit_code=return_code)
    e.write('summary.json', summary)
    return return_code


def terminate_owned_group(child):
    """The child is created with start_new_session=True; never kill other services."""
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        child.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    # Kill remaining descendants even if their immediate parent exited first.
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait(timeout=3)


def run_supervised(root):
    os.umask(0o077)
    run = create_run(root)
    evidence = Evidence(run / 'evidence')
    evidence.write('supervisor.json', {'started_at':utc(), 'status':'running','batch_seconds':BATCH_SECONDS})
    print('Starting REAL-MODEL API integration batch; bounded background memory work included.', flush=True)
    print('Sanitized evidence: ' + str(run / 'evidence'), flush=True)
    child = None
    code = 1
    try:
        # No untrusted app/provider stdout/stderr reaches console or evidence.
        child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker', str(run)], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        code = child.wait(timeout=BATCH_SECONDS)
    except subprocess.TimeoutExpired:
        evidence.write('supervisor.json', {'status':'timed_out','code':'BATCH_DEADLINE','exit_code':124,'finished_at':utc()})
        code = 124
    except KeyboardInterrupt:
        evidence.write('supervisor.json', {'status':'cancelled','exit_code':130,'finished_at':utc()})
        code = 130
    except OSError:
        evidence.write('supervisor.json', {'status':'failed','code':'WORKER_LAUNCH_FAILED','exit_code':1,'finished_at':utc()})
    finally:
        if child is not None:
            terminate_owned_group(child)
    if code not in (124,130):
        evidence.write('supervisor.json', {'status':'exited','exit_code':code,'finished_at':utc()})
    print('Batch exit code: ' + str(code) + '. Share only the evidence directory, never private-state.', flush=True)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    return worker(args.worker) if args.worker else run_supervised(Path(__file__).resolve().parents[2])


if __name__ == '__main__':
    raise SystemExit(main())

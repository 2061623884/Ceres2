"""Capture one bounded evaluation batch through the public Guide HTTP/SSE API."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import httpx

from app.evaluation.export_runs import VERSION_FIELDS, diagnostic, summary


SCHEMA_VERSION = 'ceres-local-followup-batch-v1'
CAPTURE_SCHEMA_VERSION = 'ceres-eval-capture-v2'
TIMING_SOURCE = 'client_monotonic_from_run_post_start'
NAVIGATION_FIELDS = (
    'routing_request_id', 'opening_id', 'source_role', 'target_role',
    'authorized_role', 'status', 'show_prompt', 'continue_original',
    'criteria_version', 'anchor', 'entry_judgment', 'message',
)
TERMINAL_STATUSES = frozenset({
    'completed', 'waiting_clarification', 'waiting_confirmation', 'protected',
    'stopped', 'failed', 'interrupted',
})


def _json(response):
    response.raise_for_status()
    return response.json()


def _read_stream(client, session_id, run_id, started_at):
    events = []
    timing = {'first_interim_ms': None, 'first_final_ms': None, 'stream_complete_ms': None}
    with client.stream(
        'GET', f'/api/v1/guide/sessions/{session_id}/runs/{run_id}/stream',
        params={'after_sequence': 0},
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith('data: '):
                continue
            event = json.loads(line[6:])
            events.append(event)
            received_ms = (time.monotonic() - started_at) * 1000
            if event['type'] == 'message.interim' and timing['first_interim_ms'] is None:
                timing['first_interim_ms'] = received_ms
            elif event['type'] == 'answer.delta' and timing['first_final_ms'] is None:
                timing['first_final_ms'] = received_ms
        timing['stream_complete_ms'] = (time.monotonic() - started_at) * 1000
    return events, timing


def _prepare_case(client):
    bootstrap = _json(client.get('/api/v1/bootstrap'))
    session = _json(client.post('/api/v1/guide/sessions', json={
        'entry_context': {
            'page': 'home',
            'store_id': bootstrap['store_id'],
            'delivery_zone_id': bootstrap['delivery_zone_id'],
        },
    }))
    session_id = session['session_id']
    opening = _json(client.post(
        f'/api/v1/navigation/sessions/{session_id}/opening',
        json={'role': 'keke'},
    ))
    return bootstrap, session_id, opening


def _public_state(client, session_id):
    cart = _json(client.get('/api/v1/cart'))
    guide = _json(client.get(f'/api/v1/guide/sessions/{session_id}'))
    orders = _json(client.get('/api/v1/orders'))
    opening = _json(client.get(f'/api/v1/navigation/sessions/{session_id}/opening'))
    return {'guide': guide, 'cart': cart, 'orders': orders, 'opening': opening}


def _navigation_facts(route):
    return {key: route[key] for key in NAVIGATION_FIELDS if key in route}


def _batch_entry(plan_row, outcome, *, capture=None, navigation=None, error=None,
                 captures=None, steps=None, timing_run_id=None,
                 before=None, after=None, catalog_facts=None, timing=None):
    timing = timing or {
        'first_interim_ms': None,
        'first_final_ms': None,
        'stream_complete_ms': None,
    }
    return {
        **plan_row,
        'outcome': outcome,
        'capture': capture,
        'captures': captures if captures is not None else [],
        'steps': steps if steps is not None else [],
        'navigation': navigation,
        'error': error,
        'timing_run_id': timing_run_id,
        'before': before,
        'after': after,
        'catalog_facts': catalog_facts,
        **timing,
        'timing_source': TIMING_SOURCE,
    }


def _error_record(error):
    return {'type': type(error).__name__, 'reason': str(error)}


def _build_plan(cases, core_repeats):
    core = [case['case_id'] for case in cases if case.get('core', False)]
    other = [case['case_id'] for case in cases if not case.get('core', False)]
    plan = [
        {'case_id': case_id, 'trial': 1, 'execution_id': f'{case_id}:trial:1'}
        for case_id in core + other
    ]
    for trial in range(2, core_repeats + 1):
        plan.extend(
            {'case_id': case_id, 'trial': trial, 'execution_id': f'{case_id}:trial:{trial}'}
            for case_id in core
        )
    return plan


def _not_run_record(plan_row):
    return _batch_entry(plan_row, 'not_run')


def _write_batch(output_path, batch):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _capture_guide_run(client, bootstrap, session_id, case, route, execution_id):
    message = case['message']
    expected_session_version, expected_task_id, expected_state_version = route['anchor']
    started_at = time.monotonic()
    accepted = _json(client.post(
        f'/api/v1/guide/sessions/{session_id}/runs',
        json={
            'request_id': execution_id,
            'message': message,
            'expected_task_id': expected_task_id,
            'expected_state_version': expected_state_version,
            'expected_session_version': expected_session_version,
            'routing_request_id': execution_id,
        },
    ))
    run_id = accepted['run_id']
    events, timing = _read_stream(client, session_id, run_id, started_at)
    receipt = _json(client.get(
        f'/api/v1/guide/sessions/{session_id}/turns/{execution_id}',
    ))
    if receipt['run_id'] != run_id:
        raise RuntimeError(f'case execution {execution_id!r} receipt does not match the admitted run')
    if receipt['status'] not in TERMINAL_STATUSES:
        raise RuntimeError(f'case execution {execution_id!r} SSE ended before the run became terminal')
    result = receipt['result'] or {}
    message_result = _json(client.get(
        f'/api/v1/guide/sessions/{session_id}/messages',
        params={'after_sequence': 0, 'limit': 200},
    ))
    run_messages = [
        message_row for message_row in message_result['messages']
        if message_row['request_id'] == execution_id
    ]

    version = result.get('runtime_version')
    runtime_version = (
        {key: version[key] for key in VERSION_FIELDS if key in version}
        if isinstance(version, dict) else None
    )
    first_event = next((event for event in events if event.get('type') == 'accepted'), None)
    started_at = first_event.get('recorded_at_ms') if first_event else None
    capture = {
        'schema_version': CAPTURE_SCHEMA_VERSION,
        'owner_id': bootstrap['owner_id'],
        'session_id': session_id,
        'run_id': run_id,
        'request_id': execution_id,
        'status': receipt['status'],
        'execution_id': None,
        'run_started_at_ms': started_at,
        'runtime_summary': summary(result.get('runtime_summary')),
        'runtime_events': diagnostic(result.get('runtime_events')),
        'runtime_events_note': 'Diagnostic tail only; never complete run counts or usage totals.',
        'runtime_version': runtime_version,
        'entry_judgment': diagnostic(result.get('entry_judgment')),
        'events': [
            {key: event[key] for key in ('sequence', 'type', 'recorded_at_ms', 'elapsed_ms') if key in event}
            for event in events
        ],
        'messages': [
            {key: message_row[key] for key in ('message_id', 'role', 'kind', 'content', 'sequence') if key in message_row}
            for message_row in run_messages
        ],
        'labels': None,
        'export_source_snapshot': None,
        'version_note': (
            'runtime_version is copied from the public run receipt; '
            'HTTP capture does not expose execution_id or an export-time source snapshot.'
        ),
    }
    return capture, timing


def _execute_case(api_base, case, plan_row):
    stage = 'preparation'
    navigation = None
    before = None
    after = None
    catalog_facts = None
    captures = []
    steps = []
    capture = None
    timing = None
    timing_run_id = None
    execution_id = plan_row['execution_id']
    try:
        unsupported = [field for field in ('setup',) if case.get(field)]
        if unsupported:
            raise NotImplementedError(
                f"case execution {execution_id!r} has non-empty unsupported action field(s): "
                f"{', '.join(unsupported)}"
            )
        unsupported_ops = [
            step['op'] for step in case.get('steps', [])
            if step['op'] not in ('turn', 'confirm_plan', 'repeat_confirmation')
        ]
        if unsupported_ops:
            raise NotImplementedError(
                f"case execution {execution_id!r} declares unsupported step op(s): "
                f"{', '.join(unsupported_ops)}"
            )

        # Each trial has a new cookie jar and therefore a new owner/session.
        with httpx.Client(base_url=api_base, timeout=20.0) as client:
            bootstrap, session_id, opening = _prepare_case(client)
            before = _public_state(client, session_id)
            catalog_facts = _json(client.get('/api/v1/products', params={'page_size': 500}))
            stage = 'runner'
            last_confirmation = None

            initial_step = {'op': 'turn', 'message': case['message']}
            declared_steps = case.get('steps', [])
            action_steps = [initial_step, *declared_steps]
            for step_index, action in enumerate(action_steps):
                op = action['op'] if step_index else 'turn'
                step_before = before if step_index == 0 else _public_state(client, session_id)
                if op == 'turn':
                    request_id = execution_id if step_index == 0 else f'{execution_id}:step:{step_index}'
                    message = action['message']
                    route = _json(client.post(
                        f'/api/v1/navigation/sessions/{session_id}/routes',
                        json={
                            'request_id': request_id,
                            'opening_id': opening['opening_id'],
                            'role': 'keke',
                            'message': message,
                        },
                    ))
                    step_navigation = _navigation_facts(route)
                    if step_index == 0:
                        navigation = step_navigation
                    if route['status'] == 'switch':
                        after = _public_state(client, session_id)
                        steps.append({
                            'index': step_index, 'op': op, 'request_id': request_id,
                            'message': message, 'navigation': step_navigation,
                            'before': step_before, 'after': after, 'capture': None,
                            'timing': None, 'timing_source': TIMING_SOURCE,
                            'timing_run_id': None,
                        })
                        return _batch_entry(
                            plan_row, 'role_choice_required', capture=capture,
                            captures=captures, steps=steps, navigation=navigation,
                            before=before, after=after, catalog_facts=catalog_facts,
                            timing=timing, timing_run_id=timing_run_id,
                        )
                    if route['status'] != 'ready' or route['authorized_role'] != 'keke':
                        raise RuntimeError(f'case execution {execution_id!r} has no Keke Guide authorization')
                    current_capture, current_timing = _capture_guide_run(
                        client, bootstrap, session_id, {'case_id': case['case_id'], 'message': message},
                        route, request_id,
                    )
                    captures.append(current_capture)
                    capture = current_capture
                    if step_index == 0:
                        timing = current_timing
                        timing_run_id = current_capture['run_id']
                    after = _public_state(client, session_id)
                    steps.append({
                        'index': step_index, 'op': op, 'request_id': request_id,
                        'message': message, 'navigation': step_navigation,
                        'before': step_before, 'after': after, 'capture': current_capture,
                        'timing': current_timing, 'timing_source': TIMING_SOURCE,
                        'timing_run_id': current_capture['run_id'],
                    })
                    continue

                if op == 'confirm_plan':
                    guide = step_before['guide']
                    plan = guide['plan']
                    confirmation_body = {
                        'plan_id': plan['plan_id'],
                        'plan_version': plan['plan_version'],
                        'expected_state_version': guide['state_version'],
                        'expected_session_version': guide['session_version'],
                        'selected_items': [
                            {'sku_id': item['sku_id'], 'quantity': item['remaining_quantity']}
                            for item in plan['items']
                            if item['selected'] and item['remaining_quantity'] > 0
                        ],
                    }
                    idempotency_key = f'{execution_id}:step:{step_index}:confirm'
                    task_id = guide['task_id']
                    receipt = _json(client.post(
                        f'/api/v1/guide/tasks/{task_id}/confirm',
                        json=confirmation_body,
                        headers={'idempotency-key': idempotency_key},
                    ))
                    after = _public_state(client, session_id)
                    last_confirmation = {
                        'task_id': task_id,
                        'idempotency_key': idempotency_key,
                        'confirmation_body': confirmation_body,
                    }
                    steps.append({
                        'index': step_index, 'op': op, 'task_id': task_id,
                        'idempotency_key': idempotency_key,
                        'confirmation_body': confirmation_body,
                        'confirmation_receipt': receipt,
                        'before': step_before, 'after': after, 'capture': None,
                    })
                    continue

                if op == 'repeat_confirmation':
                    if last_confirmation is None:
                        raise RuntimeError('repeat_confirmation requires a preceding confirm_plan step')
                    receipt = _json(client.post(
                        f"/api/v1/guide/tasks/{last_confirmation['task_id']}/confirm",
                        json=last_confirmation['confirmation_body'],
                        headers={'idempotency-key': last_confirmation['idempotency_key']},
                    ))
                    after = _public_state(client, session_id)
                    steps.append({
                        'index': step_index, 'op': op,
                        'task_id': last_confirmation['task_id'],
                        'idempotency_key': last_confirmation['idempotency_key'],
                        'confirmation_body': last_confirmation['confirmation_body'],
                        'confirmation_receipt': receipt,
                        'before': step_before, 'after': after, 'capture': None,
                    })
                    continue

                raise NotImplementedError(
                    f"case execution {execution_id!r} declares unsupported step op {op!r}"
                )

            return _batch_entry(
                plan_row, 'guide_run', capture=capture, captures=captures, steps=steps,
                navigation=navigation, before=before, after=after,
                catalog_facts=catalog_facts, timing=timing, timing_run_id=timing_run_id,
            )
    except httpx.HTTPError as exc:
        outcome = 'preparation_failed' if stage == 'preparation' else 'runner_failed'
        return _batch_entry(
            plan_row, outcome, capture=capture, captures=captures, steps=steps,
            navigation=navigation, error=_error_record(exc), timing_run_id=timing_run_id,
            before=before, after=after, catalog_facts=catalog_facts, timing=timing,
        )
    except Exception as exc:
        return _batch_entry(
            plan_row, 'runner_failed', capture=capture, captures=captures, steps=steps,
            navigation=navigation, error=_error_record(exc), timing_run_id=timing_run_id,
            before=before, after=after, catalog_facts=catalog_facts, timing=timing,
        )


def run_baseline(api_base, cases_path, output_path, *, core_repeats=1,
                 max_executions=None, resume=False):
    source = cases_path.read_bytes()
    case_set = json.loads(source)
    normalized_api_base = api_base.rstrip('/')
    case_set_identity = {
        'version': case_set['version'],
        'sha256': hashlib.sha256(source).hexdigest(),
    }
    plan = _build_plan(case_set['cases'], core_repeats)

    if resume:
        previous = json.loads(output_path.read_text(encoding='utf-8'))
        if previous['schema_version'] != SCHEMA_VERSION:
            raise ValueError('cannot resume: output schema version does not match')
        if previous['case_set'] != case_set_identity:
            raise ValueError('cannot resume: case set version or SHA-256 does not match')
        if previous['plan'] != plan:
            raise ValueError('cannot resume: execution plan does not match')
        if previous['api_base'] != normalized_api_base:
            raise ValueError('cannot resume: API base does not match')
        batch = previous
    else:
        batch = {
            'schema_version': SCHEMA_VERSION,
            'api_base': normalized_api_base,
            'case_set': case_set_identity,
            'plan': plan,
            'cases': [_not_run_record(row) for row in plan],
        }
        _write_batch(output_path, batch)

    cases_by_id = {case['case_id']: case for case in case_set['cases']}
    records_by_execution = {row['execution_id']: row for row in batch['cases']}
    executed = 0
    for plan_row in plan:
        record = records_by_execution[plan_row['execution_id']]
        if record['outcome'] != 'not_run':
            continue
        if max_executions is not None and executed >= max_executions:
            break
        result = _execute_case(normalized_api_base, cases_by_id[plan_row['case_id']], plan_row)
        records_by_execution[plan_row['execution_id']] = result
        batch['cases'] = [records_by_execution[row['execution_id']] for row in plan]
        _write_batch(output_path, batch)
        executed += 1
    return batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-base', required=True)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--core-repeats', type=int, default=1)
    parser.add_argument('--max-executions', type=int)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.core_repeats < 1:
        parser.error('--core-repeats must be at least 1')
    if args.max_executions is not None and args.max_executions < 0:
        parser.error('--max-executions must not be negative')
    batch = run_baseline(
        args.api_base, args.cases, args.output,
        core_repeats=args.core_repeats,
        max_executions=args.max_executions,
        resume=args.resume,
    )
    print(json.dumps({
        'schema_version': batch['schema_version'],
        'case_set': batch['case_set'],
        'cases': len(batch['cases']),
        'output': str(args.output),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()

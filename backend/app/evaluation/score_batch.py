"""Score one frozen Ceres2 development-case set against its captured batch."""
import argparse
import hashlib
import json
from pathlib import Path

from app.evaluation.annotate_runs import RunAnnotation
from app.evaluation.batch_runs import CAPTURE_SCHEMA_VERSION, captures_for_row


CASE_SCHEMA_VERSION = 'ceres-local-followup-dev-cases-v1'
BATCH_SCHEMA_VERSION = 'ceres-local-followup-batch-v1'
REPORT_SCHEMA_VERSION = 'ceres-local-followup-score-v1'
OUTCOMES = frozenset({
    'guide_run', 'role_choice_required', 'preparation_failed', 'runner_failed', 'not_run',
})


def _read_path(value, path):
    current = value
    for part in path.split('.'):
        if isinstance(current, list) and part.isdecimal():
            index = int(part)
            if index >= len(current):
                return False, None
            current = current[index]
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def _matches(actual, operator, expected):
    if operator == 'eq':
        return actual == expected
    if operator == 'contains':
        return expected in actual
    if operator == 'min':
        return actual >= expected
    if operator == 'max':
        return actual <= expected
    if operator == 'length':
        return len(actual) == expected
    if operator == 'min_length':
        return len(actual) >= expected
    raise ValueError(f'Unsupported check operator: {operator}')


def _violation(code, severity, expected=None, actual=None, source=None):
    row = {'code': code, 'severity': severity}
    if expected is not None:
        row['expected'] = expected
    if actual is not None:
        row['actual'] = actual
    if source is not None:
        row['source'] = source
    return row


def _same_public_value(before, after, path):
    found_before, before_value = _read_path(before, path)
    found_after, after_value = _read_path(after, path)
    if not found_before or not found_after:
        return None
    return before_value == after_value


def _record_step_invariants(before, after, violations, evidence_gaps, *, cart_unchanged):
    for path, code in (
        ('orders', 'unauthorized_order_change'),
        ('opening.role', 'unauthorized_role_change'),
    ):
        equal = _same_public_value(before, after, path)
        if equal is None:
            evidence_gaps.append({'code': 'invariant_evidence_missing', 'path': path})
        elif not equal:
            violations.append(_violation(code, 'critical', source=path))

    if cart_unchanged:
        equal = _same_public_value(before, after, 'cart')
        if equal is None:
            evidence_gaps.append({'code': 'invariant_evidence_missing', 'path': 'cart'})
        elif not equal:
            violations.append(_violation(
                'unauthorized_step_cart_change', 'critical', source='cart',
            ))


def _cart_quantities(snapshot):
    found, items = _read_path(snapshot, 'cart.items')
    if not found or items is None:
        return None
    return {item['sku_id']: item['quantity'] for item in items}


def _cart_delta(before, after):
    before_quantities = _cart_quantities(before)
    after_quantities = _cart_quantities(after)
    if before_quantities is None or after_quantities is None:
        return None
    return [
        {'sku_id': sku_id, 'quantity': delta}
        for sku_id in sorted(set(before_quantities) | set(after_quantities))
        if (delta := after_quantities.get(sku_id, 0) - before_quantities.get(sku_id, 0)) != 0
    ]


def _normalized_items(items):
    return sorted(
        ({'sku_id': item['sku_id'], 'quantity': item['quantity']} for item in items),
        key=lambda item: item['sku_id'],
    )


def _expected_plan_items(snapshot):
    found, plan = _read_path(snapshot, 'guide.plan')
    if not found or plan is None:
        return None, None
    return True, _normalized_items([
        {'sku_id': item['sku_id'], 'quantity': item['remaining_quantity']}
        for item in plan['items']
        if item['selected'] and item['remaining_quantity'] > 0
    ])


def _score_confirmation_step(step, violations, evidence_gaps):
    before = step.get('before')
    after = step.get('after')
    _record_step_invariants(before, after, violations, evidence_gaps, cart_unchanged=False)

    body = step.get('confirmation_body')
    receipt = step.get('confirmation_receipt')
    key = step.get('idempotency_key')
    if body is None:
        evidence_gaps.append({'code': 'confirmation_body_missing', 'step': step['index']})
    if receipt is None:
        evidence_gaps.append({'code': 'confirmation_receipt_missing', 'step': step['index']})
    if not key:
        evidence_gaps.append({'code': 'confirmation_idempotency_key_missing', 'step': step['index']})

    found, expected_items = _expected_plan_items(before)
    if not found:
        evidence_gaps.append({'code': 'confirmation_plan_missing', 'step': step['index']})
    elif body is not None:
        plan_id_found, plan_id = _read_path(before, 'guide.plan.plan_id')
        plan_version_found, plan_version = _read_path(before, 'guide.plan.plan_version')
        if not plan_id_found or not plan_version_found:
            evidence_gaps.append({'code': 'confirmation_plan_version_missing', 'step': step['index']})
        elif (body['plan_id'], body['plan_version']) != (plan_id, plan_version):
            violations.append(_violation(
                'confirmation_plan_mismatch', 'critical',
                expected={'plan_id': plan_id, 'plan_version': plan_version},
                actual={'plan_id': body['plan_id'], 'plan_version': body['plan_version']},
                source=f'steps.{step["index"]}.confirmation_body',
            ))
        if _normalized_items(body['selected_items']) != expected_items:
            violations.append(_violation(
                'confirmation_items_mismatch', 'critical',
                expected=expected_items, actual=_normalized_items(body['selected_items']),
                source=f'steps.{step["index"]}.confirmation_body.selected_items',
            ))

    cart_delta = _cart_delta(before, after)
    if cart_delta is None:
        evidence_gaps.append({'code': 'cart_delta_evidence_missing', 'step': step['index']})
    elif receipt is None or receipt['status'] != 'success':
        if cart_delta:
            violations.append(_violation(
                'unauthorized_confirmation_cart_change', 'critical',
                actual=cart_delta, source=f'steps.{step["index"]}.after.cart',
            ))
    elif body is not None and cart_delta != _normalized_items(body['selected_items']):
        violations.append(_violation(
            'confirmation_cart_delta_mismatch', 'critical',
            expected=_normalized_items(body['selected_items']), actual=cart_delta,
            source=f'steps.{step["index"]}.after.cart',
        ))

    if receipt is not None:
        if receipt['status'] != 'success':
            violations.append(_violation(
                'confirmation_not_successful', 'major', expected='success',
                actual=receipt['status'], source=f'steps.{step["index"]}.confirmation_receipt.status',
            ))
        elif body is not None and _normalized_items(receipt['items_added']) != _normalized_items(body['selected_items']):
            violations.append(_violation(
                'confirmation_receipt_mismatch', 'critical',
                expected=_normalized_items(body['selected_items']),
                actual=_normalized_items(receipt['items_added']),
                source=f'steps.{step["index"]}.confirmation_receipt.items_added',
            ))
    return {
        'idempotency_key': key,
        'confirmation_body': body,
        'confirmation_receipt': receipt,
    }


def _score_steps(case, row, violations, evidence_gaps):
    declared_steps = case.get('steps', [])
    recorded_steps = row.get('steps')
    if recorded_steps is None:
        if declared_steps:
            evidence_gaps.append({'code': 'step_evidence_missing', 'path': 'steps'})
        else:
            _record_step_invariants(
                row.get('before'), row.get('after'), violations, evidence_gaps,
                cart_unchanged=True,
            )
        return

    expected_ops = ['turn', *(step['op'] for step in declared_steps)]
    recorded_ops = [step['op'] for step in recorded_steps]
    if recorded_ops != expected_ops:
        evidence_gaps.append({
            'code': 'step_sequence_mismatch', 'expected': expected_ops,
            'actual': recorded_ops,
        })

    confirmations = []
    for index, step in enumerate(recorded_steps):
        if step['index'] != index:
            evidence_gaps.append({
                'code': 'step_index_mismatch', 'expected': index,
                'actual': step['index'],
            })
        expected_op = expected_ops[index] if index < len(expected_ops) else None
        declared = step['op'] == expected_op
        if not declared:
            violations.append(_violation(
                'undeclared_step', 'critical', expected=expected_op,
                actual=step['op'], source=f'steps.{index}.op',
            ))

        if step['op'] == 'confirm_plan' and declared:
            confirmation = _score_confirmation_step(step, violations, evidence_gaps)
            confirmations.append(confirmation)
        elif step['op'] == 'repeat_confirmation' and declared:
            _record_step_invariants(
                step.get('before'), step.get('after'), violations, evidence_gaps,
                cart_unchanged=False,
            )
            equal = _same_public_value(step.get('before'), step.get('after'), 'cart')
            if equal is None:
                evidence_gaps.append({'code': 'invariant_evidence_missing', 'path': 'cart'})
            elif not equal:
                violations.append(_violation(
                    'repeat_confirmation_changed_cart', 'critical',
                    source=f'steps.{index}.after.cart',
                ))
            if not confirmations:
                violations.append(_violation(
                    'repeat_without_confirmation', 'critical', source=f'steps.{index}',
                ))
            else:
                previous = confirmations[-1]
                for field, code in (
                    ('idempotency_key', 'confirmation_replay_key_mismatch'),
                    ('confirmation_body', 'confirmation_replay_body_mismatch'),
                    ('confirmation_receipt', 'confirmation_replay_receipt_mismatch'),
                ):
                    actual = step.get(field)
                    if actual != previous[field]:
                        violations.append(_violation(
                            code, 'critical', expected=previous[field], actual=actual,
                            source=f'steps.{index}.{field}',
                        ))
        elif step['op'] == 'turn':
            _record_step_invariants(
                step.get('before'), step.get('after'), violations, evidence_gaps,
                cart_unchanged=True,
            )
        else:
            evidence_gaps.append({
                'code': 'unsupported_recorded_step', 'step': index, 'op': step['op'],
            })


def _score_execution(case, row, execution_id, trial):
    outcome = row.get('outcome')
    capture = row.get('capture')
    captures = captures_for_row(row)
    if outcome is None:
        outcome = 'guide_run' if capture is not None else 'not_run'
    if outcome not in OUTCOMES:
        raise ValueError(f'Unsupported outcome for {execution_id}: {outcome}')
    human_run_labels = []
    for run_capture in captures:
        if run_capture['schema_version'] != CAPTURE_SCHEMA_VERSION:
            raise ValueError(f'Unsupported capture schema_version for {execution_id}')
        labels = run_capture['labels']
        if labels is not None:
            if labels['schema_version'] != 'ceres-run-annotation-v2':
                raise ValueError(f'Unsupported annotation schema_version for {execution_id}')
            annotation = RunAnnotation.model_validate({
                field: value for field, value in labels.items() if field != 'schema_version'
            })
            if (annotation.owner_id, annotation.run_id) != (run_capture['owner_id'], run_capture['run_id']):
                raise ValueError(f'Annotation owner/run mismatch for execution_id {execution_id}')
            verdict = annotation.verdict
        else:
            verdict = None
        human_run_labels.append({
            'owner_id': run_capture['owner_id'],
            'run_id': run_capture['run_id'],
            'verdict': verdict,
        })

    labels = capture.get('labels') if capture is not None else None
    human_quality = labels['verdict'] if labels is not None else None
    violations = []
    evidence_gaps = []
    checks_evaluated = 0

    checks_to_evaluate = (
        [] if outcome in ('not_run', 'preparation_failed', 'runner_failed')
        else case.get('checks', [])
    )
    for check in checks_to_evaluate:
        found, actual = _read_path(row, check['path'])
        if not found or (actual is None and not (
            check['operator'] == 'eq' and check['expected'] is None
        )):
            evidence_gaps.append({
                'code': 'check_evidence_missing',
                'path': check['path'],
                'expected': check['expected'],
            })
            continue
        checks_evaluated += 1
        if not _matches(actual, check['operator'], check['expected']):
            violations.append(_violation(
                'hard_check_failed', 'major', expected=check['expected'],
                actual=actual, source=check['path'],
            ))

    if outcome in ('guide_run', 'role_choice_required'):
        _score_steps(case, row, violations, evidence_gaps)
        if outcome == 'guide_run' and capture is None:
            evidence_gaps.append({'code': 'capture_missing', 'path': 'capture'})
        after = row.get('after')
        guide_found, guide = _read_path(after, 'guide')
        plan_found, plan = _read_path(guide, 'plan') if guide_found else (False, None)
        if outcome == 'guide_run' and plan_found and plan is not None:
            plan_items = plan.get('items')
            catalog_items = (row.get('catalog_facts') or {}).get('items')
            if not isinstance(plan_items, list):
                evidence_gaps.append({'code': 'plan_items_missing', 'path': 'after.guide.plan.items'})
            else:
                for item in plan_items:
                    if item.get('selected', True) is False:
                        continue
                    sku_id = item.get('sku_id')
                    offer = next((
                        fact for fact in catalog_items or []
                        if fact.get('sku_id') == sku_id
                    ), None)
                    if offer is None:
                        evidence_gaps.append({
                            'code': 'catalog_offer_missing', 'sku_id': sku_id,
                        })
                        continue
                    if item.get('unit_price_fen') is None or offer.get('price_fen') is None:
                        evidence_gaps.append({
                            'code': 'catalog_offer_price_missing', 'sku_id': sku_id,
                        })
                    elif item['unit_price_fen'] != offer['price_fen']:
                        violations.append(_violation(
                            'catalog_offer_price_mismatch', 'critical',
                            expected=offer['price_fen'], actual=item['unit_price_fen'],
                            source=f'catalog_facts.items#{sku_id}.price_fen',
                        ))
                    quantity = item.get('quantity')
                    line_total = item.get('line_total_fen')
                    if quantity is not None and item.get('unit_price_fen') is not None and line_total is not None:
                        if quantity * item['unit_price_fen'] != line_total:
                            violations.append(_violation(
                                'plan_line_total_mismatch', 'critical',
                                expected=quantity * item['unit_price_fen'], actual=line_total,
                                source=f'after.guide.plan.items#{sku_id}.line_total_fen',
                            ))
                    else:
                        evidence_gaps.append({
                            'code': 'plan_line_amount_missing', 'sku_id': sku_id,
                        })

            budget_found, budget = _read_path(after, 'guide.conditions.budget_fen')
            if not budget_found:
                budget_found, budget = _read_path(after, 'guide.plan.budget_quote.budget_fen')
            if budget_found:
                if budget is None:
                    evidence_gaps.append({'code': 'budget_unknown', 'path': 'after.guide.conditions.budget_fen'})
                elif plan.get('selected_total_fen') is None:
                    evidence_gaps.append({'code': 'selected_total_missing', 'path': 'after.guide.plan.selected_total_fen'})
                elif plan['selected_total_fen'] > budget:
                    quote = plan.get('budget_quote')
                    is_pending_quote = (
                        plan.get('can_confirm') is False
                        and quote == {
                            'budget_fen': budget,
                            'total_fen': plan['selected_total_fen'],
                        }
                    )
                    cart_delta = _cart_delta(row.get('before'), after)
                    confirmed = any(
                        step.get('confirmation_receipt') is not None
                        and step['confirmation_receipt']['status'] == 'success'
                        for step in row.get('steps', [])
                    )
                    if not is_pending_quote:
                        violations.append(_violation(
                            'budget_exceeded', 'critical', expected=budget,
                            actual=plan['selected_total_fen'], source='after.guide.conditions.budget_fen',
                        ))
                    elif cart_delta:
                        violations.append(_violation(
                            'budget_quote_committed', 'critical', expected='no cart change',
                            actual=cart_delta, source='after.cart',
                        ))
                    elif confirmed:
                        violations.append(_violation(
                            'budget_quote_confirmed', 'critical', expected='confirmation unavailable',
                            actual='success', source='steps.confirmation_receipt.status',
                        ))
                    elif cart_delta is None:
                        evidence_gaps.append({
                            'code': 'budget_quote_cart_effect_unknown', 'path': 'after.cart',
                        })
                    else:
                        evidence_gaps.append({
                            'code': 'budget_quote_pending_decision',
                            'budget_fen': budget,
                            'quoted_total_fen': plan['selected_total_fen'],
                        })

    failed = bool(violations)
    if failed:
        business_verdict = 'fail'
    elif evidence_gaps or checks_evaluated == 0:
        business_verdict = 'unknown'
    else:
        business_verdict = 'pass'

    budget_found, budget_fen = _read_path(row, 'after.guide.conditions.budget_fen')
    if not budget_found:
        budget_found, budget_fen = _read_path(row, 'after.guide.plan.budget_quote.budget_fen')
    if not budget_found:
        budget_fen = None

    result = {
        'case_id': case['case_id'],
        'trial': trial,
        'execution_id': execution_id,
        'outcome': outcome,
        'business_verdict': business_verdict,
        'human_quality': human_quality,
        'human_quality_scope': 'last_guide_run',
        'human_run_labels': human_run_labels,
        'budget_fen': budget_fen,
        'violations': violations,
        'evidence_gaps': evidence_gaps,
    }
    if capture is not None:
        result['owner_id'] = capture['owner_id']
        result['run_id'] = capture['run_id']
    return result


def score_batch(cases_path: Path, batch_path: Path, output_path: Path):
    case_bytes = cases_path.read_bytes()
    case_set = json.loads(case_bytes)
    batch_bytes = batch_path.read_bytes()
    batch = json.loads(batch_bytes)
    if case_set['schema_version'] != CASE_SCHEMA_VERSION:
        raise ValueError(f'Unsupported cases schema_version: {case_set["schema_version"]}')
    if batch['schema_version'] != BATCH_SCHEMA_VERSION:
        raise ValueError(f'Unsupported batch schema_version: {batch["schema_version"]}')
    case_version = case_set['version']
    case_sha = hashlib.sha256(case_bytes).hexdigest()
    if batch['case_set'] != {'version': case_version, 'sha256': case_sha}:
        raise ValueError('Batch case_set does not match the supplied cases file version and SHA-256')

    cases_by_id = {case['case_id']: case for case in case_set['cases']}
    if len(cases_by_id) != len(case_set['cases']):
        raise ValueError('Duplicate case_id in cases file')

    has_explicit_plan = 'plan' in batch
    batch_rows = {}
    for row in batch['cases']:
        case_id = row['case_id']
        if case_id not in cases_by_id:
            raise ValueError(f'Unknown case_id in batch: {case_id}')
        execution_id = (row.get('execution_id') or case_id) if has_explicit_plan else case_id
        if execution_id in batch_rows:
            raise ValueError(f'Duplicate execution_id in batch: {execution_id}')
        batch_rows[execution_id] = row

    if has_explicit_plan:
        plan = batch['plan']
    else:
        plan = [
            {
                'case_id': case['case_id'], 'trial': 1,
                'execution_id': case['case_id'],
            }
            for case in case_set['cases']
        ]

    plan_ids = [entry['execution_id'] for entry in plan]
    if len(set(plan_ids)) != len(plan_ids):
        raise ValueError('Duplicate execution_id in plan')
    plan_case_ids = {entry['case_id'] for entry in plan}
    missing_plan_cases = set(cases_by_id) - plan_case_ids
    if missing_plan_cases:
        raise ValueError(f'Plan omits cases from the supplied case set: {sorted(missing_plan_cases)}')
    if has_explicit_plan:
        unexpected_rows = set(batch_rows) - set(plan_ids)
        if unexpected_rows:
            raise ValueError(f'Batch contains execution_ids absent from plan: {sorted(unexpected_rows)}')
    results = []
    counts = {
        'planned': len(plan), 'attempted': 0, 'guide_run': 0, 'role_wait': 0,
        'preparation_failed': 0, 'runner_failed': 0, 'not_run': 0,
    }
    for entry in plan:
        case_id = entry['case_id']
        if case_id not in cases_by_id:
            raise ValueError(f'Unknown case_id in plan: {case_id}')
        execution_id = entry['execution_id']
        row = batch_rows.get(execution_id)
        if row is None:
            row = {'case_id': case_id, 'outcome': 'not_run', 'capture': None}
        elif row['case_id'] != case_id:
            raise ValueError(f'Plan/batch case_id mismatch for execution_id {execution_id}')
        result = _score_execution(cases_by_id[case_id], row, execution_id, entry['trial'])
        results.append(result)
        outcome = result['outcome']
        counts['attempted'] += outcome != 'not_run'
        if outcome == 'guide_run':
            counts['guide_run'] += 1
        elif outcome == 'role_choice_required':
            counts['role_wait'] += 1
        else:
            counts[outcome] += 1

    report = {
        'schema_version': REPORT_SCHEMA_VERSION,
        'case_set': {'version': case_version, 'sha256': case_sha},
        'batch_sha256': hashlib.sha256(batch_bytes).hexdigest(),
        'counts': counts,
        'cases': results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'schema_version': REPORT_SCHEMA_VERSION, 'counts': counts, 'output': str(output_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(score_batch(args.cases, args.batch, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()

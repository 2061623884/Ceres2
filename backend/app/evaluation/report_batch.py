"""Aggregate public evaluation outcomes without inventing missing quality or usage."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

from app.evaluation.batch_runs import annotation_for_capture, captures_for_row


CASE_SCHEMA_VERSION = 'ceres-local-followup-dev-cases-v1'
BATCH_SCHEMA_VERSION = 'ceres-local-followup-batch-v1'
SCORE_SCHEMA_VERSION = 'ceres-local-followup-score-v1'
REPORT_SCHEMA_VERSION = 'ceres-local-followup-report-v1'
VERDICTS = ('pass', 'fail', 'unknown')
TIMING_FIELDS = ('first_interim_ms', 'first_final_ms', 'stream_complete_ms')
TURN_DEADLINE_MS = 15000
GUIDE_TERMINAL_STATUSES = (
    'completed', 'waiting_clarification', 'waiting_confirmation', 'protected',
    'stopped', 'failed', 'interrupted',
)


def _counts():
    return {verdict: 0 for verdict in VERDICTS}


def _percentile(values, percentile):
    if not values:
        return None
    ordered = sorted(values)
    rank = math.ceil(percentile * len(ordered))
    return ordered[rank - 1]


def _latency_summary(values):
    return {
        'samples': len(values),
        'p50': _percentile(values, 0.50),
        'p95': _percentile(values, 0.95),
    }


def _turn_records(row):
    if 'steps' in row:
        return [
            (step['capture'], step.get('timing'))
            for step in row['steps']
            if step['op'] == 'turn' and step.get('capture') is not None
        ]
    if row.get('capture') is not None:
        return [(row['capture'], row.get('timing'))]
    return []


def _deadline_counts(records):
    counts = {'samples': len(records), 'pass': 0, 'timeout': 0, 'unknown': 0}
    for _, timing in records:
        duration = timing.get('stream_complete_ms') if timing is not None else None
        if duration is None:
            counts['unknown'] += 1
        elif duration <= TURN_DEADLINE_MS:
            counts['pass'] += 1
        else:
            counts['timeout'] += 1
    return counts


def _critical_violations(score_rows):
    eligible = 0
    executions = set()
    details = []
    for score_row in score_rows:
        if score_row['outcome'] in ('guide_run', 'role_choice_required'):
            eligible += 1
        for violation in score_row.get('violations', []):
            if violation.get('severity') != 'critical':
                continue
            executions.add(score_row['execution_id'])
            details.append({
                'case_id': score_row['case_id'],
                'execution_id': score_row['execution_id'],
                **violation,
            })
    return {
        'executions_with_findings': len(executions),
        'findings': len(details),
        'execution_denominator': eligible,
        'details': details,
    }, executions


def _case_execution_key(row, has_plan):
    return row['execution_id'] if has_plan else row['case_id']


def _capture_labels(captures, identities):
    reviewed = 0
    unreviewed = 0
    verdicts = Counter()
    failed_error_types = Counter()
    provider_coverage = {
        'guide_runs': len(captures),
        'provider_call_summary_complete_runs': 0,
        'observed_usage_complete_runs': 0,
    }
    run_summaries = []
    for capture in captures:
        annotation = annotation_for_capture(capture, f'run {capture["run_id"]}')
        identity = (capture['owner_id'], capture['run_id'])
        if identity in identities:
            raise ValueError(f'Duplicate capture owner/run: {identity[0]} / {identity[1]}')
        identities.add(identity)

        if annotation is None:
            unreviewed += 1
        else:
            reviewed += 1
            verdicts[annotation.verdict] += 1
            if annotation.verdict == 'fail':
                failed_error_types[annotation.error_type] += 1

        summary = capture.get('runtime_summary')
        if summary is None:
            run_summaries.append(None)
            continue
        calls = summary.get('provider_calls')
        summary_complete = (
            summary.get('provider_calls_complete') is True
            and summary.get('provider_records_truncated') is False
            and isinstance(calls, dict)
            and bool(calls)
        )
        if summary_complete:
            provider_coverage['provider_call_summary_complete_runs'] += 1
        usage_complete = summary_complete and all(
            metrics['usage_complete'] is True
            and metrics['observed_usage'] is not None
            and all(value is not None for value in metrics['observed_usage'].values())
            for metrics in calls.values()
        )
        if usage_complete:
            provider_coverage['observed_usage_complete_runs'] += 1
        run_summaries.append({
            'summary_complete': summary_complete,
            'usage_complete': usage_complete,
            'provider_calls': calls if summary_complete else None,
        })

    human = {
        'reviewed': reviewed,
        'unreviewed': unreviewed,
        'verdicts': {verdict: verdicts[verdict] for verdict in ('pass', 'fail', 'needs_review')},
        'failed_error_types': dict(sorted(failed_error_types.items())),
    }
    return human, provider_coverage, run_summaries


def _provider_usage(coverage, run_summaries):
    guide_runs = coverage['guide_runs']
    summary_complete = (
        guide_runs > 0
        and coverage['provider_call_summary_complete_runs'] == guide_runs
    )
    usage_complete = (
        guide_runs > 0
        and coverage['observed_usage_complete_runs'] == guide_runs
    )
    calls_by_stage = None
    if summary_complete:
        stage_totals = defaultdict(lambda: {'started': 0, 'completed': 0})
        for summary in run_summaries:
            for stage, metrics in summary['provider_calls'].items():
                stage_totals[stage]['started'] += metrics['started']
                stage_totals[stage]['completed'] += metrics['completed']
        calls_by_stage = dict(sorted(stage_totals.items()))

    observed_usage = None
    if usage_complete:
        totals = Counter()
        for summary in run_summaries:
            for metrics in summary['provider_calls'].values():
                totals.update(metrics['observed_usage'])
        observed_usage = dict(sorted(totals.items()))

    return {
        'coverage': coverage,
        'provider_call_counts_complete': summary_complete if guide_runs else None,
        'calls_by_stage': calls_by_stage,
        'observed_usage_complete': usage_complete if guide_runs else None,
        'observed_usage': observed_usage,
        'cost': None,
    }


def aggregate_report(cases_path: Path, batch_path: Path, score_path: Path, output_path: Path):
    cases_bytes = cases_path.read_bytes()
    case_set = json.loads(cases_bytes)
    batch_bytes = batch_path.read_bytes()
    batch = json.loads(batch_bytes)
    score_bytes = score_path.read_bytes()
    score = json.loads(score_bytes)
    if case_set['schema_version'] != CASE_SCHEMA_VERSION:
        raise ValueError(f'Unsupported cases schema_version: {case_set["schema_version"]}')
    if batch['schema_version'] != BATCH_SCHEMA_VERSION:
        raise ValueError(f'Unsupported batch schema_version: {batch["schema_version"]}')
    if score['schema_version'] != SCORE_SCHEMA_VERSION:
        raise ValueError(f'Unsupported score schema_version: {score["schema_version"]}')
    case_set_identity = {
        'version': case_set['version'],
        'sha256': hashlib.sha256(cases_bytes).hexdigest(),
    }
    if batch['case_set'] != case_set_identity or score['case_set'] != case_set_identity:
        raise ValueError('Cases, batch and score must use the same case set version and SHA-256')
    batch_sha = hashlib.sha256(batch_bytes).hexdigest()
    if score.get('batch_sha256') != batch_sha:
        raise ValueError('Score batch_sha256 does not match the supplied batch')

    cases_by_id = {case['case_id']: case for case in case_set['cases']}
    if len(cases_by_id) != len(case_set['cases']):
        raise ValueError('Duplicate case_id in cases file')
    has_plan = 'plan' in batch
    plan = batch['plan'] if has_plan else [
        {'case_id': case['case_id'], 'trial': 1, 'execution_id': case['case_id']}
        for case in case_set['cases']
    ]
    expected_keys = [_case_execution_key(entry, True) for entry in plan]
    score_rows = {}
    for row in score['cases']:
        key = row['execution_id']
        if key in score_rows:
            raise ValueError(f'Duplicate score execution_id: {key}')
        if key not in expected_keys:
            raise ValueError(f'Score execution_id is absent from batch plan: {key}')
        score_rows[key] = row
    if set(score_rows) != set(expected_keys):
        raise ValueError('Score report does not preserve every planned execution')

    batch_rows = {}
    for row in batch['cases']:
        key = _case_execution_key(row, has_plan)
        if key in batch_rows:
            raise ValueError(f'Duplicate batch execution key: {key}')
        batch_rows[key] = row

    business_verdicts = _counts()
    categories = {}
    core_rows = []
    core_cases = []
    for case in case_set['cases']:
        case_scores = [row for row in score['cases'] if row['case_id'] == case['case_id']]
        category = categories.setdefault(case['category'], {
            'planned': 0,
            'attempted': 0,
            'business_verdicts': _counts(),
        })
        for row in case_scores:
            verdict = row['business_verdict']
            business_verdicts[verdict] += 1
            category['planned'] += 1
            category['attempted'] += row['outcome'] != 'not_run'
            category['business_verdicts'][verdict] += 1
        if case.get('core') is True:
            verdict_counts = _counts()
            attempted = 0
            for row in case_scores:
                verdict_counts[row['business_verdict']] += 1
                attempted += row['outcome'] != 'not_run'
            core_rows.append({
                'case_id': case['case_id'],
                'planned': len(case_scores),
                'attempted': attempted,
                'business_verdicts': verdict_counts,
                'three_trials_business_pass': (
                    len(case_scores) == 3
                    and attempted == 3
                    and verdict_counts['pass'] == 3
                ),
            })
            core_cases.append((case['case_id'], case_scores))

    timings = {field: [] for field in TIMING_FIELDS}
    all_captures = []
    identities = set()
    guide_statuses = {status: 0 for status in GUIDE_TERMINAL_STATUSES}
    guide_statuses['unknown'] = 0
    turn_records_by_execution = {}
    for key, score_row in score_rows.items():
        batch_row = batch_rows.get(key)
        if batch_row is None:
            turn_records_by_execution[key] = []
            continue
        row_captures = captures_for_row(batch_row)
        all_captures.extend(row_captures)
        for capture_row in row_captures:
            status = capture_row.get('status')
            guide_statuses[status if status in GUIDE_TERMINAL_STATUSES else 'unknown'] += 1
        turn_records = _turn_records(batch_row)
        turn_records_by_execution[key] = turn_records
        for _, timing in turn_records:
            if timing is None:
                continue
            for field in TIMING_FIELDS:
                value = timing.get(field)
                if value is not None:
                    timings[field].append(value)

    critical_violations, critical_execution_ids = _critical_violations(score['cases'])
    core_trial_stability = []
    for case_id, case_scores in core_cases:
        trials = []
        for score_row in case_scores:
            execution_id = score_row['execution_id']
            turn_deadline = _deadline_counts(turn_records_by_execution.get(execution_id, []))
            has_critical = execution_id in critical_execution_ids
            performance_pass = (
                turn_deadline['samples'] > 0
                and turn_deadline['pass'] == turn_deadline['samples']
            )
            trials.append({
                'trial': score_row['trial'],
                'execution_id': execution_id,
                'business_verdict': score_row['business_verdict'],
                'critical_violation': has_critical,
                'turn_deadline_15s': turn_deadline,
                'business_and_performance_pass': (
                    score_row['business_verdict'] == 'pass'
                    and not has_critical
                    and performance_pass
                ),
            })
        core_trial_stability.append({
            'case_id': case_id,
            'trials': trials,
            'three_trials_business_pass': (
                len(trials) == 3
                and all(trial['business_verdict'] == 'pass' for trial in trials)
            ),
            'three_trials_performance_pass': (
                len(trials) == 3
                and all(
                    trial['turn_deadline_15s']['samples'] > 0
                    and trial['turn_deadline_15s']['pass'] == trial['turn_deadline_15s']['samples']
                    for trial in trials
                )
            ),
            'three_trials_combined_pass': (
                len(trials) == 3
                and all(trial['business_and_performance_pass'] for trial in trials)
            ),
        })

    human, provider_coverage, run_summaries = _capture_labels(all_captures, identities)
    turn_deadline = _deadline_counts([
        record
        for execution_records in turn_records_by_execution.values()
        for record in execution_records
    ])
    report = {
        'schema_version': REPORT_SCHEMA_VERSION,
        'case_set': case_set_identity,
        'source_sha256': {
            'batch': batch_sha,
            'score': hashlib.sha256(score_bytes).hexdigest(),
        },
        'counts': score['counts'],
        'business_verdicts': business_verdicts,
        'guide_runs': {
            'observed': len(all_captures),
            'terminal_statuses': guide_statuses,
        },
        'critical_violations': critical_violations,
        'turn_deadline_15s': {'limit_ms': TURN_DEADLINE_MS, **turn_deadline},
        'first_useful_result_ms': {
            'samples': turn_deadline['samples'],
            'observed': 0,
            'unknown': turn_deadline['samples'],
            'p50': None,
            'p95': None,
            'human_annotated': False,
            'definition': (
                'Not measured in the current batch contract; tool progress and first interim/final bytes '
                'are not evidence of a useful result.'
            ),
        },
        'categories': categories,
        'core_cases': core_rows,
        'core_trial_stability': core_trial_stability,
        'latency_ms': {
            field: _latency_summary(values) for field, values in timings.items()
        },
        'human_runs': human,
        'provider_usage': _provider_usage(provider_coverage, run_summaries),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {
        'schema_version': REPORT_SCHEMA_VERSION,
        'counts': score['counts'],
        'output': str(output_path),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--score', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(aggregate_report(args.cases, args.batch, args.score, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()

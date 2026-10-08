"""Create regression cases only from explicitly failed, owner-scoped regression runs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from app.evaluation.batch_runs import annotation_for_capture, captures_for_row


CASE_SCHEMA_VERSION = 'ceres-local-followup-dev-cases-v1'
BATCH_SCHEMA_VERSION = 'ceres-local-followup-batch-v1'


def failure_intake(cases_path: Path, batch_path: Path, output_path: Path):
    cases_bytes = cases_path.read_bytes()
    case_set = json.loads(cases_bytes)
    batch_bytes = batch_path.read_bytes()
    batch = json.loads(batch_bytes)
    if case_set['schema_version'] != CASE_SCHEMA_VERSION:
        raise ValueError(f'Unsupported cases schema_version: {case_set["schema_version"]}')
    if batch['schema_version'] != BATCH_SCHEMA_VERSION:
        raise ValueError(f'Unsupported batch schema_version: {batch["schema_version"]}')
    case_set_identity = {
        'version': case_set['version'],
        'sha256': hashlib.sha256(cases_bytes).hexdigest(),
    }
    if batch['case_set'] != case_set_identity:
        raise ValueError('Batch case_set does not match the supplied cases file version and SHA-256')

    cases_by_id = {case['case_id']: case for case in case_set['cases']}
    if len(cases_by_id) != len(case_set['cases']):
        raise ValueError('Duplicate case_id in cases file')
    excluded_cases_by_split = dict(sorted(Counter(
        case['split'] for case in case_set['cases'] if case['split'] != 'regression'
    ).items()))

    batch_sha = hashlib.sha256(batch_bytes).hexdigest()
    source_runs = {}
    for row in batch['cases']:
        case_id = row['case_id']
        if case_id not in cases_by_id:
            raise ValueError(f'Unknown case_id in batch: {case_id}')
        if cases_by_id[case_id]['split'] != 'regression':
            continue
        execution_id = row.get('execution_id', case_id)
        trial = row.get('trial', 1)
        captures = captures_for_row(row)
        for capture_index, capture in enumerate(captures, start=1):
            annotation = annotation_for_capture(capture, f'case {case_id}')
            identity = (capture['owner_id'], capture['run_id'])
            if identity in source_runs:
                raise ValueError(f'Duplicate capture owner/run: {identity[0]} / {identity[1]}')
            source_runs[identity] = {
                'case_id': case_id,
                'execution_id': execution_id,
                'trial': trial,
                'capture_index': capture_index,
                'capture': capture,
                'annotation': annotation,
            }

    failure_cases = []
    for (owner_id, run_id), source in source_runs.items():
        annotation = source['annotation']
        original = cases_by_id[source['case_id']]
        if annotation is None or annotation.verdict != 'fail':
            continue
        case_id = (
            f"failure-{source['case_id']}-trial-{source['trial']}-"
            f"run-{source['capture_index']}"
        )
        regression_case = {
            'case_id': case_id,
            'message': original['message'],
            'category': original['category'],
            'scenario_family': original['scenario_family'],
            'split': 'regression',
            'core': False,
            'expected_behavior': annotation.expected_behavior,
            'fact_sources': original['fact_sources'],
            'checks': original['checks'],
            'failure_source': {
                'case_set': case_set_identity,
                'source_batch_sha256': batch_sha,
                'case_id': source['case_id'],
                'trial': source['trial'],
                'execution_id': source['execution_id'],
                'capture_index': source['capture_index'],
                'owner_id': owner_id,
                'run_id': run_id,
                'verdict': annotation.verdict,
                'error_type': annotation.error_type,
                'severity': annotation.severity,
                'rationale': annotation.rationale,
                'reviewer': annotation.reviewer,
                'reviewed_at': annotation.reviewed_at.isoformat(),
            },
        }
        if 'steps' in original:
            regression_case['steps'] = original['steps']
        failure_cases.append(regression_case)

    cases_sha = case_set_identity['sha256'][:12]
    batch_sha_short = batch_sha[:12]
    output_set = {
        'schema_version': CASE_SCHEMA_VERSION,
        'version': f"{case_set['version']}-failures-{cases_sha}-{batch_sha_short}",
        'source': {
            'case_set': case_set_identity,
            'batch_sha256': batch_sha,
            'intake_rule': 'explicit_manual_fail_annotations_from_regression_cases_only',
            'excluded_cases_by_split': excluded_cases_by_split,
            'exclusion_reason': 'only_regression_cases_are_eligible_for_failure_intake',
        },
        'cases': failure_cases,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_set, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {
        'cases': len(failure_cases),
        'source_batch_sha256': batch_sha,
        'output': str(output_path),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(failure_intake(args.cases, args.batch, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()

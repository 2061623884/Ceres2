"""Compare two explicit public development batches without inferring quality."""
import argparse
import json
from pathlib import Path

from .annotate_runs import RunAnnotation
from .batch_runs import CAPTURE_SCHEMA_VERSION, captures_for_row


BATCH_SCHEMA_VERSION = 'ceres-local-followup-batch-v1'
ANNOTATION_SCHEMA_VERSION = 'ceres-run-annotation-v2'
REPORT_SCHEMA_VERSION = 'ceres-eval-comparison-v1'


def load_batch(path: Path):
    batch = json.loads(path.read_text(encoding='utf-8'))
    if batch['schema_version'] != BATCH_SCHEMA_VERSION:
        raise ValueError(f'Unsupported batch schema_version: {batch["schema_version"]}')
    case_set = {'version': batch['case_set']['version'], 'sha256': batch['case_set']['sha256']}
    has_plan = 'plan' in batch
    rows = {}
    plan_by_execution = {}
    if has_plan:
        for entry in batch['plan']:
            execution_id = entry['execution_id']
            if execution_id in plan_by_execution:
                raise ValueError(f'Duplicate execution_id in plan: {execution_id}')
            plan_by_execution[execution_id] = entry

    for item in batch['cases']:
        case_id = item['case_id']
        captures = captures_for_row(item)
        if has_plan:
            execution_id = item['execution_id']
            plan_entry = plan_by_execution.get(execution_id)
            if plan_entry is None:
                raise ValueError(f'Batch execution_id is absent from plan: {execution_id}')
            if (plan_entry['case_id'], plan_entry['trial']) != (case_id, item['trial']):
                raise ValueError(f'Plan/batch case or trial mismatch for execution_id {execution_id}')
            key = execution_id
        else:
            key = case_id
        if key in rows:
            raise ValueError(f'Duplicate {"execution_id" if has_plan else "case_id"} in batch: {key}')
        for capture in captures:
            if capture['schema_version'] != CAPTURE_SCHEMA_VERSION:
                raise ValueError(f'Unsupported capture schema_version for case {case_id}')
            owner_id = capture['owner_id']
            run_id = capture['run_id']
            labels = capture['labels']
            if labels is not None:
                if labels['schema_version'] != ANNOTATION_SCHEMA_VERSION:
                    raise ValueError(f'Unsupported annotation schema_version for case {case_id}')
                annotation = RunAnnotation.model_validate({
                    field: value for field, value in labels.items() if field != 'schema_version'
                })
                if annotation.owner_id != owner_id or annotation.run_id != run_id:
                    raise ValueError(f'Annotation owner/run mismatch for case {case_id}')
        rows[key] = item

    if has_plan:
        for execution_id, entry in plan_by_execution.items():
            rows.setdefault(execution_id, {
                **entry, 'outcome': 'not_run', 'capture': None,
            })
    return case_set, rows, has_plan


def comparison_side(row):
    captures = captures_for_row(row)
    capture = row.get('capture')
    labels = capture['labels'] if capture is not None else None
    if labels is None:
        quality_verdict = 'unknown'
    else:
        quality_verdict = labels['verdict']
    return {
        'outcome': row.get('outcome') or ('guide_run' if capture is not None else 'not_run'),
        'owner_id': capture['owner_id'] if capture is not None else None,
        'run_id': capture['run_id'] if capture is not None else None,
        'quality_verdict': quality_verdict,
        'quality_scope': 'last_guide_run',
        'human_run_labels': [
            {
                'owner_id': run_capture['owner_id'],
                'run_id': run_capture['run_id'],
                'verdict': run_capture['labels']['verdict'] if run_capture['labels'] is not None else None,
            }
            for run_capture in captures
        ],
        'runtime_version': capture.get('runtime_version') if capture is not None else None,
    }


def compare_runs(baseline: Path, candidate: Path, output: Path):
    baseline_set, baseline_cases, baseline_has_plan = load_batch(baseline)
    candidate_set, candidate_cases, candidate_has_plan = load_batch(candidate)
    baseline_ids = list(baseline_cases)
    candidate_ids = list(candidate_cases)
    paired_ids = [execution_id for execution_id in baseline_ids if execution_id in candidate_cases]
    report = {
        'schema_version': REPORT_SCHEMA_VERSION,
        'case_sets': {'baseline': baseline_set, 'candidate': candidate_set},
        'same_input': baseline_set == candidate_set,
        'pairs': [
            {
                'case_id': baseline_cases[key]['case_id'],
                'trial': baseline_cases[key].get('trial'),
                'execution_id': baseline_cases[key].get('execution_id') if baseline_has_plan else None,
                'baseline': comparison_side(baseline_cases[key]),
                'candidate': comparison_side(candidate_cases[key]),
            }
            for key in paired_ids
        ],
        'unpaired_baseline_execution_ids' if baseline_has_plan else 'unpaired_baseline_case_ids': [
            key for key in baseline_ids if key not in candidate_cases
        ],
        'unpaired_candidate_execution_ids' if candidate_has_plan else 'unpaired_candidate_case_ids': [
            key for key in candidate_ids if key not in baseline_cases
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'pairs': len(paired_ids), 'output': str(output), 'schema_version': REPORT_SCHEMA_VERSION}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compare_runs(args.baseline, args.candidate, args.output), ensure_ascii=False))

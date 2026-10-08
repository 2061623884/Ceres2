"""Attach explicit v2 human annotations to runs in a local evaluation batch."""
import argparse
import json
from pathlib import Path

from .annotate_runs import RunAnnotation


BATCH_SCHEMA_VERSION = 'ceres-local-followup-batch-v1'
CAPTURE_SCHEMA_VERSION = 'ceres-eval-capture-v2'
ANNOTATION_SCHEMA_VERSION = 'ceres-run-annotation-v2'


def annotate_batch(captures: Path, annotations: Path, output: Path):
    batch = json.loads(captures.read_text(encoding='utf-8'))
    if batch['schema_version'] != BATCH_SCHEMA_VERSION:
        raise ValueError(f'Unsupported batch schema_version: {batch["schema_version"]}')

    by_owner_run = {}
    owner_run_rows = {}
    for row_index, item in enumerate(batch['cases']):
        case_id = item['case_id']
        row_identity = row_index
        row_captures = item.get('captures')
        seen_in_row = set()

        def add_capture(capture, *, final_alias=False):
            if capture['schema_version'] != CAPTURE_SCHEMA_VERSION:
                raise ValueError(f'Unsupported capture schema_version for case {case_id}')
            identity = (capture['owner_id'], capture['run_id'])
            existing_row = owner_run_rows.get(identity)
            if existing_row is not None and existing_row != row_identity:
                raise ValueError(f'Duplicate capture owner/run: {identity[0]} / {identity[1]}')
            if identity in seen_in_row and not final_alias:
                raise ValueError(f'Duplicate capture owner/run: {identity[0]} / {identity[1]}')
            seen_in_row.add(identity)
            owner_run_rows[identity] = row_identity
            by_owner_run.setdefault(identity, []).append(capture)

        if row_captures is not None:
            for capture in row_captures:
                add_capture(capture)

        capture = item.get('capture')
        if capture is not None:
            if row_captures is not None:
                if not row_captures or capture != row_captures[-1]:
                    raise ValueError(f'Final capture does not match the last capture for case {case_id}')
                add_capture(capture, final_alias=True)
            else:
                add_capture(capture)

    seen = set()
    for line in annotations.read_text(encoding='utf-8').splitlines():
        annotation = RunAnnotation.model_validate_json(line)
        identity = (annotation.owner_id, annotation.run_id)
        if identity in seen:
            raise ValueError(f'Duplicate annotation owner/run: {identity[0]} / {identity[1]}')
        if identity not in by_owner_run:
            raise ValueError(f'Unknown annotation owner/run: {identity[0]} / {identity[1]}')
        seen.add(identity)
        labels = {
            'schema_version': ANNOTATION_SCHEMA_VERSION,
            **annotation.model_dump(mode='json'),
        }
        for capture in by_owner_run[identity]:
            capture['labels'] = labels

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'cases': len(batch['cases']), 'annotated': len(seen), 'output': str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', type=Path, required=True)
    parser.add_argument('--annotations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(annotate_batch(args.captures, args.annotations, args.output), ensure_ascii=False))

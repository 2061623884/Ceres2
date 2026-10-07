"""Join explicit human labels to one owner's fixed JSONL; never infer quality."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class RunAnnotation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    owner_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    verdict: Literal['pass', 'fail', 'needs_review']
    error_type: str = Field(min_length=1)
    severity: Literal['none', 'minor', 'major', 'critical']
    expected_behavior: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    reviewed_at: datetime


def annotate(owner_id: str, captures: Path, annotations: Path, output: Path):
    if not owner_id.strip():
        raise ValueError('owner_id must be explicit and nonempty')
    records = [json.loads(line) for line in captures.read_text(encoding='utf-8').splitlines()]
    by_run = {}
    for record in records:
        if record['owner_id'] != owner_id:
            raise ValueError('Capture owner mismatch')
        if record['run_id'] in by_run:
            raise ValueError('Duplicate capture run_id')
        by_run[record['run_id']] = record
    seen = set()
    for line in annotations.read_text(encoding='utf-8').splitlines():
        annotation = RunAnnotation.model_validate_json(line)
        if annotation.owner_id != owner_id:
            raise ValueError('Annotation owner mismatch')
        if annotation.run_id in seen:
            raise ValueError('Duplicate annotation run_id')
        if annotation.run_id not in by_run:
            raise ValueError('Unknown annotation run_id')
        seen.add(annotation.run_id)
        by_run[annotation.run_id]['labels'] = {'schema_version': 'ceres-run-annotation-v2',
                                               **annotation.model_dump(mode='json')}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(''.join(json.dumps(record, ensure_ascii=False) + '\n' for record in records), encoding='utf-8')
    return {'records': len(records), 'annotated': len(seen), 'output': str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner-id', required=True)
    parser.add_argument('--captures', type=Path, required=True)
    parser.add_argument('--annotations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(annotate(args.owner_id, args.captures, args.annotations, args.output), ensure_ascii=False))

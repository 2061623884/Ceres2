"""Join explicit reviewer labels to captured runs; never infer a quality label."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class RunAnnotation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    run_id: str = Field(min_length=1)
    verdict: Literal['pass', 'fail', 'needs_review']
    error_type: str = Field(min_length=1)
    severity: Literal['none', 'minor', 'major', 'critical']
    expected_behavior: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    reviewed_at: datetime


def annotate(captures: Path, annotations: Path, output: Path):
    records = [json.loads(line) for line in captures.read_text().splitlines()]
    by_run = {record['run_id']:record for record in records}
    seen = set()
    for line in annotations.read_text().splitlines():
        annotation = RunAnnotation.model_validate_json(line)
        if annotation.run_id in seen:
            raise ValueError('One annotation per run is required in this review file')
        seen.add(annotation.run_id)
        by_run[annotation.run_id]['labels'] = {'schema_version':'ceres-run-annotation-v1',
            **annotation.model_dump(mode='json')}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(''.join(json.dumps(record, ensure_ascii=False)+'\n' for record in records))
    return {'records':len(records), 'annotated':len(seen), 'output':str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--captures', type=Path, required=True)
    parser.add_argument('--annotations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(annotate(args.captures, args.annotations, args.output), ensure_ascii=False))

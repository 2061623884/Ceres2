"""Explicit human labels, owner joins and duplicate rejection via public CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest


def invoke(tmp_path, captures, annotations, owner='alice'):
    source = tmp_path/'captures.jsonl'; labels = tmp_path/'labels.jsonl'; output = tmp_path/'reviewed.jsonl'
    source.write_text(''.join(json.dumps(row)+'\n' for row in captures))
    labels.write_text(''.join(json.dumps(row)+'\n' for row in annotations))
    args = ['--captures',str(source),'--annotations',str(labels),'--output',str(output)]
    if owner is not None: args += ['--owner-id',owner]
    process = subprocess.run([sys.executable,'-m','app.evaluation.annotate_runs',*args],
        cwd=Path(__file__).resolve().parents[1], env=os.environ.copy(), capture_output=True, text=True)
    return process, output


def capture(run='run-a', owner='alice'):
    return {'schema_version':'ceres-eval-capture-v2','owner_id':owner,'run_id':run,'session_id':'session-a',
            'request_id':'request-a','status':'failed','labels':None,'cart_accepted':True}


def annotation(run='run-a', owner='alice'):
    return {'owner_id':owner,'run_id':run,'verdict':'fail','error_type':'wrong_fact','severity':'major',
            'expected_behavior':'Use canonical facts','rationale':'Fixture observation',
            'reviewer':'fixture-human','reviewed_at':'2026-10-07T00:00:00Z'}


def test_annotation_explicit_labels_and_unreviewed_failure(tmp_path):
    result, output = invoke(tmp_path,[capture(),capture('run-b')],[annotation()])
    assert result.returncode == 0, result.stderr
    rows = list(map(json.loads,output.read_text().splitlines()))
    assert rows[0]['labels']['verdict'] == 'fail'
    assert rows[0]['labels']['reviewer'] == 'fixture-human'
    assert rows[1]['labels'] is None
    assert rows[0]['cart_accepted'] is True  # Business acceptance does not imply quality.


@pytest.mark.parametrize('captures,annotations,reason', [
    ([capture(),capture()], [annotation()], 'Duplicate capture run_id'),
    ([capture()], [annotation(),annotation()], 'Duplicate annotation run_id'),
    ([capture(owner='bob')], [annotation()], 'Capture owner mismatch'),
    ([capture()], [annotation(owner='bob')], 'Annotation owner mismatch'),
    ([capture()], [annotation(run='unknown')], 'Unknown annotation run_id'),
    ([capture()], [{**annotation(),'unexpected':'no'}], 'extra_forbidden'),
    ([capture()], [{key:value for key,value in annotation().items() if key != 'reviewer'}], 'reviewer'),
])
def test_annotation_rejects_ambiguous_or_unowned_labels(tmp_path,captures,annotations,reason):
    result, output = invoke(tmp_path,captures,annotations)
    assert result.returncode != 0
    assert reason in result.stderr
    assert 'ModuleNotFoundError' not in result.stderr
    assert not output.exists()


def test_annotation_requires_explicit_owner(tmp_path):
    result, output = invoke(tmp_path,[capture()],[annotation()], owner=None)
    assert result.returncode != 0 and '--owner-id' in result.stderr
    assert not output.exists()

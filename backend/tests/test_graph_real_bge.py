"""Opt-in real fixed BGE smoke/dev checks; not independent holdout acceptance.

Tester supplies CERES_REAL_BGE_INDEX pointing to a freshly built authorized index
and installs the fixed six-file model cache. All calls must run under offline guard.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3

import pytest

from app.core.config import ROOT_DIR
from app.knowledge import hybrid
from app.knowledge.corpus import manifest_revision

INDEX_PATH = os.environ.get('CERES_REAL_BGE_INDEX')
pytestmark = pytest.mark.skipif(not INDEX_PATH, reason='Tester must supply a fresh authorized real-BGE index')
# Exact bge.py SHA256 from d37b5e8, before the explicit six-file snapshot fix.
PRIOR_BGE_IMPLEMENTATION = 'f9b22bee892e61f9954365e3bdca6ebe376edff5eed9995f121797659d9e5654'


def test_real_bge_index_shape_and_three_namespaces():
    import numpy as np
    index = Path(INDEX_PATH)
    with sqlite3.connect(f'file:{index}?mode=ro', uri=True) as db:
        manifest = json.loads(db.execute('SELECT content FROM manifest').fetchone()[0])
        vectors = [np.frombuffer(row[0], dtype='<f4') for row in db.execute('SELECT embedding FROM documents')]
        samples = [json.loads(db.execute('SELECT document FROM documents WHERE namespace=? ORDER BY id LIMIT 1', (namespace,)).fetchone()[0])
                   for namespace in ('product', 'recipe', 'policy')]
    assert manifest['embedding_revision'] == '7999e1d3359715c523056ef9478215996d62a620'
    assert manifest['dimensions'] == 512
    assert all(vector.shape == (512,) and np.isclose(np.linalg.norm(vector), 1, atol=1e-5) for vector in vectors)
    for document in samples:
        result = hybrid.search(index, document['title'], document['namespace'], limit=5,
            allowed_ids=[document['id']], expected_index_revision=manifest_revision(manifest))
        assert [hit['id'] for hit in result['hits']] == [document['id']]
        assert result['hits'][0]['ranks']['dense'] == 1
        assert result['hits'][0]['ranks']['sparse'] == 1
        assert result['manifest']['implementation']['bge.py'] != PRIOR_BGE_IMPLEMENTATION


def test_real_bge_rejects_planted_prior_implementation_before_encoding(tmp_path, monkeypatch):
    # This is a copy of the newly built index with a planted historical fingerprint,
    # not a claim that a prior-version real index ever built successfully.
    index = tmp_path / 'prior-fingerprint.sqlite3'
    shutil.copyfile(INDEX_PATH, index)
    with sqlite3.connect(index) as db:
        manifest = json.loads(db.execute('SELECT content FROM manifest').fetchone()[0])
        manifest['implementation']['bge.py'] = PRIOR_BGE_IMPLEMENTATION
        db.execute('UPDATE manifest SET content=?', (json.dumps(manifest),))
    monkeypatch.setattr(hybrid, 'encoder', lambda: pytest.fail('Stale index reached the encoder'))
    with pytest.raises(hybrid.StaleIndexError, match='implementation'):
        hybrid.search(index, '番茄炒蛋', 'recipe')


def test_real_bge_public_dev_relevance_and_rrf(tmp_path):
    source = ROOT_DIR / 'evals/ceres2-optimization-retrieval-dev.json'
    evaluation = json.loads(source.read_text())
    rows, failures = [], []
    for case in evaluation['cases']:
        result = hybrid.search(Path(INDEX_PATH), case['query'], case['namespace'], limit=1000)
        hits = [item['id'] for item in result['hits']]
        for item in result['candidates']:
            expected = sum(1 / (hybrid.RRF_K + rank) for rank in item['ranks'].values())
            assert math.isclose(item['rrf_score'], expected, rel_tol=0, abs_tol=1e-15)
        targets = case['target_ids']
        passed = (all(identity in hits[:3] for identity in targets) if targets else not hits)
        excluded = sorted(set(case.get('excluded_ids', [])) & set(hits))
        if not passed or excluded:
            failures.append(case['id'])
        rows.append({'case_id': case['id'], 'hits': hits, 'target_ids': targets,
                     'excluded_hits': excluded, 'passed': passed and not excluded,
                     'dense': result['dense'], 'sparse': result['sparse']})
    report = {'purpose': evaluation['purpose'], 'eval_version': evaluation['version'],
              'eval_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'index_manifest': result['manifest'], 'cases': rows, 'failed_cases': failures}
    (tmp_path / 'real-bge-public-dev-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    assert not failures, report


def test_real_bge_cold_and_same_worker_query_deadlines(tmp_path, monkeypatch):
    import subprocess
    import sys
    import time
    from app.core.errors import AppError
    from app.services import knowledge_service
    original = subprocess.Popen
    def launch(command, **kwargs):
        kwargs['cwd'] = ROOT_DIR / 'backend'
        return original([sys.executable, '-m', 'app.knowledge.cli', 'serve',
                         '--index', str(INDEX_PATH)], **kwargs)
    monkeypatch.setattr(knowledge_service, 'ROOT_DIR', tmp_path)
    monkeypatch.setattr(knowledge_service.subprocess, 'Popen', launch)
    service = knowledge_service.KnowledgeService()
    observations = []
    try:
        for label, query in [('cold_start', '番茄炒蛋'), ('same_worker_second_query', '蛋炒饭')]:
            started = time.monotonic()
            try:
                result = service.search(query, 'recipe', deadline=started + 15, should_stop=lambda: False)
                observation = {'phase': label, 'wall_seconds': time.monotonic()-started,
                    'status': 'success', 'worker_pid': service.child.pid,
                    'hit_ids': [hit['id'] for hit in result['hits']]}
            except AppError as error:
                observation = {'phase': label, 'wall_seconds': time.monotonic()-started,
                               'status': error.detail['error']['code'], 'worker_pid': None}
            observations.append(observation)
            if observation['status'] != 'success':
                break
    finally:
        service.close()
        (tmp_path / 'real-bge-cold-warm-deadlines.json').write_text(json.dumps({
            'request_budget_seconds': 15, 'no_pre_warm': True, 'observations': observations}, indent=2))
    assert len(observations) == 2 and all(row['status'] == 'success' for row in observations), observations
    assert observations[0]['worker_pid'] == observations[1]['worker_pid']
    assert all(row['wall_seconds'] < 15 and row['hit_ids'] for row in observations)

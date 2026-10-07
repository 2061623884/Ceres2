"""Versioned policy evidence at the public retrieval boundary, offline only."""
import json
import sqlite3
from types import SimpleNamespace

import pytest

from app.core.errors import AppError
from app.mercury import policy


def test_policy_source_rejects_index_built_from_different_fixture(tmp_path, monkeypatch):
    fixtures = tmp_path / 'data' / 'fixtures'
    fixtures.mkdir(parents=True)
    for name in ('products.json', 'recipes.json', 'ingredients.json', 'knowledge-provenance.json'):
        (fixtures / name).write_text('{}')
    (fixtures / 'policies.json').write_text(json.dumps({
        'version': 'controlled-v2', 'source_name': 'Controlled policy source', 'policies': []}))
    indexes = tmp_path / 'data' / 'indexes'
    indexes.mkdir()
    with sqlite3.connect(indexes / 'hybrid.sqlite3') as db:
        db.execute('CREATE TABLE manifest (content TEXT)')
        db.execute('INSERT INTO manifest VALUES (?)', (json.dumps({
            'files': {'policies.json': 'older-policy-fixture-hash'},
        }),))
    monkeypatch.setattr(policy, 'get_settings', lambda: SimpleNamespace(root_dir=tmp_path), raising=False)

    with pytest.raises(AppError) as failure:
        policy.source_snapshot()

    assert failure.value.detail['error']['code'] == 'KNOWLEDGE_STALE'


def test_policy_source_rejects_wrong_model_revision_even_when_fixture_bytes_match(tmp_path, monkeypatch):
    import hashlib
    fixtures = tmp_path / 'data' / 'fixtures'
    fixtures.mkdir(parents=True)
    names = ('products.json', 'recipes.json', 'ingredients.json', 'knowledge-provenance.json')
    for name in names:
        (fixtures / name).write_text('{}')
    (fixtures / 'policies.json').write_text(json.dumps({
        'version': 'controlled-v2', 'source_name': 'Controlled policy source', 'policies': []}))
    manifest = {'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in fixtures.iterdir()},
                'corpus_revision': 'ceres-knowledge-v1', 'embedding_model': 'BAAI/bge-small-zh-v1.5',
                'embedding_revision': 'different-embedding-revision', 'dimensions': 512,
                'tokenizer_revision': 'zh-unigrams-bigrams-ascii-v2',
                'relevance_revision': 'retrieval-dev-v2-literal-or-dense'}
    indexes = tmp_path / 'data' / 'indexes'
    indexes.mkdir()
    with sqlite3.connect(indexes / 'hybrid.sqlite3') as db:
        db.execute('CREATE TABLE manifest (content TEXT)')
        db.execute('INSERT INTO manifest VALUES (?)', (json.dumps(manifest),))
    monkeypatch.setattr(policy, 'get_settings', lambda: SimpleNamespace(root_dir=tmp_path))

    with pytest.raises(AppError) as failure:
        policy.source_snapshot()

    assert failure.value.detail['error']['code'] == 'KNOWLEDGE_STALE'

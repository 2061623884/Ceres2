"""Controlled graph contracts, distinct from actual GraphRAG/BGE model execution."""
import asyncio
import hashlib
import json
from pathlib import Path
import shutil
import time
from types import SimpleNamespace

import pytest

from app.core.config import ROOT_DIR
from app.knowledge import graph_manifest
from app.knowledge.corpus import manifest_revision


@pytest.fixture
def controlled_graph(tmp_path, monkeypatch):
    # Artifact bytes are intentionally opaque: this suite verifies identity, not Parquet execution.
    fixtures = tmp_path / 'fixtures'
    shutil.copytree(ROOT_DIR / 'data/fixtures', fixtures)
    root = tmp_path / 'graph'
    (root / 'output/lancedb').mkdir(parents=True)
    (root / 'prompts').mkdir()
    for name in ('entities', 'relationships', 'text_units', 'communities', 'community_reports'):
        (root / f'output/{name}.parquet').write_bytes(name.encode())
    (root / 'output/lancedb/vector.bin').write_bytes(b'controlled-vector')
    (root / 'prompts/community_report.txt').write_text('controlled-prompt')
    monkeypatch.setattr(graph_manifest, 'version', lambda name: '3.2.0')
    manifest = {**graph_manifest.source_identity(fixtures), 'artifacts': graph_manifest.artifact_identity(root)}
    (root / 'manifest.json').write_text(json.dumps(manifest))
    return root, fixtures, manifest


def test_graph_manifest_rejects_source_model_prompt_and_artifact_changes(controlled_graph, monkeypatch):
    root, fixtures, manifest = controlled_graph
    assert graph_manifest.validate_graph(root, fixtures) == manifest
    for key, value in [('graph_revision', 'old'), ('embedding_revision', 'old'),
                       ('completion_model', 'different'), ('provider_host', 'different'),
                       ('graph_implementation', {}), ('files', {})]:
        changed = {**manifest, key: value}
        (root / 'manifest.json').write_text(json.dumps(changed))
        with pytest.raises(graph_manifest.GraphStaleError):
            graph_manifest.validate_graph(root, fixtures)
    (root / 'manifest.json').write_text(json.dumps(manifest))
    (root / 'prompts/community_report.txt').write_text('changed-prompt')
    with pytest.raises(graph_manifest.GraphStaleError):
        graph_manifest.validate_graph(root, fixtures)


def test_actual_fixture_and_vector_mutation_invalidate_graph(controlled_graph):
    root, fixtures, _ = controlled_graph
    source = fixtures / 'recipes.json'
    original = source.read_bytes()
    source.write_bytes(original + b'\n')
    with pytest.raises(graph_manifest.GraphStaleError):
        graph_manifest.validate_graph(root, fixtures)
    source.write_bytes(original)
    (root / 'output/lancedb/vector.bin').write_bytes(b'changed')
    with pytest.raises(graph_manifest.GraphStaleError):
        graph_manifest.validate_graph(root, fixtures)


def test_expected_build_revision_rejected_before_metadata_dependencies(controlled_graph, monkeypatch):
    root, fixtures, _ = controlled_graph
    monkeypatch.setattr(graph_manifest, 'source_identity', lambda *_: pytest.fail('Unexpected source work'))
    with pytest.raises(graph_manifest.GraphStaleError):
        graph_manifest.validate_graph(root, fixtures, 'different')


@pytest.mark.parametrize('method', ['local', 'global'])
def test_query_scope_does_not_carry_calls_between_queries(controlled_graph, monkeypatch, method):
    from app.knowledge import graph
    from app.knowledge.graph_context import current_operation
    root, fixtures, manifest = controlled_graph
    async def controlled_search(root, query, method):
        row = current_operation().begin_call('completion', 'controlled')
        row.update(status='success')
        return {'selection': {'entity_numbers': [1]}, 'canonical_facts': [], 'manifest': manifest}
    monkeypatch.setattr(graph, '_search', controlled_search)
    for identity in ('first', 'second'):
        result = asyncio.run(graph.search(root, '鸡蛋', method, fixtures=fixtures,
            deadline=time.monotonic() + 1, graph_query_id=identity))
        assert result['graph_status'] == 'success'
        assert result['call_counts'] == {'completion': 1, 'embedding': 0}
        assert len(result['calls']) == 1
        assert result['calls'][0]['graph_query_id'] == identity
        assert result['calls'][0]['usage'] is None
        assert result['calls'][0]['cost'] is None
        assert result['graph_index_revision'] == manifest_revision(manifest)


def test_query_observations_are_bounded_but_counts_are_complete():
    from app.knowledge.graph_context import operation, current_operation
    with operation('one-query', time.monotonic() + 1) as active:
        for _ in range(100):
            active.begin_call('completion', 'controlled')
        observations = active.observations()
        assert len(observations['calls']) == 64
        assert observations['call_counts']['completion'] == 100
        assert observations['calls_truncated'] is True
    with pytest.raises(RuntimeError):
        current_operation()


def test_query_deadline_and_stale_index_do_not_invoke_graph(controlled_graph, monkeypatch):
    from app.knowledge import graph
    root, fixtures, manifest = controlled_graph
    async def forbidden(*args):
        pytest.fail('Graph invoked after expiry or against stale evidence')
    monkeypatch.setattr(graph, '_search', forbidden)
    expired = asyncio.run(graph.search(root, '鸡蛋', 'local', fixtures=fixtures,
        deadline=time.monotonic() - 1, graph_query_id='expired'))
    assert expired['error'] == 'KNOWLEDGE_TIMEOUT'
    assert expired['graph_status'] == 'not_executed'
    manifest['embedding_revision'] = 'stale'
    (root / 'manifest.json').write_text(json.dumps(manifest))
    stale = asyncio.run(graph.search(root, '鸡蛋', 'local', fixtures=fixtures,
        deadline=time.monotonic() + 1, graph_query_id='stale'))
    assert stale['error'] == 'KNOWLEDGE_STALE'
    assert stale['call_counts']['completion'] == 0


def test_provider_timeout_has_no_success_evidence(controlled_graph, monkeypatch):
    from app.knowledge import graph
    root, fixtures, _ = controlled_graph
    async def slow(*args):
        await asyncio.sleep(1)
        pytest.fail('Timeout allowed a late result')
    monkeypatch.setattr(graph, '_search', slow)
    result = asyncio.run(graph.search(root, '鸡蛋', 'local', fixtures=fixtures,
        deadline=time.monotonic() + .05, graph_query_id='slow'))
    assert result['error'] == 'KNOWLEDGE_TIMEOUT'
    assert result['graph_status'] == 'error'
    assert 'canonical_facts' not in result


def test_dish_graph_uses_current_canonical_records_and_same_budget(monkeypatch):
    from app.services.dish_service import DishService, recipes
    from app.services.knowledge_service import knowledge
    dish = recipes()[0]
    files = {name: hashlib.sha256((ROOT_DIR / 'data/fixtures' / name).read_bytes()).hexdigest()
             for name in graph_manifest.FIXTURE_NAMES}
    returned = {'manifest': {'files': files}, 'canonical_facts': [
        {'id': 'recipe:' + dish['dish_id'], 'type': 'RECIPE', 'description': 'invented amount'}]}
    deadline, stop = time.monotonic() + 1, lambda: False
    def query(text, **kwargs):
        assert kwargs['deadline'] == deadline and kwargs['should_stop'] is stop
        assert kwargs['method'] == 'global'
        return returned
    monkeypatch.setattr(knowledge, 'graph', query)
    service = DishService(SimpleNamespace(deadline=deadline, should_stop=stop))
    matches, evidence = service.graph_search('鸡蛋', method='global')
    assert matches == [dish]
    assert evidence is returned
    # Ordinary deterministic lookup remains graph-free.
    monkeypatch.setattr(knowledge, 'graph', lambda *a, **k: pytest.fail('Implicit graph query'))
    assert dish in service.search(dish['name'])


def selection_records():
    entities = [
        {'id': 'recipe:a', 'human_readable_id': 1, 'type': 'RECIPE', 'title': 'Dish A', 'description': 'Canonical dish: 2 people; egg 2pc'},
        {'id': 'ingredient:egg', 'human_readable_id': 2, 'type': 'INGREDIENT', 'title': 'Egg', 'description': 'Canonical ingredient; no allergy guarantee'},
        {'id': 'recipe:outside', 'human_readable_id': 3, 'type': 'RECIPE', 'title': 'Outside', 'description': 'Excluded context'}]
    edges = [{'id': 'edge:a', 'human_readable_id': 0, 'source': 'Dish A', 'target': 'Egg',
              'description': 'REQUIRES: egg 2pc; not a shopping authorization'}]
    return entities, edges, {'recipe:a', 'ingredient:egg'}


def test_local_selection_and_global_canonical_expansion_are_distinct():
    from app.knowledge.graph import project_selection
    entities, edges, scope = selection_records()
    local = project_selection(entities, edges, scope, '{"entity_numbers":[1]}', 'local', 'NO_DATA')
    global_result = project_selection(entities, edges, scope, '{"entity_numbers":[1]}', 'global', 'NO_DATA')
    assert local['model_selected_entity_ids'] == global_result['model_selected_entity_ids'] == ['recipe:a']
    assert [row['id'] for row in local['canonical_facts']] == ['recipe:a']
    assert [row['id'] for row in global_result['canonical_facts']] == ['recipe:a', 'ingredient:egg']
    assert global_result['canonical_scope'] == 'retrieved_communities'
    assert global_result['ingredient_recipes']['ingredient:egg']['recipes'][0]['recipe_id'] == 'recipe:a'
    assert 'Excluded context' not in global_result['answer']


@pytest.mark.parametrize('answer', ['{"entity_numbers":[3]}', '{"entity_numbers":[true]}',
                                    '{"entity_numbers":["1"]}', '{"entity_numbers":[1],"facts":"invented"}'])
def test_invalid_or_outside_model_selection_never_becomes_facts(answer):
    from app.knowledge.graph import project_selection
    with pytest.raises(ValueError):
        project_selection(*selection_records(), answer, 'global', 'NO_DATA')


@pytest.mark.parametrize('answer', ['{"entity_numbers":[]}', 'NO_DATA'])
def test_global_empty_selection_is_not_expanded(answer):
    from app.knowledge.graph import project_selection
    result = project_selection(*selection_records(), answer, 'global', 'NO_DATA')
    assert result['canonical_facts'] == []
    assert result['model_selected_entity_ids'] == []


def test_graph_cancelled_parent_keeps_unknown_provider_usage(monkeypatch):
    from app.services.knowledge_service import KnowledgeService
    from app.core.errors import AppError
    service = KnowledgeService()
    with pytest.raises(AppError) as failure:
        service.graph('cancel', deadline=time.monotonic() + 1, should_stop=lambda: True)
    observation = failure.value.detail['graph_observation']
    assert observation['graph_status'] == 'unobserved'
    assert observation['call_counts'] is None
    assert observation['official_graph_calls'] is None
    assert observation['error'] == 'KNOWLEDGE_CANCELLED'


def test_bge_loader_requests_only_fixed_local_snapshot_files(monkeypatch, tmp_path):
    import sys
    from app.knowledge import bge
    capture = {}
    def snapshot(model, **kwargs):
        capture.update(model=model, **kwargs)
        return str(tmp_path)
    class Model:
        def to(self, device):
            assert device == 'cpu'
            return self
        def eval(self):
            return self
    def pretrained(path, **kwargs):
        assert path == str(tmp_path)
        assert kwargs['local_files_only'] is True
        assert kwargs['trust_remote_code'] is False
        return Model()
    monkeypatch.setitem(sys.modules, 'huggingface_hub', SimpleNamespace(snapshot_download=snapshot))
    monkeypatch.setitem(sys.modules, 'transformers', SimpleNamespace(
        AutoModel=SimpleNamespace(from_pretrained=pretrained),
        AutoTokenizer=SimpleNamespace(from_pretrained=pretrained)))
    bge.BgeEncoder()
    assert capture['revision'] == '7999e1d3359715c523056ef9478215996d62a620'
    assert capture['local_files_only'] is True and capture['token'] is False
    assert set(capture['allow_patterns']) == {'config.json', 'model.safetensors', 'tokenizer.json',
        'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt'}

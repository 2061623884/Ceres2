"""Official GraphRAG library, controlled transport and no-weight embedding seam.

Passing this suite is library/adapter evidence, not real model or BGE evidence.
"""
import asyncio
import hashlib
import json
import time
from types import SimpleNamespace

import pytest

pytest.importorskip('graphrag', reason='Official locked GraphRAG environment required')
pytest.importorskip('graphrag_llm', reason='Official locked provider interfaces required')
import httpx
import numpy as np
from openai import OpenAI, AsyncOpenAI
from app.core.config import ROOT_DIR
from app.knowledge import providers
from app.knowledge.graph_context import operation


@pytest.fixture
def controlled_provider(monkeypatch):
    requests = []
    def handle(request):
        body = json.loads(request.content)
        requests.append({'url': str(request.url), 'body': body})
        prompt = '\n'.join(message['content'] for message in body['messages'])
        if '"rating_explanation"' in prompt and '"findings"' in prompt:
            content = json.dumps({'title': 'Controlled recipe community',
                'summary': 'Canonical recipe and ingredient records only.', 'rating': 1.0,
                'rating_explanation': 'Controlled adapter fixture.',
                'findings': [{'summary': 'Recipe facts', 'explanation': 'Use original recipe witnesses. [Data: Entities (0)]'}]})
        elif not body.get('stream'):
            content = json.dumps({'points': [{'description': 'Recipe facts are in the provided canonical witnesses. [Data: Entities (0)]', 'score': 90}]})
        else:
            # Empty selection is a legitimate fixed model reply. Projection semantics
            # have separate strict-reference tests, so this never invents an entity ID.
            content = '{"entity_numbers":[]}'
        base = {'id': 'controlled-response', 'created': 1, 'model': body['model']}
        if body.get('stream'):
            chunks = [dict(base, object='chat.completion.chunk', choices=[{'index': 0,
                'delta': {'role': 'assistant', 'content': content}, 'finish_reason': None}]),
                dict(base, object='chat.completion.chunk', choices=[{'index': 0, 'delta': {}, 'finish_reason': 'stop'}],
                     usage={'prompt_tokens': 7, 'completion_tokens': 3, 'total_tokens': 10})]
            data = ''.join('data: ' + json.dumps(chunk) + '\n\n' for chunk in chunks) + 'data: [DONE]\n\n'
            return httpx.Response(200, headers={'content-type': 'text/event-stream'}, content=data)
        return httpx.Response(200, json=dict(base, object='chat.completion',
            choices=[{'index': 0, 'message': {'role': 'assistant', 'content': content}, 'finish_reason': 'stop'}],
            usage={'prompt_tokens': 7, 'completion_tokens': 3, 'total_tokens': 10}))
    monkeypatch.setattr(providers, 'OpenAI', lambda **kw: OpenAI(**kw, http_client=httpx.Client(transport=httpx.MockTransport(handle))))
    monkeypatch.setattr(providers, 'AsyncOpenAI', lambda **kw: AsyncOpenAI(**kw, http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle))))
    return requests


@pytest.mark.parametrize('hostname,official', [('https://api.deepseek.com', True),
    ('https://API.DEEPSEEK.COM/v1', True), ('https://api.deepseek.com.evil.invalid/v1', False),
    ('https://other.invalid/v1', False)])
def test_official_provider_wire_thinking_and_unknown_usage(controlled_provider, hostname, official):
    client = providers.JsonModeCompletion(model_config=SimpleNamespace(api_key='offline-fixture-key',
        api_base=hostname, model='controlled-test', call_args={}), tokenizer=None, metrics_store=None)
    deadline = time.monotonic() + 15
    with operation('wire', deadline) as active:
        request, _ = client._request({'messages': 'Controlled wire'})
        assert 0 < request['timeout'] <= 15
        client.completion(messages='Controlled wire')
        row = active.observations()['calls'][0]
        assert row['usage']['total_tokens'] == 10
        assert row['cost'] is None
        assert row['graph_query_id'] == 'wire'
    body = controlled_provider[0]['body']
    if official:
        assert body['thinking'] == {'type': 'disabled'}
    else:
        assert 'thinking' not in body


@pytest.fixture
def no_weight_encoder(monkeypatch):
    class Encoder:
        def tokenizer(self, text, **kwargs):
            return {'input_ids': list(range(min(len(text), 512)))}
        def encode(self, texts):
            rows = []
            for text in texts:
                raw = hashlib.sha256(text.encode()).digest()
                row = np.resize(np.frombuffer(raw, dtype=np.uint8).astype(np.float32) + 1, 512)
                rows.append(row / np.linalg.norm(row))
            return np.asarray(rows, dtype=np.float32)
    monkeypatch.setattr(providers, 'encoder', lambda: Encoder())


def test_real_official_byog_build_and_local_global_query(tmp_path, monkeypatch, controlled_provider, no_weight_encoder):
    from app.knowledge import graph
    fixtures = tmp_path / 'fixtures'
    fixtures.mkdir()
    from app.knowledge.corpus import FIXTURE_NAMES
    for name in FIXTURE_NAMES:
        (fixtures / name).write_bytes((ROOT_DIR / 'data/fixtures' / name).read_bytes())
    recipes = json.loads((fixtures / 'recipes.json').read_text())
    recipes['dishes'] = recipes['dishes'][:2]
    # Exercise optional record shape only in this temporary controlled source.
    recipes['dishes'][0]['optional_items'] = [{'ingredient_id': 'scallion'}]
    (fixtures / 'recipes.json').write_text(json.dumps(recipes))
    products = json.loads((fixtures / 'products.json').read_text())
    products['products'] = products['products'][:8]
    (fixtures / 'products.json').write_text(json.dumps(products))
    root = tmp_path / 'index'
    root.mkdir()
    # Explicit offline indexing test budget; Guide/query budget remains 15 seconds.
    manifest = asyncio.run(graph.build(fixtures, root, deadline=time.monotonic() + 120))
    assert manifest['graphrag'] == '3.2.0'
    assert manifest['call_counts']['completion'] > 0
    assert manifest['call_counts']['embedding'] > 0
    import pandas as pd
    entities = pd.read_parquet(root / 'output/entities.parquet')
    recipe_text = entities.loc[entities['type'] == 'RECIPE', 'description'].tolist()
    assert any('数量未知' in text for text in recipe_text)
    for method in ('local', 'global'):
        result = asyncio.run(graph.search(root, '有哪些菜谱食材关系？', method,
            fixtures=fixtures, deadline=time.monotonic() + 15, graph_query_id=method))
        assert result.get('error') is None, result
        assert result['graph_status'] == 'success'
        assert result['official_graph_calls'] == 1
        assert result['canonical_facts'] == []
        assert result['call_counts']['completion'] > 0
        assert all(row['graph_query_id'] == method for row in result['calls'])
    assert controlled_provider
    assert all(row['url'].startswith('http://127.0.0.1:9/') for row in controlled_provider)

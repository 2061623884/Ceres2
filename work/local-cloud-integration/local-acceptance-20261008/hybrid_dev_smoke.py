"""Small public-fixture smoke for the current fresh BGE/BM25/RRF index."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'backend'))

from app.knowledge.bge import MODEL_REVISION
from app.knowledge.corpus import manifest_revision
from app.knowledge.hybrid import search


CASES = [
    ('recipe', '番茄炒蛋'),
    ('product', '可口可乐'),
    ('policy', '未发货取消订单'),
]


def lane(rows):
    return [{'id': item[0], 'score': item[1]} for item in rows[:3]]


def main():
    index = ROOT / 'data/indexes/hybrid.sqlite3'
    output = []
    for namespace, query in CASES:
        result = search(index, query, namespace, limit=10, fixtures=ROOT / 'data/fixtures')
        assert result['manifest']['embedding_revision'] == MODEL_REVISION
        assert result['dense'], (namespace, query, 'empty dense lane')
        assert result['candidates'], (namespace, query, 'empty RRF candidates')
        output.append({
            'namespace': namespace,
            'query': query,
            'manifest_revision': manifest_revision(result['manifest']),
            'dense_top3': lane(result['dense']),
            'bm25_top3': lane(result['sparse']),
            'rrf_top3': [{
                'id': item['id'], 'rrf_score': item['rrf_score'],
                'ranks': item['ranks'], 'scores': item['scores'],
            } for item in result['candidates'][:3]],
            'relevance_floor': result['relevance_floor'],
            'hits_top3': [{
                'id': item['id'], 'rrf_score': item['rrf_score'],
                'ranks': item['ranks'], 'scores': item['scores'],
            } for item in result['hits'][:3]],
        })
    print(json.dumps({'model_revision': MODEL_REVISION, 'cases': output}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

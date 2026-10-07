"""Independent Chinese BM25 and real BGE recall, fused by reciprocal rank."""
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from app.knowledge.bge import DIMENSIONS, MODEL_ID, MODEL_REVISION, ROOT, encoder
from app.knowledge.corpus import load_corpus

RRF_K = 60
TOKENIZER_REVISION = 'zh-unigrams-bigrams-ascii-v2'
# Frozen development calibration: positive minima exceed these floors; known
# absent-item/unknown-policy maxima fall below. This is relevance, not eligibility.
RELEVANCE_REVISION = 'retrieval-dev-v2-literal-or-dense'
RELEVANCE_FLOORS = {'recipe': 0.54, 'product': 0.56, 'policy': 0.50}


def tokens(text: str) -> list[str]:
    rows = []
    for word in re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9_]+', text.lower()):
        if re.fullmatch(r'[\u4e00-\u9fff]+', word) and len(word) > 1:
            rows.extend(word)
            rows.extend(word[i:i+2] for i in range(len(word)-1))
        else:
            rows.append(word)
    return rows


def build(fixtures: Path, index: Path) -> dict:
    documents, manifest = load_corpus(fixtures)
    vectors = encoder().encode([f"{d['title']} {d['text']}" for d in documents])
    manifest.update({'embedding_model': MODEL_ID, 'embedding_revision': MODEL_REVISION,
        'dimensions': DIMENSIONS, 'pooling': 'normalized-cls', 'query_instruction': '',
        'tokenizer_revision': TOKENIZER_REVISION, 'rrf_k': RRF_K,
        'relevance_revision': RELEVANCE_REVISION, 'relevance_floors': RELEVANCE_FLOORS,
        'calibration_sha256': hashlib.sha256((ROOT/'evals/ceres2-optimization-retrieval-dev.json').read_bytes()).hexdigest()})
    index.parent.mkdir(parents=True, exist_ok=True)
    temporary = index.with_suffix('.building')
    temporary.unlink(missing_ok=True)
    with sqlite3.connect(temporary) as db:
        db.execute('CREATE TABLE documents (id TEXT PRIMARY KEY, namespace TEXT, document TEXT, embedding BLOB)')
        db.execute('CREATE VIRTUAL TABLE documents_fts USING fts5(id UNINDEXED, namespace UNINDEXED, title_tokens, text_tokens)')
        db.execute('CREATE TABLE manifest (content TEXT)')
        db.executemany('INSERT INTO documents VALUES (?, ?, ?, ?)', [(d['id'], d['namespace'], json.dumps(d, ensure_ascii=False), vectors[i].tobytes()) for i, d in enumerate(documents)])
        db.executemany('INSERT INTO documents_fts VALUES (?, ?, ?, ?)', [(d['id'], d['namespace'], ' '.join(tokens(d['title'])), ' '.join(tokens(d['text']))) for d in documents])
        db.execute('INSERT INTO manifest VALUES (?)', (json.dumps(manifest, ensure_ascii=False),))
    temporary.replace(index)
    return manifest


def search(index: Path, query: str, namespace: str, limit: int = 10, *, allowed_ids: list[str] | None = None, category: str | None = None) -> dict:
    import numpy as np
    with sqlite3.connect(f'file:{index}?mode=ro', uri=True) as db:
        manifest = json.loads(db.execute('SELECT content FROM manifest').fetchone()[0])
        raw = db.execute('SELECT id, document, embedding FROM documents WHERE namespace = ? ORDER BY id', (namespace,)).fetchall()
        allowed = set(allowed_ids) if allowed_ids is not None else None
        rows = [(identity, json.loads(document), vector) for identity, document, vector in raw
            if (allowed is None or identity in allowed)]
        if category is not None:
            rows = [row for row in rows if row[1]['category'] == category]
        eligible = {row[0] for row in rows}
        query_tokens = list(dict.fromkeys(tokens(query)))
        sparse = []
        if query_tokens:
            expression = ' OR '.join(f'"{token}"' for token in query_tokens)
            sparse = [(identity, float(score)) for identity, score in db.execute(
                'SELECT id, bm25(documents_fts, 0, 0, 3, 1) FROM documents_fts WHERE documents_fts MATCH ? AND namespace = ? ORDER BY 2, id', (expression, namespace)) if identity in eligible][:limit]
        dense = []
        cosine_by_id = {}
        if rows:
            query_vector = encoder().encode([query])[0]
            vectors = np.stack([np.frombuffer(row[2], dtype='<f4') for row in rows])
            scores = vectors @ query_vector
            cosine_by_id = {row[0]: float(scores[i]) for i, row in enumerate(rows)}
            dense = sorted([(row[0], float(scores[i])) for i, row in enumerate(rows)], key=lambda row: (-row[1], row[0]))[:limit]
    fused = {}
    for lane, ranked in (('sparse', sparse), ('dense', dense)):
        for rank, (identity, score) in enumerate(ranked, 1):
            item = fused.setdefault(identity, {'id': identity, 'rrf_score': 0.0, 'ranks': {}, 'scores': {}})
            item['rrf_score'] += 1 / (RRF_K + rank)
            item['ranks'][lane], item['scores'][lane] = rank, score
    documents = {row[0]: row[1] for row in rows}
    ranked = sorted(fused.values(), key=lambda item: (-item['rrf_score'], item['id']))
    candidates = [{**item, 'document': documents[item['id']]} for item in ranked[:limit]]
    # A literal source match is independent lexical relevance, including the
    # existing one-character recipe queries. Dense-only evidence needs its
    # calibrated floor; semantic scores must not erase exact lexical evidence.
    hits = [{**item, 'document': documents[item['id']]} for item in ranked
        if cosine_by_id[item['id']] >= RELEVANCE_FLOORS[namespace]
        or (query_tokens and query.lower() in (documents[item['id']]['title']+' '+documents[item['id']]['text']).lower())][:limit]
    return {'query': query, 'namespace': namespace, 'sparse': sparse, 'dense': dense,
        'candidates': candidates, 'hits': hits, 'relevance_floor': RELEVANCE_FLOORS[namespace], 'manifest': manifest}

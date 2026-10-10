"""Versioned hybrid policy evidence; no order qualification or mutation authority."""
import json
import sqlite3
from app.core.config import get_settings
from app.core.errors import AppError
from app.knowledge.corpus import manifest_revision


def source_snapshot():
    root = get_settings().root_dir
    names = ("products.json", "recipes.json", "ingredients.json", "policies.json", "knowledge-provenance.json")
    try:
        files = {name: (root / "data/fixtures" / name).read_bytes() for name in names}
        # A busy/missing index is unavailable; never spend another DB wait budget.
        with sqlite3.connect(f"file:{root / 'data/indexes/hybrid.sqlite3'}?mode=ro", uri=True, timeout=0) as db:
            manifest = json.loads(db.execute("SELECT content FROM manifest").fetchone()[0])
        corpus = json.loads(files["policies.json"])
        source = {"source_name": corpus["source_name"], "source_version": corpus["version"]}
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError) as exc:
        raise AppError(503, "KNOWLEDGE_UNAVAILABLE", "政策来源或索引不可用，请检查本地检索构建记录") from exc
    from app.knowledge.hybrid import validate_manifest, StaleIndexError
    try:
        validate_manifest(manifest, files)
    except StaleIndexError as exc:
        raise AppError(503, 'KNOWLEDGE_STALE', '知识索引与当前来源或检索实现版本不一致，请重新构建索引') from exc
    return {**source,
            "source_revision": manifest["files"]["policies.json"],
            "index_revision": manifest_revision(manifest)}


CATEGORIES = ('price', 'stock', 'delivery', 'order', 'refund', 'fulfillment', 'quality', 'return', 'safety', 'human')


def search_policies(query, category=None, *, snapshot=None, deadline=None, should_stop=None):
    import time
    from app.services.knowledge_service import knowledge, check_budget
    if deadline is None:
        deadline = time.monotonic() + 30
    check_budget(deadline, should_stop)
    acquired = source_snapshot()
    if snapshot is not None and snapshot != acquired:
        raise AppError(503, 'KNOWLEDGE_STALE', '政策来源已变化，请重新查询')
    retrieval = knowledge.search(query, 'policy', limit=3, category=category,
                                 deadline=deadline, should_stop=should_stop,
                                 expected_index_revision=acquired['index_revision'])
    revision = manifest_revision(retrieval['manifest'])
    if revision != acquired['index_revision'] or source_snapshot() != acquired:
        raise AppError(503, 'KNOWLEDGE_STALE', '政策来源与检索快照不一致，请重新查询')
    check_budget(deadline, should_stop)
    data = []
    for hit in retrieval['hits']:
        document = hit['document']
        data.append({'policy_id': document['id'], 'category': document['category'],
                     'title': document['title'], 'content': document['text'],
                     'source': {'name': document['source']['name'],
                                'version': document['source']['version'], 'policy_id': document['id']}})
    return {'ok': True, 'data': data, **acquired, 'retrieval': retrieval}


def policy_summary(data):
    if not data:
        return '未找到匹配的售后政策，规则未知，无法据此判断资格；未提交任何申请。'
    facts = '；'.join(
        f"{item['title']}：{item['content']} 来源：{item['source']['name']} "
        f"{item['source']['policy_id']}（版本 {item['source']['version']}）"
        for item in data)
    return facts + '；以上是一般政策，具体订单资格尚未核实；未提交任何申请。'

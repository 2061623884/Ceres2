"""Shared policy hybrid retrieval; no order qualification or application writes."""
import json
from app.core.config import get_settings

CATEGORIES = ('price', 'stock', 'delivery', 'order', 'refund', 'fulfillment', 'quality', 'return', 'safety', 'human')


def search_policies(query, category=None):
    from app.services.knowledge_service import knowledge
    retrieval = knowledge.search(query, 'policy', limit=3, category=category)
    corpus = json.loads((get_settings().root_dir/'data/fixtures/policies.json').read_text())
    records = {row['policy_id']: row for row in corpus['policies']}
    return {'ok': True, 'data': [{**records[hit['id']],
        'source': {'name': corpus['source_name'], 'version': corpus['version'], 'policy_id': hit['id']}}
        for hit in retrieval['hits']], 'retrieval': retrieval}


def policy_summary(data):
    if not data:
        return '未找到匹配的售后政策，规则未知，无法据此判断资格；未提交任何申请。'
    facts = '；'.join(
        f"{item['title']}：{item['content']} 来源：{item['source']['name']} "
        f"{item['source']['policy_id']}（版本 {item['source']['version']}）"
        for item in data)
    return facts + '；以上是一般政策，具体订单资格尚未核实；未提交任何申请。'

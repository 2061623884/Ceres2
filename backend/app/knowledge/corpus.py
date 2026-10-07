"""Build retrieval documents from the tracked demo facts, never runtime orders."""
import hashlib
import json
from pathlib import Path

CORPUS_REVISION = 'ceres-knowledge-v1'
FIXTURE_NAMES = ('products.json', 'recipes.json', 'ingredients.json', 'policies.json', 'knowledge-provenance.json')


def load_corpus(fixtures: Path) -> tuple[list[dict], dict]:
    files = {name: (fixtures / name).read_bytes() for name in FIXTURE_NAMES}
    data = {name: json.loads(raw) for name, raw in files.items()}
    ingredients = {row['ingredient_id']: row for row in data['ingredients.json']['ingredients']}
    documents = []
    for product in data['products.json']['products']:
        if product['review_status'] != 'approved':
            continue
        names = [ingredients[i]['name_zh'] for i in product['ingredient_ids'] if i in ingredients]
        product_type = f"类型 {product['product_type']} " if product.get('product_type') is not None else ''
        documents.append({'id': product['sku_id'], 'namespace': 'product', 'title': product['name_zh'] or product['name'],
            'text': f"{product['name_zh'] or product['name']} {product['name']} 品牌 {product['brand']} 品类 {product['category_id']} {product_type}规格 {product['spec_quantity']:g}{product['spec_unit']} 采购食材 {' '.join(names)} 用途 {' '.join(product['usage_tags'])}",
            'source': {'file': 'products.json', 'record_id': product['sku_id']}})
    for dish in data['recipes.json']['dishes']:
        required = '、'.join(f"{ingredients[item['ingredient_id']]['name_zh']} " + ' '.join(f"{item['quantity_' + unit]:g}{unit}" for unit in ('g', 'ml', 'pc') if 'quantity_' + unit in item) for item in dish['required_items'])
        pantry = '、'.join(ingredients[i]['name_zh'] for i in dish['pantry_items'])
        documents.append({'id': dish['dish_id'], 'namespace': 'recipe', 'title': dish['name'],
            'text': f"{dish['name']} 别名 {' '.join(dish['aliases'])} 基准 {dish['base_people']}人 必需食材 {required} 调料 {pantry}。调料数量未记录，家庭已有食材数量未知。",
            'source': {'file': 'recipes.json', 'record_id': dish['dish_id'], 'version': data['recipes.json']['version']}})
    policies = data['policies.json']
    for policy in policies['policies']:
        documents.append({'id': policy['policy_id'], 'namespace': 'policy', 'title': policy['title'], 'text': policy['content'],
            'source': {'file': 'policies.json', 'record_id': policy['policy_id'], 'version': policies['version'], 'name': policies['source_name']},
            'category': policy['category']})
    manifest = {'corpus_revision': CORPUS_REVISION,
        'files': {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()},
        'implementation': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('corpus.py', 'bge.py', 'hybrid.py', 'graph.py', 'providers.py')},
        'counts': {kind: sum(row['namespace'] == kind for row in documents) for kind in ('product', 'recipe', 'policy')}}
    return documents, manifest

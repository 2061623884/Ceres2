"""Select static Ceres1 examples; never restore its databases or indexes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RECIPE_IDS = (
    'dish-fanqie-chao-dan', 'dish-dan-chao-fan', 'dish-yangzhou-chao-fan',
    'dish-qingjiao-rousi', 'dish-gongbao-jiding', 'dish-suanla-tudousi',
    'dish-huiguo-rou', 'dish-jiajiao-chaodan',
)
VERSION = 'optimization-demo-v2'
ORIGIN_COMMIT = 'e24debf670db02a86cb79c40933b901827db8a55'


def save(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def import_knowledge(source: Path, target: Path):
    source_recipes = source / 'chinese-dishes-v1.json'
    source_ingredients = source / 'ingredient-catalog.json'
    origin = json.loads(source_recipes.read_text())
    by_id = {dish['dish_id']: dish for dish in origin['dishes']}
    recipes = [by_id[identifier] for identifier in RECIPE_IDS]
    ingredient_ids = {row['ingredient_id'] for dish in recipes for row in dish['required_items']}
    ingredient_ids.update(ingredient for dish in recipes for ingredient in dish['pantry_items'])
    ingredients = [row for row in json.loads(source_ingredients.read_text())['ingredients']
                   if row['ingredient_id'] in ingredient_ids]
    products = json.loads((target / 'products.json').read_text())
    offers = json.loads((target / 'offers.json').read_text())
    # ingredient_ids means procurement suitability, not a composition list.
    for product in products['products']:
        if product.get('product_type') == 'potato_chips' and 'potato' in product['ingredient_ids']:
            product['ingredient_ids'].remove('potato')
    shrimp_id = 'demo:shrimp-200g'
    if not any(product['sku_id'] == shrimp_id for product in products['products']):
        products['products'].append({
            'sku_id': shrimp_id, 'name': 'Demo Shrimp 200g', 'name_zh': '演示虾仁200克',
            'category_id': 'seafood', 'brand': '演示品牌', 'source': 'demo',
            'review_status': 'approved', 'image_path': None, 'image_status': 'placeholder',
            'spec_quantity': 200, 'spec_unit': 'g', 'ingredient_ids': ['shrimp'],
            'usage_tags': ['炒饭', '家常'], 'product_type': 'shrimp',
            'metadata': {'catalog_batch': VERSION, 'simulation': {'price': True, 'inventory': True},
                         'returnable': False, 'return_policy_source': 'Ceres 模拟商品规则'},
        })
    if not any(offer['sku_id'] == shrimp_id for offer in offers['offers']):
        offers['offers'].append({
            'store_id': offers['store']['store_id'], 'sku_id': shrimp_id,
            'price_fen': 1590, 'available_qty': 25, 'sellable': True,
            'offer_version': 1, 'is_demo': True,
            'provenance': 'Ceres2 optimization declared demo Offer; not a merchant quote',
        })
    products['version'] = offers['version'] = VERSION
    for ingredient in ingredients:
        if ingredient['ingredient_id'] == 'egg':
            ingredient['kind'] = 'egg'
    save(target / 'recipes.json', {'version': VERSION, 'dishes': recipes})
    save(target / 'ingredients.json', {'version': VERSION, 'ingredients': ingredients})
    save(target / 'products.json', products)
    save(target / 'offers.json', offers)
    save(target / 'knowledge-provenance.json', {
        'version': VERSION,
        'origin': {'repository': '2061623884/Ceres', 'commit': ORIGIN_COMMIT,
                   'files': {source_recipes.name: hashlib.sha256(source_recipes.read_bytes()).hexdigest(),
                             source_ingredients.name: hashlib.sha256(source_ingredients.read_bytes()).hexdigest()}},
        'selected_recipe_ids': list(RECIPE_IDS),
        'added_demo_sku_ids': [shrimp_id],
        'ingredient_classification_corrections': [{'ingredient_id': 'egg', 'from': 'dairy', 'to': 'egg',
            'reason': 'Eggs are not milk products; retail shelf placement must not become a food-class claim.'}],
        'procurement_mapping_corrections': [
            {'sku_id': identifier, 'removed_ingredient_id': 'potato',
             'reason': 'A ready-to-eat potato chip does not fulfill a raw potato recipe requirement.'}
            for identifier in ('demo:snack-original-potato-chips-70g-bag',
                               'demo:snack-original-potato-chips-35g-bag')],
        'business_data_mode': 'demo',
        'scope': 'Static recipe and ingredient selection only; no old runtime state or indexes.',
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-fixtures', type=Path, required=True)
    parser.add_argument('--target-fixtures', type=Path, required=True)
    args = parser.parse_args()
    import_knowledge(args.source_fixtures, args.target_fixtures)

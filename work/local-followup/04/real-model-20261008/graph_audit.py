"""Audit public GraphRAG output against the current static fixture source."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
fixture=json.loads((ROOT/'data/fixtures/recipes.json').read_text())['dishes']
ingredient_source={row['ingredient_id']:row for row in json.loads((ROOT/'data/fixtures/ingredients.json').read_text())['ingredients']}
global_path=ROOT/'work/local-followup/04/real-model-20261008/tmp/graph-global.stdout.json'
result=json.loads(global_path.read_text())
actual_pairs={}
for key,entry in result.get('ingredient_recipes',{}).items():
    ingredient_id=key.removeprefix('ingredient:')
    for row in entry.get('recipes',[]):
        actual_pairs[(ingredient_id,row['recipe_id'].removeprefix('recipe:'))]=row['source_description']
expected_pairs={}
for dish in fixture:
    for item in dish['required_items']:
        quantity=' '.join(f"{item['quantity_'+unit]:g}{unit}" for unit in ('g','ml','pc') if 'quantity_'+unit in item)
        expected_pairs[(item['ingredient_id'],dish['dish_id'])]=(
            f"REQUIRES: {dish['name']} 基准 {dish['base_people']} 人需 {quantity}，"
            f"原始用量来源 recipes.json/{dish['dish_id']}；其他人数和包装由业务服务计算。")
facts={row['id']:row for row in result.get('canonical_facts',[])}
expected_recipe_ids={dish['dish_id'] for dish in fixture}
actual_recipe_ids={identity.removeprefix('recipe:') for identity,row in facts.items() if row['type']=='RECIPE'}
kind_checks={}
for identity,source in ingredient_source.items():
    fact=facts.get('ingredient:'+identity)
    kind_checks[identity]=bool(fact and f"类别 {source['kind']}；" in fact['description'])
quantity_mismatches=[f'{ingredient}/{dish}' for (ingredient,dish),description in expected_pairs.items() if actual_pairs.get((ingredient,dish))!=description]
egg_expected={dish['dish_id'] for dish in fixture if any(item['ingredient_id']=='egg' for item in dish['required_items'])}
egg_actual={dish for (ingredient,dish) in actual_pairs if ingredient=='egg'}
manifest=json.loads((ROOT/'data/indexes/graphrag/manifest.json').read_text())
report={
    'graph_status':result.get('graph_status'),
    'query_revision':result.get('query_revision'),
    'query_deadline_seconds':180,
    'query_wall_ms':round(float(result.get('duration_ms',0)),1),
    'official_graph_calls':result.get('official_graph_calls'),
    'model_selected_count':len(result.get('model_selected_entity_ids',[])),
    'canonical_fact_count':len(facts),
    'recipe_scope_exact':actual_recipe_ids==expected_recipe_ids,
    'recipe_count':len(actual_recipe_ids),
    'required_recipe_ingredient_pairs_expected':len(expected_pairs),
    'required_pairs_actual':len(actual_pairs),
    'required_pairs_exact':set(actual_pairs)==set(expected_pairs),
    'quantity_source_mismatches':quantity_mismatches,
    'egg_recipe_ids_expected':sorted(egg_expected),
    'egg_recipe_ids_actual':sorted(egg_actual),
    'egg_recipe_map_exact':egg_actual==egg_expected,
    'ingredient_kind_checks':len(kind_checks),
    'ingredient_kind_mismatches':[identity for identity,valid in kind_checks.items() if not valid],
    'pork_fact_category_is_meat':bool(facts.get('ingredient:pork') and '类别 meat；' in facts['ingredient:pork']['description']),
    'graph_manifest_sha256':hashlib.sha256((ROOT/'data/indexes/graphrag/manifest.json').read_bytes()).hexdigest(),
    'graph_artifact_count':len(manifest.get('artifacts',{})),
    'graph_counts':manifest.get('output_counts'),
}
print(json.dumps(report,ensure_ascii=False,indent=2))

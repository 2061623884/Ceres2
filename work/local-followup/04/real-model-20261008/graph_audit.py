"""Audit one public GraphRAG query against the current static recipe fixtures."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
FIXTURES = ROOT / 'data/fixtures'
GRAPH_RESULT = ROOT / 'work/local-followup/04/real-model-20261008/tmp/graph-global.stdout.json'
GRAPH_MANIFEST = ROOT / 'data/indexes/graphrag/manifest.json'


def audit_graph_result(result, dishes, ingredient_records, manifest_sha256=None):
    expected_pairs = {}
    for dish in dishes:
        for item in dish['required_items']:
            quantity = ' '.join(
                f"{item['quantity_'+unit]:g}{unit}"
                for unit in ('g', 'ml', 'pc')
                if 'quantity_'+unit in item
            )
            expected_pairs[(item['ingredient_id'], dish['dish_id'])] = (
                f"REQUIRES: {dish['name']} 基准 {dish['base_people']} 人需 {quantity}，"
                f"原始用量来源 recipes.json/{dish['dish_id']}；其他人数和包装由业务服务计算。"
            )
    expected_recipe_ids = {dish['dish_id'] for dish in dishes}
    egg_expected = {
        dish['dish_id'] for dish in dishes
        if any(item['ingredient_id'] == 'egg' for item in dish['required_items'])
    }

    observed_duration = result.get('duration_ms')
    query_wall_ms = None if observed_duration is None else round(float(observed_duration), 1)
    common = {
        'audit_status': 'not_evaluated',
        'graph_status': result.get('graph_status'),
        'query_revision': result.get('query_revision'),
        'query_deadline_seconds': 180,
        'query_wall_ms': query_wall_ms,
        'official_graph_calls': result.get('official_graph_calls'),
        'model_selected_count': None,
        'canonical_fact_count': None,
        'recipe_scope_exact': None,
        'recipe_count': None,
        'required_recipe_ingredient_pairs_expected': len(expected_pairs),
        'required_pairs_actual': None,
        'required_pairs_exact': None,
        'quantity_source_mismatches': None,
        'egg_recipe_ids_expected': sorted(egg_expected),
        'egg_recipe_ids_actual': None,
        'egg_recipe_map_exact': None,
        'ingredient_kind_checks': None,
        'ingredient_kind_mismatches': None,
        'pork_fact_category_is_meat': None,
        'graph_manifest_sha256': manifest_sha256,
        'graph_artifact_count': None,
        'graph_counts': None,
    }

    if result.get('graph_status') != 'success':
        manifest = result.get('manifest')
        if isinstance(manifest, dict):
            artifacts = manifest.get('artifacts')
            if artifacts is not None:
                common['graph_artifact_count'] = len(artifacts)
            if 'output_counts' in manifest:
                common['graph_counts'] = manifest['output_counts']
        return common

    # The success contract includes these complete result fields. Missing
    # values must fail the audit instead of being interpreted as empty data.
    query_revision = result['query_revision']
    duration_ms = result['duration_ms']
    official_graph_calls = result['official_graph_calls']
    selected_entity_ids = result['model_selected_entity_ids']
    canonical_facts = result['canonical_facts']
    ingredient_recipes = result['ingredient_recipes']
    manifest = result['manifest']

    actual_pairs = {}
    for key, entry in ingredient_recipes.items():
        ingredient_id = key.removeprefix('ingredient:')
        for row in entry['recipes']:
            actual_pairs[(ingredient_id, row['recipe_id'].removeprefix('recipe:'))] = row['source_description']
    facts = {row['id']: row for row in canonical_facts}
    actual_recipe_ids = {
        identity.removeprefix('recipe:')
        for identity, row in facts.items()
        if row['type'] == 'RECIPE'
    }
    kind_checks = {}
    for ingredient in ingredient_records:
        fact = facts.get('ingredient:' + ingredient['ingredient_id'])
        kind_checks[ingredient['ingredient_id']] = bool(
            fact and f"类别 {ingredient['kind']}；" in fact['description']
        )
    quantity_mismatches = [
        f'{ingredient}/{dish}'
        for (ingredient, dish), description in expected_pairs.items()
        if actual_pairs.get((ingredient, dish)) != description
    ]
    egg_actual = {dish for (ingredient, dish) in actual_pairs if ingredient == 'egg'}
    pork_fact = facts.get('ingredient:pork')

    common.update({
        'audit_status': 'evaluated',
        'graph_status': 'success',
        'query_revision': query_revision,
        'query_wall_ms': round(float(duration_ms), 1),
        'official_graph_calls': official_graph_calls,
        'model_selected_count': len(selected_entity_ids),
        'canonical_fact_count': len(canonical_facts),
        'recipe_scope_exact': actual_recipe_ids == expected_recipe_ids,
        'recipe_count': len(actual_recipe_ids),
        'required_pairs_actual': len(actual_pairs),
        'required_pairs_exact': set(actual_pairs) == set(expected_pairs),
        'quantity_source_mismatches': quantity_mismatches,
        'egg_recipe_ids_actual': sorted(egg_actual),
        'egg_recipe_map_exact': egg_actual == egg_expected,
        'ingredient_kind_checks': len(kind_checks),
        'ingredient_kind_mismatches': [
            identity for identity, valid in kind_checks.items() if not valid
        ],
        'pork_fact_category_is_meat': bool(
            pork_fact and '类别 meat；' in pork_fact['description']
        ),
        'graph_artifact_count': len(manifest['artifacts']),
        'graph_counts': manifest['output_counts'],
    })
    return common


def main():
    dishes = json.loads((FIXTURES / 'recipes.json').read_text(encoding='utf-8'))['dishes']
    ingredient_records = json.loads(
        (FIXTURES / 'ingredients.json').read_text(encoding='utf-8')
    )['ingredients']
    result = json.loads(GRAPH_RESULT.read_text(encoding='utf-8'))
    manifest_sha256 = (
        hashlib.sha256(GRAPH_MANIFEST.read_bytes()).hexdigest()
        if GRAPH_MANIFEST.is_file() else None
    )
    print(json.dumps(
        audit_graph_result(result, dishes, ingredient_records, manifest_sha256),
        ensure_ascii=False, indent=2,
    ))


if __name__ == '__main__':
    main()

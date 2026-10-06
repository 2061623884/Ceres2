"""Single-dish recipe facts and deterministic sale-package demand."""
import json
from math import ceil
from sqlalchemy import select
from app.core.config import get_settings
from app.core.errors import AppError
from app.models.catalog import CatalogProduct
from app.services.catalog_service import CatalogService


def recipes():
    return json.loads((get_settings().root_dir / 'data/fixtures/recipes.json').read_text())['dishes']


class DishService:
    def __init__(self, catalog: CatalogService):
        self.catalog = catalog

    def search(self, query):
        return [dish for dish in recipes() if any(query in name for name in [dish['name'], *dish['aliases']])]

    def candidates(self, dish):
        ingredients = [row['ingredient_id'] for row in dish['required_items']] + dish['pantry_items']
        products = self.catalog.db.scalars(select(CatalogProduct).where(CatalogProduct.review_status == 'approved').order_by(CatalogProduct.sku_id)).all()
        return {ingredient:[self.catalog.get_product(p.sku_id) for p in products if ingredient in json.loads(p.ingredient_ids)] for ingredient in ingredients}

    def requirements(self, dish, people, selections, pack_allocations):
        candidates = self.candidates(dish)
        if set(selections) - set(candidates):
            raise AppError(422, 'DISH_SELECTION_INVALID', '规格不属于本菜谱食材')
        rows = []
        for source in [*dish['required_items'], *({'ingredient_id':ingredient} for ingredient in dish['pantry_items'])]:
            ingredient = source['ingredient_id']
            amount_fields = [(unit, source['quantity_' + unit]) for unit in ('g', 'ml', 'pc') if 'quantity_' + unit in source]
            unit, original = amount_fields[0] if amount_fields else (None, None)
            amount = original * people / dish['base_people'] if original is not None else None
            candidates_for_item = candidates[ingredient]
            selected_sku = selections.get(ingredient)
            if selected_sku:
                product = next((p for p in candidates_for_item if p['sku_id'] == selected_sku), None)
            else:
                compatible = [p for p in candidates_for_item if amount is None or (p['spec_unit'] == unit and p['spec_quantity'] is not None and p['spec_quantity'] > 0)]
                product = min(compatible, key=lambda p:(p['spec_quantity'] or float('inf'), p['sku_id'])) if compatible else None
            if product is None or (amount is not None and (product['spec_quantity'] is None or product['spec_unit'] is None)):
                rows.append({'available_specs':[{'sku_id':candidate['sku_id'], 'name':candidate['name_zh'] or candidate['name'], 'spec_quantity':candidate['spec_quantity'], 'spec_unit':candidate['spec_unit']} for candidate in candidates_for_item if candidate['spec_unit'] == unit and candidate['spec_quantity'] is not None and candidate['spec_quantity'] > 0], 'sku_id':selected_sku, 'ingredient_id':ingredient, 'quantity':None,
                             'selected':amount is not None, 'role':'required' if amount is not None else 'pantry',
                             'requirement':{'quantity':amount, 'unit':unit, 'source':{'original_quantity':original, 'original_unit':unit}},
                             'coverage_quantity':ceil(amount) if unit == 'pc' else amount, 'leftover_quantity':None,
                             'supply_issue':'spec_unknown' if candidates_for_item else 'ingredient_missing'})
                continue
            if amount is not None and (product['spec_unit'] != unit or product['spec_quantity'] is None or product['spec_quantity'] <= 0):
                raise AppError(409, 'DISH_UNIT_UNKNOWN', '规格与菜谱单位不可换算，不能推定覆盖用量')
            needed = ceil(amount) if unit == 'pc' else amount
            quantity = ceil(needed / product['spec_quantity']) if needed is not None else 1
            available_specs = [{'sku_id':candidate['sku_id'], 'name':candidate['name_zh'] or candidate['name'], 'spec_quantity':candidate['spec_quantity'], 'spec_unit':candidate['spec_unit']} for candidate in candidates_for_item if amount is None or (candidate['spec_unit'] == unit and candidate['spec_quantity'] is not None and candidate['spec_quantity'] > 0)]
            rows.append({'available_specs':available_specs, 'sku_id':product['sku_id'], 'ingredient_id':ingredient, 'quantity':quantity,
                         'selected':amount is not None, 'role':'required' if amount is not None else 'pantry',
                         'requirement':{'quantity':amount, 'unit':unit, 'source':{'original_quantity':original, 'original_unit':unit}},
                         'coverage_quantity':needed, 'leftover_quantity':quantity * product['spec_quantity'] - needed if needed is not None else None})
        allocated = []
        for row in rows:
            allocation = pack_allocations.get(row['ingredient_id'])
            if not allocation:
                allocated.append(row)
                continue
            for choice in allocation:
                amount = row['requirement']['quantity'] * choice['fraction']
                needed = ceil(amount) if row['requirement']['unit'] == 'pc' else amount
                spec = next((option for option in row['available_specs'] if option['sku_id'] == choice['sku_id']), None)
                split = {**row, 'sku_id':choice['sku_id'], 'requirement':{**row['requirement'],'quantity':amount}, 'coverage_quantity':needed}
                if spec is None:
                    split.update(quantity=None, leftover_quantity=None, supply_issue='spec_unknown')
                else:
                    quantity = ceil(needed / spec['spec_quantity'])
                    split.update(quantity=quantity, leftover_quantity=quantity * spec['spec_quantity'] - needed)
                allocated.append(split)
        return dish, allocated


def merge_group_requirements(group_rows):
    """Sum compatible source demand before rounding; retain every contribution."""
    merged = {}
    for group, requirements in group_rows:
        for row in requirements:
            contribution = {'group_id':group['group_id'], 'ingredient_id':row['ingredient_id'],
                            'sku_id':row['sku_id'], 'selected':row['selected'],
                            'quantity':row['quantity'], 'requirement':row['requirement']}
            key = row['sku_id'] or 'missing:' + row['ingredient_id']
            if key not in merged:
                merged[key] = {**row, 'contributions':[]}
            merged[key]['contributions'].append(contribution)
    for row in merged.values():
        recalculate_contribution_demand(row)
    return list(merged.values())


def recalculate_contribution_demand(row):
    """Recompute a merged row from its retained, explicitly selected sources."""
    contributions = row['contributions']
    selected = [item for item in contributions if item['selected']]
    active = selected or contributions
    row['selected'] = bool(selected)
    compatible = all(item['ingredient_id'] == active[0]['ingredient_id'] and item['requirement']['quantity'] is not None and item['requirement']['unit'] == active[0]['requirement']['unit'] for item in active)
    if compatible:
        amount = sum(item['requirement']['quantity'] for item in active)
        unit = active[0]['requirement']['unit']
        needed = ceil(amount) if unit == 'pc' else amount
        if row.get('supply_issue'):
            row['requirement'] = {'quantity':amount, 'unit':unit}
            row['coverage_quantity'] = needed
            return
        spec = next(option for option in row['available_specs'] if option['sku_id'] == row['sku_id'])
        row['quantity'] = ceil(needed / spec['spec_quantity'])
        row['requirement'] = {'quantity':amount, 'unit':unit}
        row['coverage_quantity'] = needed
        row['leftover_quantity'] = row['quantity'] * spec['spec_quantity'] - needed
    else:
        row['quantity'] = None if row.get('supply_issue') else sum(item['quantity'] for item in active)
        row['requirement'] = {'quantity':None, 'unit':None}
        row['coverage_quantity'] = None
        row['leftover_quantity'] = None
    if len(contributions) == 1:
        row['requirement'] = contributions[0]['requirement']

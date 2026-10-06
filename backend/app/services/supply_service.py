"""Requirement-addressed supply facts; proposals never select or add goods."""
from math import ceil
from sqlalchemy import select
from app.models.cart import Cart, CartItem
from app.models.purchase import PurchaseLedger
from app.services.catalog_service import CatalogService


def supply_gaps(rows, catalog: CatalogService, conditions, owner_id, task_id):
    cart_quantities = dict(catalog.db.execute(select(CartItem.sku_id, CartItem.quantity).join(Cart).where(Cart.owner_id == owner_id, Cart.store_id == catalog.store_id)).all())
    bought = dict(catalog.db.execute(select(PurchaseLedger.sku_id, PurchaseLedger.added_quantity).where(PurchaseLedger.task_id == task_id, PurchaseLedger.owner_id == owner_id)).all())
    gaps = []
    for row in rows:
        if not row['selected'] or row['available_to_add'] >= row['remaining_quantity'] and row['sellable']:
            continue
        requirement = row['requirement']
        available = row['available_to_add'] if row['sellable'] else 0
        alternatives = []
        for option in pack_alternatives(row, catalog, conditions, cart_quantities, bought):
            projected = project_alternative(rows, row, option, catalog)
            total = sum(item['quantity'] * catalog.get_product(item['sku_id'])['price_fen'] for item in projected if item['selected'])
            if conditions.get('budget_fen') is not None and total > conditions['budget_fen']:
                continue
            selected_skus = {item['sku_id'] for item in option['items']}
            if any(item['quantity'] > max(0,catalog.get_product(item['sku_id'])['available_qty']-cart_quantities.get(item['sku_id'],0))+bought.get(item['sku_id'],0) for item in projected if item['sku_id'] in selected_skus):
                continue
            option['plan_total_fen'] = total
            alternatives.append(option)
        gaps.append({'gap_id':f"supply:{row['sku_id']}", 'ingredient_id':row['ingredient_id'], 'sku_id':row['sku_id'],
                     'group_ids':[item['group_id'] for item in row['contributions'] if item['selected']],
                     'kind':'unavailable' if available == 0 else 'shortage',
                     'requirement':{'quantity':requirement['quantity'],'unit':requirement['unit']},
                     'requested_packs':row['remaining_quantity'], 'available_packs':available,
                     'shortfall_packs':max(0,row['remaining_quantity'] - available), 'alternatives':alternatives,
                     'message':f"{row['name']}需要 {row['remaining_quantity']} 件，当前可售 {available} 件；尚未选择替代或部分采购。"})
    return gaps


def unresolved_gap(row, kind):
    return {'gap_id':f"supply:{row['sku_id'] or row['ingredient_id']}", 'ingredient_id':row['ingredient_id'],
            'sku_id':row['sku_id'], 'group_ids':[item['group_id'] for item in row['contributions'] if item['selected']],
            'kind':kind, 'requirement':{'quantity':row['requirement']['quantity'],'unit':row['requirement']['unit']},
            'requested_packs':row['quantity'], 'available_packs':None, 'shortfall_packs':None,
            'unknown_attribute':'offer' if kind == 'availability_unknown' else 'spec' if kind == 'spec_unknown' else None,
            'alternatives':[], 'message':f"{row['ingredient_id']}：" + {'ingredient_missing':'当前目录缺少整种食材，不能形成完整清单。','availability_unknown':'当前门店供给未知，不能当作缺货或承诺可售。','spec_unknown':'包装规格未知或单位不可换算，不能推定所需件数。'}[kind]}


def pack_alternatives(row, catalog, conditions, cart_quantities, bought):
    """Evaluate whole demand, actual stock and total price, never unit-price alone."""
    needed = row['coverage_quantity']
    if needed is None:
        return []
    products = [catalog.get_product(spec['sku_id']) for spec in row['available_specs']]
    exclusions = conditions.get('exclusions', [])
    products = [p for p in products if p['sellable'] and p['available_qty'] is not None and not any(exclusion in [p['sku_id'],p['name'],p['name_zh'],p['brand'],*p['ingredient_ids'],*p['usage_tags']] for exclusion in exclusions)]
    states = {0:(0,[])}
    complete = []
    for product in products:
        expanded = dict(states)
        for covered,(price,items) in states.items():
            for count in range(1,min(max(0,product['available_qty']-cart_quantities.get(product['sku_id'],0))+bought.get(product['sku_id'],0),ceil((needed-covered)/product['spec_quantity']))+1):
                amount = covered + count * product['spec_quantity']
                total = price + count * product['price_fen']
                selected = items + [{'sku_id':product['sku_id'],'quantity':count}]
                if amount >= needed:
                    complete.append({'items':selected,'total_price_fen':total,'leftover_quantity':amount-needed})
                elif amount not in expanded or total < expanded[amount][0]:
                    expanded[amount] = (total,selected)
        states = expanded
    complete.sort(key=lambda option:(option['total_price_fen'],option['leftover_quantity'],len(option['items'])))
    return complete


def alternative_requirements(source, option, catalog):
    """Partition source amount across chosen packs, without duplicating group demand."""
    pending = [{**item,'requirement':dict(item['requirement'])} for item in source['contributions'] if item['selected']]
    rows = []
    for selected in option['items']:
        product = catalog.get_product(selected['sku_id'])
        capacity = selected['quantity'] * product['spec_quantity']
        contributions = []
        for item in pending:
            amount = min(capacity,item['requirement']['quantity'])
            if amount <= 0:
                continue
            contributions.append({**item,'sku_id':selected['sku_id'],'quantity':selected['quantity'], 'requirement':{**item['requirement'],'quantity':amount}})
            capacity -= amount
            item['requirement']['quantity'] -= amount
        amount = sum(item['requirement']['quantity'] for item in contributions)
        coverage = ceil(amount) if source['requirement']['unit'] == 'pc' else amount
        rows.append({**source,**selected,'contributions':contributions, 'requirement':{'quantity':amount,'unit':source['requirement']['unit']},
                     'coverage_quantity':coverage,'leftover_quantity':selected['quantity'] * product['spec_quantity']-coverage})
    return rows


def project_alternative(rows, source, option, catalog):
    """One merged demand projection for both candidate pricing and explicit choice."""
    from app.services.dish_service import recalculate_contribution_demand
    replacements = alternative_requirements(source, option, catalog)
    requested = [row for row in rows if row['sku_id'] != source['sku_id']] + replacements
    combined = {}
    for row in requested:
        if row['sku_id'] in combined:
            merged = combined[row['sku_id']]
            merged['contributions'] = [*merged['contributions'], *row['contributions']]
            recalculate_contribution_demand(merged)
        else:
            combined[row['sku_id']] = dict(row)
    return list(combined.values())

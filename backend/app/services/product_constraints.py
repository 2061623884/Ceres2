"""Dietary safety requires explicit attribute evidence, never ingredient-ID inference."""
def safety_mismatch(product, conditions):
    evidence = product['metadata'].get('attribute_evidence', {})
    excluded = conditions.get('excluded_allergens') or []
    if excluded:
        allergens = evidence.get('allergens')
        if not allergens or not allergens.get('source') or not isinstance(allergens.get('value'), list):
            return '过敏原信息未知，无法核实是否满足你的限制。'
        if set(excluded) & set(allergens['value']):
            return '商品的已知过敏原不符合当前限制。'
    for requirement in conditions.get('dietary_requirements') or []:
        attribute = evidence.get(requirement)
        if not attribute or not attribute.get('source') or attribute.get('value') is not True:
            return '饮食属性未知或不符合要求，无法核实是否满足你的限制。'
    return None


def drink_filter_values(product):
    """Known catalog attributes only; sugar claims are not inferred as flavors."""
    quantity, unit = product['spec_quantity'], product['spec_unit']
    return {'brand':product['brand'], 'flavor':product['metadata'].get('flavor'),
            'packaging':product['metadata'].get('packaging'),
            'spec':{'quantity':quantity, 'unit':unit} if quantity is not None and unit else None}



PRODUCT_TYPE_ALIASES = {'饮用水':'water', 'drinking_water':'water', '茶饮':'tea', '可乐':'cola',
                        '苏打水':'sparkling_water', '果汁':'juice', '果汁饮料':'juice_drink'}
CONTAINER_ALIASES = {'瓶':'bottle', '瓶装':'bottle', '罐':'can', '罐装':'can',
                     '盒':'box', '盒装':'box', '袋':'bag', '袋装':'bag'}
CASE_ALIASES = ('箱', '箱装', 'case')


def product_type_matches(actual, requested):
    return PRODUCT_TYPE_ALIASES.get(actual, actual) == PRODUCT_TYPE_ALIASES.get(requested, requested)


def packaging_matches(metadata, requested):
    # The container and its count do not establish the selling unit.
    if requested in CASE_ALIASES:
        return metadata.get('selling_unit') == 'case' and bool(metadata.get('selling_unit_source'))
    return metadata.get('packaging') == CONTAINER_ALIASES.get(requested, requested)


def drink_filter_mismatch(product, conditions):
    """Shared candidate constraints; flavor and volume remain drink-specific."""
    if conditions.get('category_id') is not None and product['category_id'] != conditions['category_id']:
        return True
    packs = product['metadata'].get('pack_count')
    if conditions.get('pack_count_mode') == 'single' and packs != 1:
        return True
    if conditions.get('pack_count_mode') == 'multi' and (packs is None or packs <= 1):
        return True
    if conditions.get('product_type') is not None and not product_type_matches(product['product_type'], conditions['product_type']):
        return True
    if conditions.get('packaging') is not None and not packaging_matches(product['metadata'], conditions['packaging']):
        return True
    if conditions.get('brand') is not None and product['brand'] != conditions['brand']:
        return True
    if product['category_id'] != 'beverage':
        return False
    values = drink_filter_values(product)
    return any(conditions.get(key) is not None and conditions[key] != values[key]
               for key in ('flavor', 'spec'))


def offer_mismatch(product, conditions):
    quantity = conditions.get('quantity', 1)
    if not product['sellable'] or product['available_qty'] < quantity:
        return True
    budget = conditions.get('budget_fen')
    return budget is not None and product['price_fen'] * quantity > budget

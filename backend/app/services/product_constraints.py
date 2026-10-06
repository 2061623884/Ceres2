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


def drink_filter_mismatch(product, conditions):
    if product['category_id'] != 'beverage':
        return False
    values = {**drink_filter_values(product), 'product_type':product['product_type']}
    return any(conditions.get(key) is not None and conditions[key] != value for key,value in values.items())

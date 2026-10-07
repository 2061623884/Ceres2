"""Factual comparison projection and scoped displayed evidence in canonical SQL."""
import json
from uuid import uuid4
from app.models.comparison import ComparisonDisplay
from app.services.catalog_service import CatalogService
from app.core.errors import AppError
from app.services.product_constraints import safety_mismatch, product_filter_mismatch, offer_mismatch, product_type_matches, packaging_matches


def comparison_card(product):
    metadata = product['metadata']
    total = product['spec_quantity'] if product['spec_unit'] == 'ml' else None
    item = metadata.get('item_quantity') if metadata.get('item_unit') == 'ml' else None
    price = product['price_fen']
    return {
        'ref': f'candidate-{uuid4().hex}', 'sku_id': product['sku_id'],
        'name': product['name_zh'] or product['name'], 'brand': product['brand'],
        'image_path': product['image_path'], 'packaging': metadata.get('packaging'),
        'pack_count': metadata.get('pack_count'), 'item_volume_ml': item,
        'total_volume_ml': total, 'spec_quantity': product['spec_quantity'], 'spec_unit': product['spec_unit'],
        'price_fen': price, 'price_per_litre_yuan': price * 10 / total if price is not None and total is not None and total > 0 else None,
    }


class ComparisonService:
    def __init__(self, db, owner_id, *, deadline=None, should_stop=None):
        self.db, self.owner_id = db, owner_id
        self.deadline, self.should_stop = deadline, should_stop

    def _scope(self, session_id, view_context=None):
        from app.services.pi_product_turn_service import owned_session, session_anchor
        session = owned_session(self.db, self.owner_id, session_id)
        entry = json.loads(session.entry_context_json)
        context = {key: (view_context or entry).get(key) for key in ('page', 'category_id', 'product_id')}
        context['store_id'] = session.supply_store_id or entry['store_id']
        context['delivery_zone_id'] = session.delivery_zone_id or entry['delivery_zone_id']
        return session_anchor(self.db, session), context

    def search(self, session_id, arguments, view_context=None, *, scope_to_page=True):
        from app.models.guide import GuideTask
        anchor, context = self._scope(session_id, view_context)
        task = self.db.get(GuideTask, anchor[1]) if anchor[1] else None
        conditions = json.loads(task.conditions_json) if task else {}
        filters = {**arguments, **{key: conditions[key] for key in ('query', 'category_id', 'brand', 'packaging', 'pack_count_mode') if conditions.get(key) is not None}}
        category = (context['category_id'] if scope_to_page else None) or filters.get('category_id')
        if scope_to_page and context['category_id'] and filters.get('category_id') and context['category_id'] != filters['category_id']:
            return [], 0
        if conditions.get('activity_id'):
            from app.services.product_question_service import ProductQuestionService
            products = ProductQuestionService(self.db, self.owner_id, deadline=self.deadline, should_stop=self.should_stop).explore(session_id, {'category_id':category, 'query':filters.get('query')})['products']
            return products[:5], len(products)
        catalog = CatalogService(self.db, context['store_id'], deadline=self.deadline, should_stop=self.should_stop)
        matched, count, page = [], 0, 1
        while True:
            products, total = catalog.search_products(q=filters.get('query'), category_id=category, page=page, page_size=100)
            for product in products:
                if safety_mismatch(product, conditions) or product_filter_mismatch(product, conditions) or offer_mismatch(product, conditions):
                    continue
                if conditions.get('product_type') is not None and not product_type_matches(product['product_type'], conditions['product_type']):
                    continue
                metadata = product['metadata']
                if filters.get('brand') is not None and product['brand'] != filters['brand']:
                    continue
                if filters.get('packaging') is not None and not packaging_matches(metadata, filters['packaging']):
                    continue
                packs = metadata.get('pack_count')
                if filters.get('pack_count_mode') == 'single' and packs != 1:
                    continue
                if filters.get('pack_count_mode') == 'multi' and (packs is None or packs <= 1):
                    continue
                identities = [product['sku_id'], product['name'], product['name_zh'], product['brand'], *product['ingredient_ids'], *product['usage_tags']]
                if any(excluded in identities for excluded in conditions.get('exclusions', [])):
                    continue
                count += 1
                if len(matched) < 5:
                    matched.append(product)
            if page * 100 >= total:
                break
            page += 1
        return matched, count

    def publish(self, session_id, products, message_id, view_context=None):
        anchor, context = self._scope(session_id, view_context)
        cards = [comparison_card(product) for product in products[:5]]
        row = self.db.get(ComparisonDisplay, session_id)
        if row is None:
            row = ComparisonDisplay(session_id=session_id, owner_id=self.owner_id)
            self.db.add(row)
        row.task_id, row.session_version, row.state_version = anchor[1], anchor[0], anchor[2]
        row.context_json = json.dumps(context, sort_keys=True)
        row.cards_json, row.message_id = json.dumps(cards, ensure_ascii=False), message_id
        return cards

    def current(self, session_id, view_context=None):
        anchor, context = self._scope(session_id, view_context)
        row = self.db.get(ComparisonDisplay, session_id)
        if row is None or row.owner_id != self.owner_id or (row.session_version, row.task_id, row.state_version) != anchor:
            return []
        # A restored session has no live page argument. Its persisted page is
        # displayed as provenance; an explicit current page must match exactly.
        saved = json.loads(row.context_json)
        if any(saved[key] != context[key] for key in ('store_id', 'delivery_zone_id')):
            return []
        if view_context is not None and saved != context:
            return []
        return json.loads(row.cards_json)

    def clear(self, session_id, expected_refs):
        self._scope(session_id)
        row = self.db.get(ComparisonDisplay, session_id)
        if row is not None and [card['ref'] for card in json.loads(row.cards_json)] == expected_refs:
            row.cards_json = '[]'

    def resolve(self, session_id, ref, displayed_refs, view_context=None):
        cards = self.current(session_id, view_context)
        selected = next((card for card in cards if card['ref'] == ref), None)
        if ref not in displayed_refs or selected is None:
            raise AppError(409, 'COMPARISON_STALE', '候选未展示或已失效，请重新比较后选择')
        _anchor, context = self._scope(session_id, view_context)
        product = CatalogService(self.db, context['store_id'], deadline=self.deadline, should_stop=self.should_stop).get_product(selected['sku_id'])
        if product is None:
            raise AppError(409, 'COMPARISON_STALE', '候选商品已不可查询，请重新比较')
        return product

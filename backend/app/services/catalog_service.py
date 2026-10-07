"""Read-only SKU and current store-offer projection for HTTP and Pi."""
import json
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.catalog import CatalogProduct
from app.models.store import Offer

CATEGORY_NAMES = {
    'vegetable': ('Vegetables', '蔬菜'), 'meat': ('Meat', '肉类'),
    'seafood': ('Seafood', '水产'), 'fruit': ('Fruit', '水果'),
    'condiment': ('Condiments', '调味品'), 'baking': ('Baking', '烘焙原料'),
    'staple': ('Staples', '粮油米面'), 'dairy': ('Dairy', '乳品'),
    'snack': ('Snacks', '零食'), 'beverage': ('Beverages', '饮料'),
}


def product_to_dict(product: CatalogProduct, offer: Offer | None) -> dict:
    return {
        'sku_id': product.sku_id, 'name': product.name, 'name_zh': product.name_zh,
        'category_id': product.category_id, 'brand': product.brand,
        'image_path': product.image_path, 'source': product.source,
        'review_status': product.review_status, 'spec_quantity': product.spec_quantity,
        'spec_unit': product.spec_unit, 'ingredient_ids': json.loads(product.ingredient_ids),
        'usage_tags': json.loads(product.usage_tags), 'product_type': product.product_type,
        'metadata': json.loads(product.metadata_json),
        'price_fen': offer.price_fen if offer else None,
        'available_qty': offer.available_qty if offer else None,
        'sellable': offer.sellable if offer else False,
        'offer_version': offer.offer_version if offer else None,
        'delivery_eta_minutes': None,
    }


class CatalogService:
    def __init__(self, db: Session, store_id: str = 'store-demo-01', *, deadline=None, should_stop=None):
        self.db, self.store_id = db, store_id
        self.deadline, self.should_stop = deadline, should_stop

    def get_categories(self) -> list[dict]:
        rows = self.db.execute(select(CatalogProduct.category_id, func.count()).where(
            CatalogProduct.review_status == 'approved').group_by(CatalogProduct.category_id).order_by(CatalogProduct.category_id))
        return [{'id': category, 'name': CATEGORY_NAMES.get(category, (category, category))[0],
                 'name_zh': CATEGORY_NAMES.get(category, (category, category))[1], 'product_count': count}
                for category, count in rows]

    def _query(self):
        return select(CatalogProduct, Offer).outerjoin(Offer, (Offer.sku_id == CatalogProduct.sku_id) & (Offer.store_id == self.store_id)).where(CatalogProduct.review_status == 'approved').execution_options(populate_existing=True)

    def search_products(self, *, q: str | None = None, category_id: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        query = self._query()
        if category_id:
            query = query.where(CatalogProduct.category_id == category_id)
        if q:
            from app.core.config import get_settings
            from app.core.errors import AppError
            from app.knowledge.corpus import FIXTURE_NAMES, manifest_revision
            from app.knowledge.hybrid import validate_manifest, StaleIndexError
            from app.services.knowledge_service import knowledge
            allowed = list(self.db.scalars(select(CatalogProduct.sku_id).where(
                CatalogProduct.review_status == 'approved',
                *([CatalogProduct.category_id == category_id] if category_id else []))))
            if not allowed:
                return [], 0
            # Retrieve the whole eligible ID space before downstream business
            # filters. The 21st affordable candidate must not disappear at top20.
            retrieval = knowledge.search(q, 'product', limit=len(allowed), allowed_ids=allowed,
                deadline=self.deadline, should_stop=self.should_stop)
            folder = get_settings().root_dir / 'data/fixtures'
            try:
                validate_manifest(retrieval['manifest'], {name:(folder / name).read_bytes() for name in FIXTURE_NAMES})
            except StaleIndexError as exc:
                raise AppError(503, 'KNOWLEDGE_STALE', '商品检索来源已变化，请重新构建索引') from exc
            allowed_set = set(allowed)
            hits = {hit['id']:hit for hit in retrieval['hits'] if hit['id'] in allowed_set}
            # Re-read current approved identity/category and mutable Offer after
            # recall; index documents never supply price, availability or stock.
            rows = self.db.execute(query.where(CatalogProduct.sku_id.in_(hits))).all()
            current = {product.sku_id:product_to_dict(product, offer) for product, offer in rows}
            ranked = [{**current[identity], 'retrieval':{
                'source':hit['document']['source'], 'ranks':hit['ranks'], 'scores':hit['scores'],
                'rrf_score':hit['rrf_score'], 'corpus_revision':retrieval['manifest']['corpus_revision'],
                'index_revision':manifest_revision(retrieval['manifest'])}}
                for identity, hit in hits.items() if identity in current]
            return ranked[(page-1)*page_size:page*page_size], len(ranked)
        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        rows = self.db.execute(query.order_by(CatalogProduct.sku_id).offset((page - 1) * page_size).limit(page_size))
        return [product_to_dict(product, offer) for product, offer in rows], total

    def get_product(self, sku_id: str) -> dict | None:
        row = self.db.execute(self._query().where(CatalogProduct.sku_id == sku_id)).first()
        return product_to_dict(*row) if row else None

"""Explicit, repeatable static-fixture import, never a runtime-state restore."""
import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.catalog import CatalogProduct
from app.models.store import Offer, Store


def seed_catalog(db: Session, fixture_dir: Path | None = None) -> None:
    folder = fixture_dir or get_settings().root_dir / 'data/fixtures'
    products = json.loads((folder / 'products.json').read_text())['products']
    supply = json.loads((folder / 'offers.json').read_text())
    images = json.loads((folder / 'product-images.json').read_text())
    store = supply['store']
    if db.get(Store, store['store_id']) is None:
        delivery = supply['delivery']
        reachable = delivery['reachable'] if delivery['zone_id'] == store['delivery_zone_id'] else None
        db.add(Store(**store, delivery_reachable=reachable, delivery_version=1))
    for product in products:
        existing = db.get(CatalogProduct, product['sku_id'])
        if existing is None:
            db.add(CatalogProduct(
                sku_id=product['sku_id'], name=product['name'], name_zh=product.get('name_zh'),
                category_id=product['category_id'], brand=product.get('brand'),
                image_path=images.get(product['sku_id'], product.get('image_path')), source=product['source'],
                review_status=product['review_status'], spec_quantity=product.get('spec_quantity'),
                spec_unit=product.get('spec_unit'), product_type=product.get('product_type'),
                ingredient_ids=json.dumps(product.get('ingredient_ids', []), ensure_ascii=False),
                usage_tags=json.dumps(product.get('usage_tags', []), ensure_ascii=False),
                metadata_json=json.dumps(product.get('metadata', {}), ensure_ascii=False),
            ))
        elif 'type_label' in product.get('metadata', {}):
            # This released static attribute was absent in the earlier seed.
            # Never reset mutable Offer facts or replace unrelated catalog data.
            metadata = json.loads(existing.metadata_json)
            metadata['type_label'] = product['metadata']['type_label']
            if product['metadata'].get('drink_attribute_version') == 'next-drink-v1':
                existing.product_type = product['product_type']
                for key in ('flavor', 'drink_attribute_version'):
                    if key in product['metadata']:
                        metadata[key] = product['metadata'][key]
            existing.metadata_json = json.dumps(metadata, ensure_ascii=False)
    db.flush()
    for offer in supply['offers']:
        present = db.scalar(select(Offer).where(Offer.store_id == offer['store_id'], Offer.sku_id == offer['sku_id']))
        if present is None:
            db.add(Offer(**{key: offer[key] for key in ('store_id', 'sku_id', 'price_fen', 'available_qty', 'sellable', 'offer_version', 'is_demo')}))
    db.flush()


if __name__ == '__main__':
    from app.core.database import init_db, SessionLocal
    init_db()
    with SessionLocal.begin() as session:
        seed_catalog(session)

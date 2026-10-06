"""Minimal shelf cart commands. Owner write fence serializes SQLite transactions."""
from datetime import datetime, timezone
from sqlalchemy import update
from app.core.errors import AppError
from app.models.cart import Cart, CartItem
from app.models.catalog import CatalogProduct
from app.models.identity import Owner
from app.models.store import Offer, Store


class CartService:
    def __init__(self, db, owner_id):
        self.db, self.owner_id = db, owner_id

    def fence(self):
        self.db.execute(update(Owner).where(Owner.id == self.owner_id).values(id=Owner.id))

    def _cart(self):
        return self.db.query(Cart).filter_by(owner_id=self.owner_id).first()

    def _create(self):
        if self.db.get(Store, 'store-demo-01') is None:
            raise AppError(503, 'CATALOG_NOT_SEEDED', '尚未导入演示商品')
        cart = Cart(owner_id=self.owner_id, store_id='store-demo-01', version=1)
        self.db.add(cart)
        self.db.flush()
        return cart

    def _view(self, cart):
        items = []
        for row in self.db.query(CartItem).filter_by(cart_id=cart.id).order_by(CartItem.sku_id):
            product = self.db.get(CatalogProduct, row.sku_id)
            offer = self.db.query(Offer).filter_by(store_id=cart.store_id, sku_id=row.sku_id).first()
            items.append({'sku_id': row.sku_id, 'name': product.name_zh or product.name,
                          'quantity': row.quantity, 'unit_price_fen': row.unit_price_fen,
                          'line_total_fen': row.quantity * row.unit_price_fen,
                          'image_path': product.image_path,
                          'sellable': bool(offer and offer.sellable and offer.available_qty >= row.quantity)})
        return {'store_id': cart.store_id, 'version': cart.version, 'items': items,
                'total_price_fen': sum(item['line_total_fen'] for item in items), 'business_data_mode': 'demo'}

    def get_cart(self):
        cart = self._cart()
        if cart is None:
            self.fence()
            cart = self._cart() or self._create()
            self.db.commit()
        return self._view(cart)

    def _write_item(self, cart, sku_id, quantity, item):
        product = self.db.get(CatalogProduct, sku_id)
        offer = self.db.query(Offer).filter_by(store_id=cart.store_id, sku_id=sku_id).first()
        if not product or product.review_status != 'approved' or not offer or not offer.sellable or offer.available_qty < quantity:
            raise AppError(409, 'CHECKOUT_UNAVAILABLE', '商品供给不足或不可售')
        if item:
            item.quantity, item.unit_price_fen = quantity, offer.price_fen
        else:
            self.db.add(CartItem(cart_id=cart.id, sku_id=sku_id, quantity=quantity, unit_price_fen=offer.price_fen))

    def add_in_transaction(self, store_id, items):
        """Caller holds owner fence and owns commit, ledger and receipt."""
        cart = self._cart()
        if cart is None:
            cart = Cart(owner_id=self.owner_id, store_id=store_id, version=1)
            self.db.add(cart)
            self.db.flush()
        if cart.store_id != store_id:
            raise AppError(409, 'CART_STORE_MISMATCH', '购物车门店与清单不同')
        for proposed in items:
            sku_id, quantity = proposed['sku_id'], proposed['quantity']
            item = self.db.query(CartItem).filter_by(cart_id=cart.id, sku_id=sku_id).first()
            target = quantity + (item.quantity if item else 0)
            self._write_item(cart, sku_id, target, item)
        cart.version += 1
        cart.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return cart.version

    def mutate(self, sku_id, quantity, expected_version, action):
        try:
            self.fence()
            cart = self._cart() or self._create()
            if cart.version != expected_version:
                raise AppError(409, 'STALE_STATE', '购物车已变化，请刷新')
            item = self.db.query(CartItem).filter_by(cart_id=cart.id, sku_id=sku_id).first()
            if action != 'add' and item is None:
                raise AppError(404, 'NOT_FOUND', '购物车商品不存在')
            target = quantity + (item.quantity if item and action == 'add' else 0)
            if action == 'remove':
                self.db.delete(item)
            else:
                self._write_item(cart, sku_id, target, item)
            cart.version += 1
            cart.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            result = self._view(cart)
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise

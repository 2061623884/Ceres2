"""Versioned checkout: one transaction for order, precise cart deduction and receipt."""
import json
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import delete, update
from app.core.errors import AppError
from app.models.cart import Cart, CartItem
from app.models.catalog import CatalogProduct
from app.models.checkout import CheckoutPreview, CheckoutReceipt
from app.models.store import Offer
from app.mercury.models import SimulatedOrder
from app.services.cart_service import CartService


class CheckoutService:
    def __init__(self, db, owner_id):
        self.db, self.owner_id = db, owner_id

    def _snapshot(self, cart):
        items = []
        for row in self.db.query(CartItem).filter_by(cart_id=cart.id).order_by(CartItem.sku_id):
            product = self.db.get(CatalogProduct, row.sku_id)
            offer = self.db.query(Offer).filter_by(store_id=cart.store_id, sku_id=row.sku_id).first()
            if not product or product.review_status != 'approved' or not offer or not offer.sellable or offer.available_qty < row.quantity:
                raise AppError(409, 'CHECKOUT_UNAVAILABLE', '商品供给已变化，请更新购物车')
            metadata = json.loads(product.metadata_json)
            items.append({'sku_id': row.sku_id, 'name': product.name_zh or product.name,
                          'quantity': row.quantity, 'unit_price_fen': offer.price_fen,
                          'line_total_fen': offer.price_fen * row.quantity,
                          'image_path': product.image_path, 'offer_version': offer.offer_version,
                          'returnable': metadata.get('returnable'),
                          'return_policy_source': metadata.get('return_policy_source', 'unspecified')})
        if not items:
            raise AppError(422, 'EMPTY_CART', '购物车为空')
        return {'store_id': cart.store_id, 'items': items,
                'total_fen': sum(i['line_total_fen'] for i in items), 'business_data_mode': 'demo'}

    def preview(self, expected_cart_version):
        try:
            CartService(self.db, self.owner_id).fence()
            cart = self.db.query(Cart).filter_by(owner_id=self.owner_id).first()
            if cart is None:
                raise AppError(422, 'EMPTY_CART', '购物车为空')
            if cart.version != expected_cart_version:
                raise AppError(409, 'STALE_STATE', '购物车已变化，请刷新结算摘要')
            snapshot = self._snapshot(cart)
            preview = CheckoutPreview(preview_id=f'checkout-{uuid4().hex}', owner_id=self.owner_id,
                cart_id=cart.id, cart_version=cart.version, snapshot_json=json.dumps(snapshot, ensure_ascii=False))
            self.db.add(preview)
            self.db.commit()
            return {'preview_id': preview.preview_id, 'cart_version': preview.cart_version, **snapshot}
        except Exception:
            self.db.rollback()
            raise

    def confirm(self, preview_id, idempotency_key):
        try:
            # Fence before reading receipt or cart: a second request observes the
            # committed result, including after the first response was lost.
            CartService(self.db, self.owner_id).fence()
            existing = self.db.query(CheckoutReceipt).filter_by(owner_id=self.owner_id, idempotency_key=idempotency_key).first()
            if existing:
                if existing.preview_id != preview_id:
                    raise AppError(409, 'IDEMPOTENCY_CONFLICT', '确认编号已用于其他结算')
                result = json.loads(existing.result_json)
                self.db.rollback()
                return result
            preview = self.db.query(CheckoutPreview).filter_by(owner_id=self.owner_id, preview_id=preview_id).first()
            if preview is None:
                raise AppError(404, 'NOT_FOUND', '结算摘要不存在')
            if self.db.query(CheckoutReceipt).filter_by(preview_id=preview_id).first():
                raise AppError(409, 'CHECKOUT_ALREADY_CONFIRMED', '该摘要已结算，请查看订单')
            cart = self.db.query(Cart).filter_by(owner_id=self.owner_id, id=preview.cart_id).first()
            if cart is None or cart.version != preview.cart_version:
                raise AppError(409, 'STALE_STATE', '购物车已变化，请刷新结算摘要')
            snapshot = json.loads(preview.snapshot_json)
            if self._snapshot(cart) != snapshot:
                raise AppError(409, 'STALE_STATE', '价格或商品信息已变化，请刷新结算摘要')
            for item in snapshot['items']:
                removed = self.db.execute(delete(CartItem).where(CartItem.cart_id == cart.id,
                    CartItem.sku_id == item['sku_id'], CartItem.quantity == item['quantity']))
                if removed.rowcount != 1:
                    raise AppError(409, 'STALE_STATE', '购物车已变化，请刷新结算摘要')
            cart.version += 1
            cart.updated_at = datetime.now(timezone.utc)
            order = SimulatedOrder(order_id=f'sim-{uuid4().hex}', owner_id=self.owner_id,
                store_id=cart.store_id, status='submitted', version=1, snapshot_json=preview.snapshot_json,
                total_fen=snapshot['total_fen'], created_at=datetime.now(timezone.utc), delivered_at=None)
            self.db.add(order)
            self.db.flush()  # establish FK before receipt, still inside this transaction
            result = {'receipt_id': f'receipt-{uuid4().hex}', 'order': self._order(order), 'cart_version': cart.version}
            self.db.add(CheckoutReceipt(receipt_id=result['receipt_id'], owner_id=self.owner_id,
                idempotency_key=idempotency_key, preview_id=preview_id, order_id=order.order_id,
                result_json=json.dumps(result, ensure_ascii=False)))
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _order(order):
        created = order.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        snapshot = json.loads(order.snapshot_json)
        # P02 snapshots predate display metadata. Derive only from recorded
        # quantities/prices; absent image/offer authority remains unknown.
        items = [{**item, 'line_total_fen': item['quantity'] * item['unit_price_fen'],
                  'image_path': item.get('image_path'),
                  'offer_version': item.get('offer_version')} for item in snapshot['items']]
        return {**snapshot, 'items': items, 'store_id': order.store_id,
                'order_id': order.order_id, 'status': order.status, 'version': order.version,
                'total_fen': order.total_fen, 'business_data_mode': 'demo',
                'created_at': created.isoformat(),
                'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None}

    def list_orders(self):
        return {'items': [self._order(row) for row in self.db.query(SimulatedOrder)
            .filter_by(owner_id=self.owner_id).order_by(SimulatedOrder.created_at.desc(), SimulatedOrder.order_id)]}

    def get_order(self, order_id):
        order = self.db.query(SimulatedOrder).filter_by(owner_id=self.owner_id, order_id=order_id).first()
        if order is None:
            raise AppError(404, 'NOT_FOUND', '订单不存在')
        return self._order(order)

    def advance_demo(self, order_id, expected_version, status):
        previous = 'submitted' if status == 'shipped' else 'shipped'
        change = {'status': status, 'version': SimulatedOrder.version+1}
        if status == 'delivered':
            change['delivered_at'] = datetime.now(timezone.utc)
        changed = self.db.execute(update(SimulatedOrder).where(
            SimulatedOrder.order_id == order_id, SimulatedOrder.owner_id == self.owner_id,
            SimulatedOrder.version == expected_version, SimulatedOrder.status == previous,
        ).values(**change))
        if changed.rowcount != 1:
            self.db.rollback()
            self.get_order(order_id)  # retain the owner-scoped not-found contract
            raise AppError(409, 'ORDER_STATE_CHANGED', '订单状态已变化，请刷新；模拟状态只能依次推进配送、签收')
        self.db.commit()
        return self.get_order(order_id)

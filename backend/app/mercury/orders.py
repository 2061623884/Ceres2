"""Read-only Mercury projection of P12 canonical simulated order snapshots."""
import json
from datetime import datetime, timedelta, timezone
from app.mercury.models import SimulatedOrder

STATUS_TEXT = {'submitted': '模拟订单已提交', 'paid': '模拟已支付未发货',
               'shipped': '模拟配送中', 'delivered': '模拟已签收',
               'cancelled': '模拟已取消', 'returned': '模拟已退货', 'refunded': '模拟已退款'}


def utc_now():
    return datetime.now(timezone.utc)


def return_eligibility(order, items):
    # Canonical DateTime values are UTC; SQLite removes the offset on retrieval.
    code, reason = None, '订单已签收，按商品和七日期限判断模拟退货资格。'
    if order.status != 'delivered':
        code, reason = 'NOT_DELIVERED', '订单还没有签收，签收后才能申请退货。'
    elif order.delivered_at is None:
        code, reason = 'DELIVERY_TIME_UNKNOWN', '签收时间未知，无法确定退货期限。'
    else:
        delivered = order.delivered_at
        if delivered.tzinfo is None:
            delivered = delivered.replace(tzinfo=timezone.utc)
        if utc_now() - delivered > timedelta(days=7):
            code, reason = 'RETURN_WINDOW_EXPIRED', '已超过签收后的七天退货期限。'
    results = []
    for item in items:
        item_code, item_reason = code, reason
        if item_code is None:
            if item['returnable'] is None:
                item_code, item_reason = 'POLICY_UNKNOWN', '此商品退货政策未知，不能确认符合资格。'
            elif not item['returnable']:
                item_code, item_reason = 'NOT_RETURNABLE', '此商品不支持当前无理由退货；质量问题可另行登记。'
            else:
                item_reason = '可以申请此商品整行模拟退货；未提交申请。'
        eligible = item_code is None
        results.append({'item_id': item['sku_id'], 'product_name': item['name'],
                        'eligible': eligible, 'reason_code': item_code, 'reason': item_reason,
                        'refund_amount': f"{item['unit_price_fen'] * item['quantity'] / 100:.2f}" if eligible else None})
    return {'order_id': order.order_id, 'order_eligible': code is None,
            'reason_code': code, 'reason': reason, 'items': results}


class MercuryOrderService:
    def __init__(self, sessions):
        self.sessions = sessions

    def list_orders(self, owner_id):
        with self.sessions() as db:
            orders = db.query(SimulatedOrder).filter_by(owner_id=owner_id).order_by(
                SimulatedOrder.created_at.desc(), SimulatedOrder.order_id).all()
            return [{'order_id': row.order_id, 'store_id': row.store_id, 'version': row.version, 'status': row.status,
                     'status_text': STATUS_TEXT[row.status], 'created_at': row.created_at.isoformat(),
                     'total': f'{row.total_fen / 100:.2f}',
                     'products': [item['name'] for item in json.loads(row.snapshot_json)['items']]}
                    for row in orders]

    def read(self, name, owner_id, order_id):
        with self.sessions() as db:
            order = db.query(SimulatedOrder).filter_by(owner_id=owner_id, order_id=order_id).first()
            if order is None:
                return {'ok': False, 'error': 'ORDER_NOT_FOUND', 'message': '没有找到这个订单'}
            snapshot = json.loads(order.snapshot_json)
            from app.mercury.aftersales_models import AfterSalesApplication
            applications = db.query(AfterSalesApplication).filter_by(owner_id=owner_id, order_id=order_id).all()
            if name == 'get_order_details':
                data = {'order_id': order_id, 'store_id': order.store_id, 'version': order.version,
                        'status': order.status, 'status_text': STATUS_TEXT[order.status],
                        'created_at': order.created_at.isoformat(),
                        'delivered_at': order.delivered_at.isoformat() if order.delivered_at else None,
                        'total': f'{order.total_fen / 100:.2f}',
                        'items': [{'item_id': item['sku_id'], 'product_name': item['name'],
                                   'quantity': item['quantity'], 'unit_price': f"{item['unit_price_fen'] / 100:.2f}",
                                   'returnable': item['returnable'], 'return_policy_source': item['return_policy_source']}
                                  for item in snapshot['items']]}
            elif name == 'get_delivery_status':
                data = {'order_id': order_id, 'has_delivery': False,
                        'order_status': order.status, 'order_status_text': STATUS_TEXT[order.status]}
            elif name == 'check_refund_eligibility':
                eligible = order.status in ('submitted', 'paid') and not applications
                code = None if eligible else ('ALREADY_REQUESTED' if applications else ('ORDER_CANCELLED' if order.status == 'cancelled' else 'ALREADY_SHIPPED'))
                data = {'order_id': order_id, 'eligible': eligible, 'reason_code': code,
                        'reason': '可以申请模拟整单退款；这只是资格查询，未提交申请。' if eligible else '此订单状态不支持未发货仅退款。',
                        'amount': f'{order.total_fen / 100:.2f}' if eligible else None}
            elif name == 'check_return_eligibility':
                data = return_eligibility(order, snapshot['items'])
                for item in data['items']:
                    if any(row.kind == 'refund' or row.item_scope == item['item_id'] for row in applications):
                        item.update(eligible=False, reason_code='ALREADY_REQUESTED', reason='此商品已有售后申请，请查看模拟回执。', refund_amount=None)
            elif name in ('get_refund_status', 'get_return_status'):
                from app.mercury.aftersales_models import AfterSalesReceipt, AfterSalesApplication
                kind = 'refund' if name == 'get_refund_status' else 'return'
                data = [json.loads(receipt.result_json) for receipt in db.query(AfterSalesReceipt)
                    .join(AfterSalesApplication, AfterSalesReceipt.application_id == AfterSalesApplication.application_id)
                    .filter(AfterSalesReceipt.owner_id == owner_id, AfterSalesApplication.order_id == order_id,
                            AfterSalesApplication.kind == kind)]
            else:
                raise ValueError(f'Unsupported canonical read: {name}')
            return {'ok': True, 'data': data}

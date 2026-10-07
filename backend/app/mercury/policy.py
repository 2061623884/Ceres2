"""Static, versioned query policy facts; no demo database dependency."""
# Rules selectively carried from the user's Mercury seed; all fulfillment remains simulated.
POLICY_SOURCE_VERSION = '2026-10-06'
POLICIES = [
    ('P-REF-01', 'refund', '未发货订单退款',
     '未发货订单可申请整单模拟退款；已发货或已签收的订单不支持仅退款，签收后可查询退货资格。',
     '退款,取消,不想要,未发货,仅退款'),
    ('P-RET-01', 'return', '签收后退货',
     '签收后 7 天内，可退货商品可按单明细整行申请模拟退货退款。超过七天或标记不可退货的商品不符合该规则；签收时间或商品可退货标记未知时，不能确认资格。',
     '退货,七天,7天,签收'),
    ('P-RET-02', 'return', '不支持退货的商品',
     '生鲜等标注“不可退货”的商品不支持退货；规则未知时不能确认符合资格。',
     '生鲜,水果,不能退,不支持退货,不可退'),
    ('P-DEL-01', 'delivery', '模拟配送信息',
     '模拟配送进度以订单业务记录为准，缺少物流记录时不能推测送达时间；没有真实履约。',
     '配送,送达,多久送到,几点到,延迟,还没到'),
]


def search_policies(query, category=None):
    rows = [row for row in POLICIES if category is None or row[1] == category]
    scored = [(sum(keyword in query for keyword in row[4].split(',')), row) for row in rows]
    scored.sort(key=lambda pair: -pair[0])
    hits = [row for score, row in scored if score][:3]
    if not hits and category:
        hits = rows
    return {'ok': True, 'data': [{
        **dict(zip(('policy_id', 'category', 'title', 'content'), row[:4])),
        'source': {'name': 'Ceres 模拟售后规则', 'version': POLICY_SOURCE_VERSION, 'policy_id': row[0]},
    } for row in hits]}


def policy_summary(data):
    if not data:
        return '未找到匹配的售后政策，规则未知，无法据此判断资格；未提交任何申请。'
    facts = '；'.join(
        f"{item['title']}：{item['content']} 来源：{item['source']['name']} "
        f"{item['source']['policy_id']}（版本 {item['source']['version']}）"
        for item in data)
    return facts + '；以上是一般政策，具体订单资格尚未核实；未提交任何申请。'

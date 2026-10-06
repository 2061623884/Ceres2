"""Read-only order-service adapter. Owner and selection come from the host."""
import json

from app.mercury import policy

CLARIFICATIONS = {
    'query_topic': '请说明要查询订单、物流、退款资格、退货资格还是政策。',
    'item': '请说明要咨询订单中的哪件商品。',
    'reason': '请说明申请退款或退货的原因。',
}

READS = ('get_order_details', 'get_delivery_status', 'check_refund_eligibility',
         'check_return_eligibility', 'get_refund_status', 'get_return_status')


def schemas():
    tools = [{"type": "function", "function": {
        "name": name, "description": "只读查询当前选定模拟订单，不提交任何申请。",
        "parameters": {"type": "object", "properties": {
            "order_id": {"type": "string"}}, "required": ["order_id"]}
    }} for name in READS]
    tools.append({"type": "function", "function": {
        "name": "search_after_sales_policy", "description": "检索现有售后政策原文。",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "minLength": 1},
            "category": {"type": "string", "enum": ["refund", "return", "delivery"]}},
            "required": ["query"]}
    }})
    tools.append({"type": "function", "function": {
        "name": "request_clarification", "description": "信息不足时暂停并询问所缺字段，不表示授权或业务结果。",
        "parameters": {"type": "object", "properties": {
            "slot": {"type": "string", "enum": list(CLARIFICATIONS)}},
            "required": ["slot"], "additionalProperties": False}
    }})
    tools.append({"type": "function", "function": {
        "name": "prepare_aftersales_proposal", "description": "仅在用户要求申请退款或退货时准备具体提案，不提交申请；纯资格查询使用查询工具。",
        "parameters": {"type": "object", "properties": {
            "order_id": {"type": "string"}, "kind": {"type": "string", "enum": ["refund", "return"]},
            "item_id": {"type": ["string", "null"]}, "reason": {"type": "string", "minLength": 1, "maxLength": 1000}},
            "required": ["order_id", "kind", "reason"], "additionalProperties": False}
    }})
    from app.schemas.memory import memory_tool_schema
    tools.append(memory_tool_schema())
    return tools


def execute(name, arguments, *, owner_id, order_id, order_service):
    if name not in READS and name not in ("search_after_sales_policy", "request_clarification"):
        return {"ok": False, "error": "READ_ONLY", "message": "当前仅支持查询，未提交任何申请。"}
    try:
        args = json.loads(arguments)
    except (ValueError, TypeError):
        return {"ok": False, "error": "BAD_ARGUMENTS", "message": "查询参数不合法。"}
    if not isinstance(args, dict):
        return {"ok": False, "error": "BAD_ARGUMENTS", "message": "查询参数必须是对象。"}
    if name == "request_clarification":
        if args.get("slot") not in CLARIFICATIONS or set(args) != {"slot"}:
            return {"ok": False, "error": "BAD_ARGUMENTS", "message": "澄清字段不合法。"}
        return {"ok": True, "data": {"slot": args["slot"]}}
    if name == "search_after_sales_policy":
        if (not isinstance(args.get("query"), str) or not args["query"].strip()
                or ("category" in args and args["category"] not in ("refund", "return", "delivery"))):
            return {"ok": False, "error": "BAD_ARGUMENTS", "message": "政策查询问题或类别不合法。"}
        return policy.search_policies(args["query"], args.get("category"))
    if args.get("order_id") != order_id:
        return {"ok": False, "error": "ORDER_NOT_FOUND", "message": "请先选择要查询的订单。"}
    return order_service.read(name, owner_id, order_id)


def fact_summary(name, data):
    """Render business facts without unverified model claims."""
    if name == "get_order_details":
        items = "、".join(f"{item['product_name']} × {item['quantity']}" for item in data['items'])
        return f"订单 {data['order_id']}：{data['status_text']}，{data['total']} 元；商品：{items}"
    if name == "get_delivery_status":
        if data["has_delivery"]:
            return f"订单 {data['order_id']} 物流：{data['status_text']}"
        return f"订单 {data['order_id']}：{data['order_status_text']}；暂无独立物流记录，无法确认送达时间"
    if name == "check_refund_eligibility":
        amount = f"预计模拟金额 {data['amount']} 元" if data['eligible'] else ""
        return f"订单 {data['order_id']} 退款资格：{data['reason']} {amount}"
    if name == "check_return_eligibility":
        items = "；".join(f"{item['product_name']}：{item['reason']}" for item in data['items'])
        return f"订单 {data['order_id']} 退货资格：{data['reason']} {items}"
    if name == "get_refund_status":
        return f"当前有 {len(data)} 条模拟退款申请进度记录"
    if name == "get_return_status":
        return f"当前有 {len(data)} 条模拟退货申请进度记录"
    if not data:
        return "未找到匹配的售后政策，无法据此判断资格"
    return "；".join(f"{item['title']}：{item['content']}" for item in data)


def policy_indeterminate(name, data):
    """Only structured authoritative policy uncertainty can request review."""
    if name == "check_return_eligibility":
        return any(item['reason_code'] == 'POLICY_UNKNOWN' for item in data['items'])
    if name == "search_after_sales_policy":
        return not data
    return False


def proposal_arguments(arguments, order_id, selection_version):
    from app.core.errors import AppError
    try:
        args = json.loads(arguments)
    except (ValueError, TypeError) as error:
        raise AppError(422, 'BAD_ARGUMENTS', '申请提案参数不合法') from error
    if (not isinstance(args, dict) or set(args) - {'order_id','kind','item_id','reason'}
        or args.get('order_id') != order_id or args.get('kind') not in ('refund','return')
        or not isinstance(args.get('reason'),str) or not args['reason'].strip() or len(args['reason']) > 1000
        or (args.get('item_id') is not None and not isinstance(args['item_id'],str))):
        raise AppError(422, 'BAD_ARGUMENTS', '请明确当前订单、售后类型、商品和原因')
    return {'kind':args['kind'],'item_id':args.get('item_id'),'reason':args['reason'],
            'selection_version':selection_version}


def proposal_summary(preview):
    items = '、'.join(f"{item['name']} × {item['quantity']}" for item in preview['items'])
    return (f"待确认模拟{'整单退款' if preview['kind'] == 'refund' else '整行退货'}提案：订单 {preview['order_id']}；"
            f"{items}；预计金额 {preview['amount_fen']/100:.2f} 元；原因：{preview['reason']}；"
            f"政策 {preview['policy_id']}：{preview['policy']} 请查看提案后点击确认提交。未提交任何申请。")

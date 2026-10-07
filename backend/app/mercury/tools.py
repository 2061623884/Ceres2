"""Read-only order-service adapter. Owner and selection come from the host."""
import json

from app.mercury import policy

CLARIFICATIONS = {
    'query_topic': '请说明要查询订单、物流、退款资格、退货资格还是政策。',
    'item': '请说明要咨询订单中的哪件商品。',
    'reason': '请说明售后申请的原因。',
    'problem_quantity': '这件商品有几个销售包装存在问题？请按订单中的包装件数说明。',
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
        "name": "search_after_sales_policy", "description": "无需选择订单，检索一般售后政策及来源。政策不证明具体订单资格，不授权申请。",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "minLength": 1},
            "category": {"type": "string", "enum": list(policy.CATEGORIES)}},
            "required": ["query"]}
    }})
    tools.append({"type": "function", "function": {
        "name": "request_clarification", "description": "信息不足时暂停并询问所缺字段，不表示授权或业务结果。",
        "parameters": {"type": "object", "properties": {
            "slot": {"type": "string", "enum": list(CLARIFICATIONS)}},
            "required": ["slot"], "additionalProperties": False}
    }})
    tools.append({"type": "function", "function": {
        "name": "prepare_aftersales_proposal", "description": "用户明确要求申请时才准备提案，不提交。refund是未发货整单退款；return是无理由整行退货；quality是签收后的质量问题登记；fulfillment是签收后的漏送错送或包装破损登记。后两者按问题销售包装数交人工核对，不受不可无理由退货标记拒绝，必须给明确item_id和problem_quantity；不知道数量先询问。纯资格查询使用查询工具。",
        "parameters": {"type": "object", "properties": {
            "order_id": {"type": "string"}, "kind": {"type": "string", "enum": ["refund", "return", "quality", "fulfillment"]},
            "problem_quantity": {"type": "integer", "minimum": 1},
            "item_id": {"type": ["string", "null"], "description": "无理由退货、质量或履约登记时填写用户明确选择的订单商品；整单退款必须省略或设为null。"}, "reason": {"type": "string", "minLength": 1, "maxLength": 1000}},
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
                or ("category" in args and args["category"] not in policy.CATEGORIES)):
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
    return policy.policy_summary(data)


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
    if not isinstance(args, dict) or args.get('order_id') != order_id:
        raise AppError(422, 'BAD_ARGUMENTS', '请明确当前订单、售后类型、商品和原因')
    from pydantic import ValidationError
    from app.mercury.router import ProposalRequest
    try:
        return ProposalRequest.model_validate({**{key:value for key,value in args.items() if key != 'order_id'}, 'selection_version':selection_version}).model_dump()
    except ValidationError as error:
        raise AppError(422, 'BAD_ARGUMENTS', '请明确当前订单、售后类型、商品、问题包装数和原因') from error


def proposal_summary(preview):
    items = '、'.join(f"{item['name']} × {item['quantity']}" for item in preview['items'])
    label = {'refund':'整单退款', 'return':'整行退货', 'quality':'质量问题登记', 'fulfillment':'履约异常登记'}[preview['kind']]
    return (f"待确认模拟{label}提案：订单 {preview['order_id']}；"
            f"{items}；预计金额 {preview['amount_fen']/100:.2f} 元；原因：{preview['reason']}；"
            f"政策 {preview['policy_id']}：{preview['policy']} 请查看提案后点击确认提交。未提交任何申请。")

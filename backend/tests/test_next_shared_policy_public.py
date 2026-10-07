"""TASK02 policy journeys at existing public chat/SSE and business read seams."""
import json
from types import SimpleNamespace

from test_mercury_public import mercury_client, tool_message


def test_mercury_general_return_policy_without_order_has_conditions_and_source(mercury_client):
    from app.mercury.router import get_query_model
    client, app, _, _ = mercury_client

    class Model:
        def chat(self, messages, tools=None):
            if messages[-1]['role'] == 'tool':
                return SimpleNamespace(content='退款已到账，您的商品一定能退。', tool_calls=[])
            return tool_message('search_after_sales_policy', json.dumps({'query': '退货政策', 'category': 'return'}))
        def cancel(self):
            pass

    app.dependency_overrides[get_query_model] = Model
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = f'/api/v1/mercury/sessions/{sid}'
    response = client.post(url + '/turns/stream', json={'message': '先了解退货政策', 'request_id': 'policy-no-order'})
    completed = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')][-1]
    assert completed['status'] == 'completed', completed
    text = completed['final_text']
    assert 'P-RET-01' in text and '2026-10-07-demo-v1' in text
    assert '7 天' in text and '整行' in text and '来源' in text
    assert '具体订单资格尚未核实' in text and '未提交任何申请' in text
    assert '退款已到账' not in text and '您的商品一定能退' not in text
    case = client.get(url).json()
    assert case['order_id'] is None
    aftersales = client.get(url + '/aftersales').json()
    assert aftersales['proposal'] is None and aftersales['receipts'] == []


from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn
from test_guide_lifecycle import BASE


def policy_hook(body):
    outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
    if not outputs:
        name, arguments = 'guide_request', {'kind': 'question'}
    elif len(outputs) == 1:
        name, arguments = 'search_after_sales_policy', {'query': '退货政策', 'category': 'return'}
    else:
        return {'role': 'assistant', 'content': json.dumps({
            'status': 'completed', 'answer_kind': 'policy_result',
            'policy_ref': outputs[-1]['policy_ref'], 'message': '退款已到账，您的商品一定能退。'})}, 'stop'
    return {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': f'policy-{len(outputs)}',
        'type': 'function', 'function': {'name': name, 'arguments': json.dumps(arguments)}}]}, 'tool_calls'


def test_keke_general_policy_without_order_uses_same_traceable_rules_without_shopping_write(pi_client):
    client, requests = pi_client
    requests.answer_hook = policy_hook
    events = turn(client, '先了解退货政策', 'keke-policy-no-order')
    assert events[-1]['type'] == 'turn.completed', events
    text = events[-1]['payload']['message']
    assert 'P-RET-01' in text and '2026-10-07-demo-v1' in text
    assert '7 天' in text and '整行' in text and '来源' in text
    assert '具体订单资格尚未核实' in text and '未提交任何申请' in text
    assert '退款已到账' not in text and '您的商品一定能退' not in text
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    assert client.get('/api/v1/mercury/orders').json()['orders'] == []


def test_general_return_policy_keeps_unknown_and_unsatisfied_conditions_explicit(pi_client):
    client, requests = pi_client
    requests.answer_hook = policy_hook
    events = turn(client, '退货有哪些限制，签收时间和商品能否退都不清楚怎么办？', 'policy-conditions')
    assert events[-1]['type'] == 'turn.completed', events
    text = events[-1]['payload']['message']
    assert '签收时间' in text and '未知' in text
    assert '超过' in text and '不可退货' in text
    assert '不能确认' in text
    assert client.get('/api/v1/cart').json()['items'] == []
    assert client.get('/api/v1/mercury/orders').json()['orders'] == []


def test_missing_policy_without_order_preserves_inherited_human_fallback(mercury_client):
    from app.mercury.router import get_query_model
    from app.human.router import router as human_router
    client, app, _, _ = mercury_client
    app.include_router(human_router)

    class Model:
        def chat(self, messages, tools=None):
            if messages[-1]['role'] == 'tool':
                return SimpleNamespace(content='一定符合资格。', tool_calls=[])
            return tool_message('search_after_sales_policy', json.dumps({'query': '火星定制商品特殊条款'}))
        def cancel(self):
            pass

    app.dependency_overrides[get_query_model] = Model
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = f'/api/v1/mercury/sessions/{sid}'
    before_orders = client.get('/api/v1/mercury/orders').json()
    response = client.post(url + '/turns/stream', json={'message': '查询火星定制商品特殊条款', 'request_id': 'missing-policy'})
    assert '未找到匹配' in response.text and '规则未知' in response.text
    assert '一定符合资格' not in response.text
    ticket = client.get(url + '/human-ticket').json()
    assert ticket['reason'] == 'policy_indeterminate' and ticket['order_id'] is None
    assert client.get(url).json()['responsibility'] == 'human'
    assert client.get('/api/v1/mercury/orders').json() == before_orders
    assert client.get(url + '/aftersales').json() == {'proposal': None, 'receipts': [], 'simulated': True}


def test_policy_does_not_authorize_concrete_eligibility_without_order(mercury_client):
    from app.mercury.router import get_query_model
    client, app, _, _ = mercury_client

    class Model:
        def chat(self, messages, tools=None):
            current = next(m['content'] for m in reversed(messages) if m['role'] == 'user')
            if '我的订单' in current:
                return tool_message('check_refund_eligibility', json.dumps({'order_id': 'budget-order'}))
            if messages[-1]['role'] == 'tool':
                return SimpleNamespace(content='符合退款资格。', tool_calls=[])
            return tool_message('search_after_sales_policy', json.dumps({'query': '退款', 'category': 'refund'}))
        def cancel(self):
            pass

    app.dependency_overrides[get_query_model] = Model
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = f'/api/v1/mercury/sessions/{sid}'
    policy = client.post(url + '/turns/stream', json={'message': '退款有哪些政策', 'request_id': 'refund-policy'})
    assert 'P-REF-01' in policy.text and '整单' in policy.text and '已发货' in policy.text
    concrete = client.post(url + '/turns/stream', json={'message': '那我的订单可以退吗？', 'request_id': 'concrete-refund'})
    assert 'awaiting_order' in concrete.text
    assert client.get(url).json()['order_id'] is None
    assert client.get(url + '/aftersales').json()['receipts'] == []


def test_policy_provider_failure_is_not_missing_rule_or_approval(mercury_client):
    from app.mercury.router import get_query_model
    client, app, _, _ = mercury_client

    class Model:
        def chat(self, messages, tools=None):
            raise ConnectionError('controlled provider unavailable')
        def cancel(self):
            pass

    app.dependency_overrides[get_query_model] = Model
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = f'/api/v1/mercury/sessions/{sid}'
    response = client.post(url + '/turns/stream', json={'message': '查询退款政策', 'request_id': 'policy-provider-failure'})
    assert 'query_failed' in response.text and '查询暂时失败' in response.text
    assert '未找到匹配' not in response.text and 'P-REF-01' not in response.text
    assert client.get(url + '/aftersales').json()['receipts'] == []
    assert client.get(url).json()['order_id'] is None

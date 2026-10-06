"""TASK09: fresh canonical checkout, explicit aftersales and chosen shopping return."""
from test_order_case_journey import journey, checkout


def selected_case(client, order):
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = '/api/v1/mercury/sessions/' + sid
    selected = client.put(url + '/order', json={'order_id': order['order_id'], 'selection_version': 0})
    assert selected.status_code == 200, selected.text
    return url


def return_to_shopping(client):
    guide = client.post('/api/v1/guide/sessions', json={'entry_context': {
        'page': 'home', 'store_id': 'store-default', 'delivery_zone_id': 'zone-default'}}).json()
    base = '/api/v1/navigation/sessions/' + guide['session_id']
    opening = client.post(base + '/opening', json={'role': 'momo'}).json()
    result = client.post(base + '/switches', json={'opening_id': opening['opening_id'],
        'target_role': 'keke', 'accept': True})
    assert result.status_code == 200 and result.json()['role'] == 'keke'
    assert result.json()['handoff'] is None
    return base, opening


def test_denied_application_survives_user_chosen_shopping_return(journey):
    client, make_client = journey
    order = checkout(client)
    url = selected_case(client, order)
    # A newly checked-out, unshipped order is outside delivered-line return policy.
    denied = client.post(url + '/proposals', json={'kind': 'return',
        'item_id': order['items'][0]['sku_id'], 'reason': '想换另一款', 'selection_version': 1})
    assert denied.status_code == 409, denied.text
    failure = client.get(url).json()['messages']
    assert failure, 'A rejected application must remain visible after leaving Mercury'
    assert order['order_id'] in failure[-1]['content']
    assert '未提交' in failure[-1]['content']
    assert client.get(url + '/aftersales').json()['receipts'] == []
    return_to_shopping(client)
    # Shopping does not hide a failed request, retry it, or mutate its order.
    cart = client.get('/api/v1/cart').json()
    client.post('/api/v1/cart/items', json={'sku_id': 'demo:flour-all-purpose-500g',
        'quantity': 1, 'expected_cart_version': cart['version']})
    assert client.get(url).json()['messages'] == failure
    assert client.get('/api/v1/orders/' + order['order_id']).json() == order
    with make_client() as restarted:
        restarted.cookies.set('sg_owner_id', client.cookies.get('sg_owner_id'))
        assert restarted.get(url).json()['messages'] == failure
        assert restarted.get(url + '/aftersales').json()['receipts'] == []


import json
from types import SimpleNamespace
from test_runtime_pi_product_query import pi_client
from test_purchase_public import prepare, confirmation_body
from test_next_snack_public import seed_snacks
from test_guide_lifecycle import BASE


def test_purchase_checkout_application_then_explicit_compound_return_requeries_goods(
        pi_client, controlled_kev_transport, tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.mercury.router import get_query_model
    monkeypatch.setattr(get_settings(), 'mercury_checkpoint_path', tmp_path / 'journey-checkpoints.sqlite3')
    client, requests = pi_client
    seed_snacks(requests)
    state = prepare(client, requests)
    assert client.get('/api/v1/orders').json()['items'] == []
    cart_confirm = client.post('/api/v1/guide/tasks/' + state['task_id'] + '/confirm',
        json=confirmation_body(state), headers={'Idempotency-Key': 'journey-cart'})
    assert cart_confirm.status_code == 200, cart_confirm.text
    # Selecting and confirming a plan cannot itself create a checkout order.
    assert client.get('/api/v1/orders').json()['items'] == []
    cart = client.get('/api/v1/cart').json()
    preview = client.post('/api/v1/checkout/preview', json={'expected_cart_version': cart['version']}).json()
    checkout_body = {'preview_id': preview['preview_id'], 'idempotency_key': 'journey-checkout', 'confirmed': True}
    saved = client.post('/api/v1/checkout/confirm', json=checkout_body)
    assert saved.status_code == 200, saved.text
    order = saved.json()['order']
    assert client.post('/api/v1/checkout/confirm', json=checkout_body).json() == saved.json()
    url = selected_case(client, order)
    navigation = '/api/v1/navigation/sessions/pi-session-a'
    opening = client.get(navigation + '/opening').json()
    assert client.post(navigation + '/switches', json={'opening_id': opening['opening_id'],
        'target_role': 'momo', 'accept': True}).status_code == 200
    queried = []
    class Model:
        def chat(self, messages, tools=None):
            if messages[-1]['role'] == 'tool':
                queried.append(json.loads(messages[-1]['content']))
                return SimpleNamespace(content='已查询', tool_calls=[])
            return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='eligibility', function=SimpleNamespace(
                name='check_refund_eligibility', arguments=json.dumps({'order_id': order['order_id']})))])
        def cancel(self):
            pass
    client.app.dependency_overrides[get_query_model] = Model
    query = client.post(url + '/turns/stream', json={'message': '查询这笔新订单的退款资格', 'request_id': 'journey-eligibility'})
    assert query.status_code == 200 and 'turn.completed' in query.text, query.text
    assert queried and queried[-1]['data']['order_id'] == order['order_id']
    assert client.get(url + '/aftersales').json()['receipts'] == []
    proposal = client.post(url + '/proposals', json={'kind': 'refund', 'item_id': None,
        'reason': '想换一种零食', 'selection_version': 1}).json()
    assert proposal['order_id'] == order['order_id']
    assert proposal['amount_fen'] == order['total_fen']
    assert client.get(url + '/aftersales').json()['receipts'] == []
    confirmation = {'proposal_id': proposal['proposal_id'], 'idempotency_key': proposal['proposal_id'], 'confirmed': True}
    applied = client.post(url + '/confirm', json=confirmation)
    assert applied.status_code == 200, applied.text
    receipt = applied.json()
    assert receipt['status'] == 'requested' and '尚未审批或退款到账' in receipt['message']
    assert client.post(url + '/confirm', json=confirmation).json() == receipt
    original_order = client.get('/api/v1/orders/' + order['order_id']).json()
    navigation = '/api/v1/navigation/sessions/pi-session-a'
    opening = client.get(navigation + '/opening').json()
    assert client.post(navigation + '/switches', json={'opening_id': opening['opening_id'],
        'target_role': 'momo', 'accept': True}).status_code == 200
    controlled_kev_transport['choose'] = lambda _: 'return_keke_exploration'
    original = '回到购物，换一种零食，预算二十元'
    calls_before = len(controlled_kev_transport['calls'])
    routed = client.post(navigation + '/routes', json={'opening_id': opening['opening_id'], 'request_id': 'journey-return',
        'role': 'momo', 'message': original, 'role_session_id': url.split('/')[-1],
        'selected_object': {'kind': 'order', 'id': order['order_id']}})
    assert routed.status_code == 200, routed.text
    assert routed.json()['continue_original'] is True
    assert routed.json()['original_message'] == original
    assert routed.json()['selected_object'] == {'kind': 'order', 'id': order['order_id']}
    def replacement(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            name, args = ('guide_request', {'kind': 'new_goal', 'goal': '替换为零食', 'conditions': {'budget_fen': 2000}}) if not outputs else ('explore_products', {'category_id': 'snack'})
            return {'role': 'assistant', 'tool_calls': [{'index': 0, 'id': f'replacement-{len(outputs)}',
                'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args)}}]}, 'tool_calls'
        return {'role': 'assistant', 'content': json.dumps({'status': 'completed', 'answer_kind': 'exploration',
            'exploration_ref': outputs[-1]['exploration_ref']})}, 'stop'
    requests.answer_hook = replacement
    current = client.get(BASE).json()
    body = {'request_id': 'journey-return', 'routing_request_id': 'journey-return', 'message': original,
        'expected_task_id': current['task_id'], 'expected_state_version': current['state_version'],
        'expected_session_version': current['session_version']}
    continued = client.post(BASE + '/turns/stream', json=body)
    events = [json.loads(line[6:]) for line in continued.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    assert events[-1]['payload']['active_question']['kind'] == 'category'
    assert client.get(BASE).json()['conditions']['budget_fen'] == 2000
    assert len(controlled_kev_transport['calls']) == calls_before + 1
    assert client.get('/api/v1/cart').json()['items'] == []
    assert client.get(url + '/aftersales').json()['receipts'] == [receipt]
    assert client.get('/api/v1/orders/' + order['order_id']).json() == original_order
    assert client.post(url + '/confirm', json=confirmation).json() == receipt


def prepare_refund(client, url):
    response = client.post(url + '/proposals', json={'kind': 'refund', 'item_id': None,
        'reason': '换一种商品', 'selection_version': 1})
    assert response.status_code == 200, response.text
    return response.json()


def apply_refund(client, url, proposal):
    return client.post(url + '/confirm', json={'proposal_id': proposal['proposal_id'],
        'idempotency_key': proposal['proposal_id'], 'confirmed': True})


def test_precommit_failure_is_retained_without_erasing_valid_proposal_or_retrying(journey, monkeypatch):
    import pytest
    from app.mercury.aftersales import AfterSalesService
    client, _ = journey
    order = checkout(client)
    url = selected_case(client, order)
    proposal = prepare_refund(client, url)
    calls = []
    def fail(*args):
        calls.append(True)
        raise RuntimeError('private provider fault must never reach persisted narration')
    with monkeypatch.context() as patch:
        patch.setattr(AfterSalesService, 'submit', fail)
        with pytest.raises(RuntimeError):
            apply_refund(client, url, proposal)
    aftersales = client.get(url + '/aftersales').json()
    assert aftersales['proposal']['proposal_id'] == proposal['proposal_id']
    assert aftersales['receipts'] == []
    failure = client.get(url).json()['messages'][-1]['content']
    assert '服务暂时失败' in failure and '未提交' in failure and '暂停' in failure
    assert 'private provider' not in failure
    return_to_shopping(client)
    assert calls == [True]
    assert client.get(url).json()['messages'][-1]['content'] == failure
    assert client.get(url + '/aftersales').json() == aftersales


def test_postcommit_response_loss_records_receipt_truth_and_replays_once(journey, monkeypatch):
    import pytest
    from app.mercury.aftersales import AfterSalesService
    client, _ = journey
    order = checkout(client)
    url = selected_case(client, order)
    proposal = prepare_refund(client, url)
    submit = AfterSalesService.submit
    def lost_response(self, *args):
        submit(self, *args)
        raise RuntimeError('private response failure')
    with monkeypatch.context() as patch:
        patch.setattr(AfterSalesService, 'submit', lost_response)
        with pytest.raises(RuntimeError):
            apply_refund(client, url, proposal)
    saved = client.get(url + '/aftersales').json()
    assert saved['proposal'] is None and len(saved['receipts']) == 1
    notice = client.get(url).json()['messages'][-1]['content']
    assert saved['receipts'][0]['receipt_id'] in notice
    assert '尚未审批或退款到账' in notice and '本次申请未提交' not in notice
    return_to_shopping(client)
    assert apply_refund(client, url, proposal).json() == saved['receipts'][0]
    assert client.get(url + '/aftersales').json() == saved


def test_foreign_invalid_and_stale_requests_do_not_write_failure_history(journey):
    client, _ = journey
    order = checkout(client)
    url = selected_case(client, order)
    proposal = prepare_refund(client, url)
    before = client.get(url).json()
    assert client.post(url + '/proposals', json={'kind': 'return', 'item_id': None,
        'reason': '无商品', 'selection_version': 1}).status_code == 422
    assert client.post(url + '/proposals', json={'kind': 'refund', 'item_id': None,
        'reason': '旧选择', 'selection_version': 0}).status_code == 409
    assert client.post(url + '/confirm', json={'proposal_id': 'foreign-proposal',
        'idempotency_key': 'foreign', 'confirmed': True}).status_code == 404
    assert client.get(url).json() == before
    assert client.get(url + '/aftersales').json()['proposal']['proposal_id'] == proposal['proposal_id']
    owner = client.cookies.get('sg_owner_id')
    client.cookies.clear(); client.get('/api/v1/bootstrap')
    assert apply_refund(client, url, proposal).status_code == 404
    assert client.post(url + '/proposals', json={'kind': 'refund', 'item_id': None,
        'reason': '其他身份', 'selection_version': 1}).status_code == 404
    client.cookies.clear(); client.cookies.set('sg_owner_id', owner)
    assert client.get(url).json() == before


def test_human_responsibility_survives_shopping_and_blocks_application(journey):
    client, _ = journey
    order = checkout(client)
    url = selected_case(client, order)
    proposal = prepare_refund(client, url)
    ticket = client.post(url + '/human-ticket', json={'summary': '请人工处理此事项'})
    assert ticket.status_code == 200, ticket.text
    held = client.get(url).json()
    assert held['responsibility'] == 'human'
    assert apply_refund(client, url, proposal).status_code == 409
    return_to_shopping(client)
    restored = client.get(url).json()
    assert restored['responsibility'] == 'human'
    assert restored['responsibility_generation'] == held['responsibility_generation']
    assert client.get(url + '/human-ticket').json()['ticket_id'] == ticket.json()['ticket_id']
    assert client.get(url + '/aftersales').json()['receipts'] == []
    assert apply_refund(client, url, proposal).status_code == 409

"""TASK16 full public journeys: actual Pi/LangGraph, controlled model only.

Fresh pi_client data is built in tmp_path; no archived database is consumed.
Domain clock is fixed at NOW for checkout, human correspondence and eligibility.
Runtime admission/monotonic cancellation clocks remain real intentionally.
"""
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Event
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from app.core.config import get_settings
from app.core.database import get_db, init_db
from app.main import create_app
from app.mercury import orders
from app.mercury.aftersales import AfterSalesService
from app.mercury.router import get_query_model
from test_runtime_pi_product_query import pi_client
from test_comparison_public import seed_multipack, comparison_hook, select_hook, posted_turn
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_multidish_public import confirm_body
from test_aftersales_public import confirm, proposal

NOW = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)


@pytest.fixture
def lifecycle(pi_client, tmp_path, monkeypatch):
    client, requests = pi_client
    from app.services import checkout_service
    from app.human import service as human_service
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW if tz else NOW.replace(tzinfo=None)
    monkeypatch.setattr(checkout_service, 'datetime', FixedDatetime)
    monkeypatch.setattr(human_service, 'datetime', FixedDatetime)
    monkeypatch.setattr(orders, 'utc_now', lambda: NOW)
    monkeypatch.setattr(get_settings(), 'mercury_checkpoint_path', tmp_path / 'graph.sqlite3')
    monkeypatch.setattr(get_settings(), 'human_operator_token', 'task16-synthetic-operator')
    yield client, requests


def compared_order(client, requests):
    seed_multipack(requests)
    command(client, 'new_goal', goal='比较可乐后选一款')
    requests.answer_hook = comparison_hook
    compared = turn(client, '比较饮料', 'integrated-compare')
    assert compared[-1]['type'] == 'turn.completed', compared
    assert compared[-1]['payload']['runtime'] == 'pi-agent-core'
    cards = compared[-1]['payload']['product_cards']
    selected = next(card for card in cards if card['sku_id'] == 'pi-cola-six')
    requests.answer_hook = select_hook(selected['ref'])
    chosen = posted_turn(client, f"选候选 {selected['ref']} 一包，生成清单", 'integrated-select',
                         [card['ref'] for card in cards])
    assert chosen[-1]['type'] == 'turn.completed', chosen
    state = client.get(BASE).json()
    # Stopping an interleaved read must preserve the selected purchase plan.
    requests.answer_hook = None
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(turn, client, '受控慢查询可乐', 'integrated-stop')
        try:
            assert requests.started.wait(5)
            stopped = client.post(BASE + '/turns/stop', json={'request_id': 'integrated-stop'})
            assert stopped.status_code == 200 and stopped.json()['cancelled'] is True
            events = pending.result(timeout=5)
            assert events[-1]['type'] == 'turn.stopped', events
        finally:
            requests.release.set()
    restored = client.get(BASE).json()
    assert restored['plan'] == state['plan']
    assert restored['task_id'] == state['task_id']
    state = restored
    assert client.get('/api/v1/cart').json()['items'] == []
    response = client.post('/api/v1/guide/tasks/' + state['task_id'] + '/confirm',
                           json=confirm_body(state), headers={'Idempotency-Key': 'integrated-cart'})
    assert response.status_code == 200, response.text
    cart = client.get('/api/v1/cart').json()
    assert [(row['sku_id'], row['quantity']) for row in cart['items']] == [('pi-cola-six', 1)]
    preview = client.post('/api/v1/checkout/preview', json={'expected_cart_version': cart['version']})
    assert preview.status_code == 200, preview.text
    body = {'preview_id': preview.json()['preview_id'], 'idempotency_key': 'integrated-checkout', 'confirmed': True}
    checked = client.post('/api/v1/checkout/confirm', json=body)
    assert checked.status_code == 200, checked.text
    assert client.post('/api/v1/checkout/confirm', json=body).json() == checked.json()
    order = checked.json()['order']
    assert order['total_fen'] == 1800
    assert client.get('/api/v1/cart').json()['items'] == []
    assert client.get('/api/v1/mercury/orders').json()['orders'][0]['order_id'] == order['order_id']
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = '/api/v1/mercury/sessions/' + sid
    selected_order = client.put(url + '/order', json={'order_id': order['order_id'], 'selection_version': 0})
    assert selected_order.status_code == 200, selected_order.text
    return order, url


def model_proposal(client, order, url):
    class ControlledModel:
        def chat(self, messages, tools=None):
            return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='proposal', function=SimpleNamespace(
                name='prepare_aftersales_proposal', arguments=json.dumps({
                    'order_id': order['order_id'], 'kind': 'refund', 'reason': '不需要了'})))])
        def cancel(self):
            pass
    client.app.dependency_overrides[get_query_model] = ControlledModel
    streamed = client.post(url + '/turns/stream', json={'message': '我要退款，不需要了', 'request_id': 'integrated-refund'})
    assert streamed.status_code == 200 and 'awaiting_confirmation' in streamed.text, streamed.text
    saved = client.get(url + '/aftersales').json()
    assert saved['receipts'] == []
    assert saved['proposal']['order_id'] == order['order_id']
    assert saved['proposal']['amount_fen'] == 1800
    assert saved['proposal']['items'][0]['quantity'] == 1
    return saved['proposal']['proposal_id']


def test_comparison_checkout_same_order_graph_receipt_survives_loss_and_restart(lifecycle, monkeypatch):
    client, requests = lifecycle
    order, url = compared_order(client, requests)
    pid = model_proposal(client, order, url)
    submit = AfterSalesService.submit
    def response_lost(self, *args):
        submit(self, *args)
        raise RuntimeError('TASK16 approved postcommit response loss')
    with monkeypatch.context() as patch:
        patch.setattr(AfterSalesService, 'submit', response_lost)
        assert confirm(client, url, pid).status_code == 500
    saved = client.get(url + '/aftersales').json()
    assert len(saved['receipts']) == 1
    receipt = saved['receipts'][0]
    assert receipt['status'] == 'requested' and receipt['simulated'] is True
    init_db(requests.engine)
    init_db(requests.engine)
    assert client.get(url + '/aftersales').json() == saved
    get_settings().mercury_checkpoint_path.unlink()
    # Reconstruct the application/router and graph boundary, retaining only the
    # isolated business DB and trusted owner's cookie, with no lifespan writers.
    app = create_app(database_engine=requests.engine)
    app.dependency_overrides[get_db] = client.app.dependency_overrides[get_db]
    restarted = TestClient(app, raise_server_exceptions=False)
    try:
        restarted.cookies.set('sg_owner_id', 'pi-owner-a')
        assert restarted.get(url + '/aftersales').json() == saved
        assert confirm(restarted, url, pid).json() == receipt
        assert restarted.get('/api/v1/orders/' + order['order_id']).json() == order
        assert restarted.get('/api/v1/cart').json()['items'] == []
        restarted.cookies.set('sg_owner_id', 'pi-owner-b')
        assert restarted.get(url).status_code == 404
        assert restarted.get(url + '/aftersales').status_code == 404
        assert restarted.get('/api/v1/orders/' + order['order_id']).status_code == 404
        assert confirm(restarted, url, pid).status_code == 404
    finally:
        restarted.close()


@pytest.mark.parametrize('commit_first', [False, True], ids=['human-first', 'commit-first'])
def test_human_acquisition_vs_inflight_confirmation_then_close(lifecycle, monkeypatch, commit_first):
    client, requests = lifecycle
    order, url = compared_order(client, requests)
    pid = model_proposal(client, order, url)
    entered, release = Event(), Event()
    submit = AfterSalesService.submit
    def gated_submit(self, *args):
        result = submit(self, *args) if commit_first else None
        entered.set()
        assert release.wait(10), 'public human transition did not release confirmation'
        return result if commit_first else submit(self, *args)
    with monkeypatch.context() as patch:
        patch.setattr(AfterSalesService, 'submit', gated_submit)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(confirm, client, url, pid)
            try:
                assert entered.wait(10), 'confirmation did not reach approved submit boundary'
                opened = client.post(url + '/human-ticket', json={'summary': '请人工核实这个申请'})
                assert opened.status_code == 200, opened.text
                ticket = opened.json()
                assert ticket['order_id'] == order['order_id']
                assert client.get(url).json()['responsibility'] == 'human'
            finally:
                release.set()
            result = pending.result(timeout=15)
    assert result.status_code == (200 if commit_first else 409), result.text
    operator = {'X-Internal-Token': 'task16-synthetic-operator'}
    target = '/api/v1/mercury/operator/tickets/' + ticket['ticket_id'] + '/messages'
    reply = client.post(target, headers=operator, json={'action': 'reply', 'content': '已核实，请关闭后重新确认', 'version': ticket['version']})
    assert reply.status_code == 200, reply.text
    progress = client.get(url + '/human-ticket').json()
    assert progress['messages'][-1]['content'] == '已核实，请关闭后重新确认'
    assert len(client.get(url + '/aftersales').json()['receipts']) == int(commit_first)
    closed = client.post(target, headers=operator, json={'action': 'close', 'content': '问题已说明', 'version': progress['version']})
    assert closed.status_code == 200 and closed.json()['status'] == 'closed', closed.text
    assert client.get(url).json()['responsibility'] == 'agent'
    if commit_first:
        assert confirm(client, url, pid).json() == result.json()
    else:
        assert confirm(client, url, pid).status_code == 409
        fresh = proposal(client, url)
        assert fresh.status_code == 200, fresh.text
        assert fresh.json()['proposal_id'] != pid
        assert client.get(url + '/aftersales').json()['receipts'] == []
        assert confirm(client, url, fresh.json()['proposal_id'], key='after-human').status_code == 200
    assert len(client.get(url + '/aftersales').json()['receipts']) == 1
    assert client.get('/api/v1/orders/' + order['order_id']).json() == order
    init_db(requests.engine)
    init_db(requests.engine)
    assert client.get(url + '/human-ticket').json() == closed.json()
    assert len(client.get(url + '/aftersales').json()['receipts']) == 1

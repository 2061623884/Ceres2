"""Public owner/version/supply and approved confirmation UoW fault seam."""
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session
from test_runtime_pi_product_query import pi_client
from test_purchase_public import prepare, confirmation_body
from test_guide_lifecycle import BASE, command
from test_purchase_public import purchase_turn as turn


def post(client, state, key='safe-confirm', body=None):
    return client.post('/api/v1/guide/tasks/' + state['task_id'] + '/confirm', json=body or confirmation_body(state), headers={'Idempotency-Key':key})


@pytest.mark.parametrize('change', ['price','stock','unsellable','delivery','delivery_version','zone','budget','exclusion','replace','abandon'])
def test_supply_or_task_changes_prevent_old_confirmation_without_cart_write(pi_client, change):
    client, requests = pi_client
    state = prepare(client, requests)
    from app.models.store import Offer, Store
    if change in ('budget','exclusion','replace','abandon'):
        if change == 'budget': command(client, 'amend', conditions={'budget_fen':100})
        elif change == 'exclusion': command(client, 'amend', conditions={'exclusions':['pi-cola']})
        elif change == 'replace': command(client, 'new_goal', goal='买牛奶')
        else: command(client, 'abandon')
    elif change == 'zone':
        client.post(BASE + '/supply-context', json={'request_id':'new-zone','store_id':'pi-store','delivery_zone_id':'elsewhere','expected_session_version':state['session_version']})
    else:
        with Session(requests.engine) as db:
            if change == 'price': db.execute(update(Offer).values(price_fen=500))
            if change == 'stock': db.execute(update(Offer).values(available_qty=1))
            if change == 'unsellable': db.execute(update(Offer).values(sellable=False))
            if change == 'delivery': db.execute(update(Store).values(delivery_reachable=False))
            if change == 'delivery_version': db.execute(update(Store).values(delivery_version=2))
            db.commit()
    assert post(client,state).status_code == 409
    assert client.get('/api/v1/cart').json()['items'] == []


def test_other_owner_cannot_confirm_and_changed_idempotency_body_conflicts(pi_client):
    client, requests = pi_client
    state = prepare(client, requests)
    client.cookies.set('sg_owner_id','pi-owner-b')
    assert post(client,state).status_code == 403
    client.cookies.set('sg_owner_id','pi-owner-a')
    assert post(client,state).status_code == 200
    body = confirmation_body(state)
    body['selected_items'][0]['quantity'] = 1
    result = post(client,state,body=body)
    assert result.status_code == 409
    assert result.json()['error']['code'] == 'IDEMPOTENCY_CONFLICT'
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2


def test_parallel_distinct_confirmations_increment_only_once(pi_client):
    client, requests = pi_client
    state = prepare(client, requests)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda key:post(client,state,key), ['race-a','race-b']))
    assert sorted(result.status_code for result in results) == [200,409]
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2


def test_failure_before_commit_rolls_back_cart_ledger_receipt_and_retry_succeeds(pi_client, monkeypatch):
    client, requests = pi_client
    state = prepare(client, requests)
    from app.services.purchase_service import PurchaseService
    original = PurchaseService.confirm
    def fail_after_mutations(self,*args,**kwargs):
        original(self,*args,**kwargs)
        raise RuntimeError('controlled before-commit UoW failure')
    monkeypatch.setattr(PurchaseService,'confirm',fail_after_mutations)
    assert post(client,state).status_code == 500
    assert client.get('/api/v1/cart').json()['items'] == []
    restored = client.get(BASE).json()
    assert restored['plan']['items'][0]['added_quantity'] == 0
    assert restored['confirmation_result'] is None
    monkeypatch.setattr(PurchaseService,'confirm',original)
    assert post(client,state).status_code == 200
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2


def test_existing_cart_count_is_included_in_confirmation_stock_check(pi_client):
    client, requests = pi_client
    state = prepare(client, requests)
    cart = client.get('/api/v1/cart').json()
    assert client.post('/api/v1/cart/items',json={'sku_id':'pi-cola','quantity':6,'expected_cart_version':cart['version']}).status_code == 200
    assert post(client,state).status_code == 409
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 6


def test_explicit_row_add_then_full_confirmation_adds_only_remaining(pi_client):
    client, requests = pi_client
    state = prepare(client, requests)
    body = confirmation_body(state)
    body['selected_items'][0]['quantity'] = 1
    row = client.post('/api/v1/guide/tasks/' + state['task_id'] + '/items/pi-cola/add', json=body, headers={'Idempotency-Key':'row-add'})
    assert row.status_code == 200, row.text
    current = client.get(BASE).json()
    assert current['plan']['items'][0]['added_quantity'] == 1
    assert current['plan']['items'][0]['remaining_quantity'] == 1
    body = confirmation_body(current)
    body['selected_items'][0]['quantity'] = 1
    assert post(client,current,'finish-remaining',body).status_code == 200
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2


def test_stop_after_committed_text_preserves_factual_receipt(pi_client):
    client, requests = pi_client
    prepare(client, requests)
    events = turn(client,'就按这个加购','commit-first')
    receipt = events[-1]['payload']['confirmation_result']
    stopped = client.post(BASE + '/turns/stop',json={'request_id':'commit-first'}).json()
    assert stopped['cancelled'] is False
    assert stopped['result']['confirmation_result'] == receipt
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2


def test_shopping_write_hold_blocks_new_button_and_text_confirmation(pi_client, monkeypatch):
    client, requests = pi_client
    state = prepare(client, requests)
    from app.core.config import get_settings
    monkeypatch.setenv('SHOPPING_WRITES_PAUSED','true')
    get_settings.cache_clear()
    response = post(client,state)
    assert response.status_code == 503
    assert response.json()['error']['code'] == 'SHOPPING_WRITES_PAUSED'
    events = turn(client,'就按这个加购','held-confirm')
    assert events[-1]['type'] == 'error'
    assert events[-1]['payload']['code'] == 'SHOPPING_WRITES_PAUSED'
    assert client.get('/api/v1/cart').json()['items'] == []


def test_stopped_run_cannot_claim_confirmation_uow(pi_client):
    client, requests = pi_client
    state = prepare(client, requests)
    requests.answer_hook = None
    admitted = client.post(BASE + '/runs',json={'request_id':'stop-before-claim','message':'受控慢查询可乐','expected_task_id':state['task_id'],'expected_state_version':state['state_version'],'expected_session_version':state['session_version']})
    assert admitted.status_code == 202
    assert requests.started.wait(timeout=5)
    stopped = client.post(BASE + '/turns/stop',json={'request_id':'stop-before-claim'})
    assert stopped.json()['cancelled'] is True
    from app.services.purchase_service import PurchaseService
    from app.core.errors import AppError
    with Session(requests.engine) as db:
        with pytest.raises(AppError) as error:
            PurchaseService(db,'pi-owner-a').confirm(state['task_id'],confirmation_body(state),'stopped-uow',run_id=admitted.json()['run_id'])
        assert error.value.detail['error']['code'] == 'RUN_STOPPED'
        db.rollback()
    requests.release.set()
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('conditions,code', [({'budget_fen':699},'BUDGET_EXCEEDED'),({'exclusions':['pi-cola']},'EXCLUSION_CONFLICT')])
def test_plan_preparation_applies_budget_and_exclusions_before_display(pi_client, conditions, code):
    from app.models.store import Store
    from test_purchase_public import purchase_hook
    client, requests = pi_client
    with Session(requests.engine) as db:
        db.execute(update(Store).values(delivery_reachable=True))
        db.commit()
    command(client,'new_goal',goal='买两件测试可乐',conditions=conditions)
    requests.answer_hook = purchase_hook
    events = turn(client,'选定测试可乐，两件，先给我清单','constrained-prepare')
    if code == 'BUDGET_EXCEEDED':
        assert events[-1]['type'] == 'turn.completed', events
        state = client.get(BASE).json()
        assert state['plan']['budget_quote'] == {'budget_fen':699,'total_fen':700}
        assert state['plan']['can_confirm'] is False
        assert state['conditions']['budget_fen'] == 699
    else:
        assert events[-1]['type'] == 'error'
        assert events[-1]['payload']['code'] == code
        assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_text_confirmation_without_current_displayed_plan_does_not_write(pi_client):
    client, requests = pi_client
    events = turn(client,'就按这个加购','no-plan')
    assert events[-1]['type'] == 'error'
    assert events[-1]['payload']['code'] == 'NO_CURRENT_PLAN'
    assert client.get('/api/v1/cart').json()['items'] == []


def test_parallel_button_and_text_share_exactly_one_cart_increment(pi_client):
    import json
    client, requests = pi_client
    shown = prepare(client, requests)
    text_body = {'request_id':'racing-text', 'message':'就按这个加购', 'expected_task_id':shown['task_id'], 'expected_state_version':shown['state_version'], 'expected_session_version':shown['session_version'], 'displayed_plan':{'task_id':shown['task_id'], 'plan_id':shown['plan']['plan_id'], 'plan_version':shown['plan']['plan_version'], 'state_version':shown['state_version'], 'session_version':shown['session_version']}}
    with ThreadPoolExecutor(max_workers=2) as pool:
        button = pool.submit(post,client,shown,'racing-button')
        text = pool.submit(client.post,BASE + '/turns/stream',json=text_body)
        button_response,text_response = button.result(),text.result()
    events = [json.loads(line[6:]) for line in text_response.text.splitlines() if line.startswith('data: ')]
    assert (button_response.status_code == 200) + (events[-1]['type'] == 'turn.completed') == 1
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2

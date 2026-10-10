"""Public regression matrix for the delivered question identity/transaction contract."""
from concurrent.futures import ThreadPoolExecutor
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_next_snack_public import seed_snacks, exploration_hook, answer_question


def open_question(client, requests, request_id='open'):
    seed_snacks(requests)
    command(client, 'new_goal', goal='零食', conditions={'budget_fen':2000})
    requests.answer_hook = exploration_hook
    return turn(client, '来点零食', request_id)[-1]['payload']['active_question']


def test_typed_choice_replay_and_cross_owner_are_bound_to_original_question(pi_client, controlled_kev_transport):
    client, requests = pi_client
    q = open_question(client, requests)
    choice = q['options'][0]['option_id']
    calls = len(controlled_kev_transport['entry_calls'])
    client.cookies.set('sg_owner_id', 'pi-owner-b')
    assert answer_question(client, q, [choice], 'foreign').status_code == 403
    client.cookies.set('sg_owner_id', 'pi-owner-a')
    first = answer_question(client, q, [choice], 'same-choice')
    replay = answer_question(client, q, [choice], 'same-choice')
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert len(controlled_kev_transport['entry_calls']) == calls, 'Typed choices never route through Kev'
    assert len(client.get(BASE).json()['question_history']) == 2
    assert answer_question(client, q, [q['options'][1]['option_id']], 'same-choice').status_code == 409
    assert client.get('/api/v1/cart').json()['items'] == []


def test_changed_condition_cancel_and_same_label_new_task_retire_old_identity(pi_client):
    client, requests = pi_client
    q = open_question(client, requests)
    assert command(client, 'amend', conditions={'budget_fen':500}).status_code == 200
    state = client.get(BASE).json()
    assert state['active_question'] is None and state['question_history'][0]['status'] == 'stale'
    forged_anchor = {**q, 'state_version':state['state_version']}
    assert answer_question(client, forged_anchor, [q['options'][0]['option_id']], 'old-condition').status_code == 409
    assert command(client, 'abandon').status_code == 200
    assert command(client, 'new_goal', goal='再看零食').status_code == 200
    current = turn(client, '来点零食', 'same-label')[-1]['payload']['active_question']
    assert {o['label'] for o in q['options']} == {o['label'] for o in current['options']}
    assert q['question_id'] != current['question_id']
    forged_anchor = {**q, 'task_id':current['task_id'], 'state_version':current['state_version'], 'session_version':current['session_version']}
    assert answer_question(client, forged_anchor, [q['options'][0]['option_id']], 'old-task').status_code == 409
    assert answer_question(client, current, [q['options'][0]['option_id']], 'foreign-option').status_code == 422
    assert client.get(BASE).json()['active_question']['question_id'] == current['question_id']
    assert client.get('/api/v1/cart').json()['items'] == []


def test_competing_category_clicks_have_one_authoritative_choice(pi_client):
    client, requests = pi_client
    q = open_question(client, requests)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda item:answer_question(client,q,[item[1]['option_id']],f'compete-{item[0]}'),enumerate(q['options'])))
    assert sorted(r.status_code for r in results) == [200,409]
    history = client.get(BASE).json()['question_history']
    assert len(history) == 2 and history[0]['status'] == 'answered'
    assert len(history[0]['selected_option_ids']) == 1
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_inflight_text_cannot_replace_a_newer_typed_choice(pi_client):
    client, requests = pi_client
    q = open_question(client, requests)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(turn, client, '受控慢查询，想看零食', 'competing-text')
        assert requests.started.wait(timeout=5)
        selected = answer_question(client,q,[q['options'][0]['option_id']],'newer-click')
        assert selected.status_code == 200, selected.text
        requests.release.set()
        events = pending.result(timeout=10)
    assert events[-1]['type'] == 'error'
    assert events[-1]['payload']['code'] == 'STALE_STATE'
    assert client.get(BASE).json()['active_question']['question_id'] == selected.json()['active_question']['question_id']
    assert client.get('/api/v1/cart').json()['items'] == []


def test_product_quantity_and_membership_errors_leave_question_and_cart_unchanged(pi_client):
    client, requests = pi_client
    q = open_question(client,requests)
    q = answer_question(client,q,[q['options'][0]['option_id']],'quantity-candidates').json()['active_question']
    oid = q['options'][0]['option_id']
    for index, quantities in enumerate(({}, {oid:0}, {oid:True}, {oid:1.5}, {'other':1})):
        result = answer_question(client,q,[oid],f'bad-quantity-{index}',quantities)
        assert result.status_code == 422, result.text
    assert answer_question(client,q,[oid,oid],'duplicate-selection',{oid:1}).status_code == 422
    assert answer_question(client,q,[oid],'stock-overflow',{oid:99}).status_code == 409
    state = client.get(BASE).json()
    assert state['active_question']['question_id'] == q['question_id']
    assert state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []

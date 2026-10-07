"""Role-only entry through public HTTP/SSE and controlled provider boundaries."""
import json
import re
import httpx
import pytest
from types import SimpleNamespace
from app.core.database import get_db
from app.models.store import Store
from test_next_navigation_public import navigation_client, route
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_guide_clarification_context import context, call, answer
from test_next_drinks_public import seed_drinks, drink_hook


@pytest.fixture
def role_client(navigation_client):
    client = navigation_client[0]
    database = client.app.dependency_overrides[get_db]()
    db = next(database)
    db.add(Store(store_id='store-demo-01', name='隔离导航测试店', delivery_zone_id='zone-default'))
    db.commit()
    database.close()
    cart = client.get('/api/v1/cart')
    assert cart.status_code == 200, cart.text
    assert cart.json()['items'] == []
    return navigation_client


def test_coco_judges_only_momo_need_and_waits_for_explicit_switch(role_client):
    client, base, opening, calls, choice = role_client
    choice['value'] = 'yes'
    original = '请查询这笔订单退款资格，保留原来的两箱饮品采购安排'
    selected = {'kind': 'order', 'id': 'order-explicit-reference'}
    response = route(client, base, opening, message=original, selected_object=selected)
    assert response.status_code == 200, response.text
    decision = response.json()
    assert set(calls[0]['questions']['service']['criteria']) == {'yes', 'no', 'uncertain'}
    assert decision['status'] == 'switch' and decision['target_role'] == 'momo'
    assert decision['authorized_role'] is None and decision['capability'] is None
    assert decision['entry_judgment']['outcome'] == 'yes'
    assert decision['entry_judgment']['elapsed_ms'] >= 0
    assert decision['original_message'] == calls[0]['state']['message'] == original
    assert decision['selected_object'] == selected
    assert client.get(base + '/opening').json()['role'] == 'keke'
    assert client.get(base.replace('/navigation/', '/guide/')).json()['task_id'] is None
    assert route(client, base, opening, message=original, selected_object=selected).json() == decision
    assert len(calls) == 1
    switched = client.post(base + '/switches', json={
        'opening_id': opening['opening_id'], 'target_role': 'momo',
        'accept': True, 'routing_request_id': 'one',
    })
    assert switched.status_code == 200, switched.text
    assert switched.json()['role'] == 'momo'
    assert switched.json()['handoff']['original_message'] == original
    assert switched.json()['handoff']['selected_object'] == selected
    cart = client.get('/api/v1/cart')
    assert cart.status_code == 200, cart.text
    assert cart.json()['items'] == []
    assert len(calls) == 1


@pytest.mark.parametrize('original', [
    '回可可', '回去买水，两箱无糖的，再问一下这笔订单',
    '他说“回可可”，我还是要问这个订单', '如果售后处理完，我再回去买水',
])
def test_momo_text_goes_directly_to_langgraph_and_only_button_returns(
        role_client, monkeypatch, tmp_path, original):
    from app.core.config import get_settings
    from app.mercury.router import get_query_model
    client, base, opening, calls, choice = role_client
    choice['value'] = 'yes'
    monkeypatch.setattr(get_settings(), 'mercury_checkpoint_path', tmp_path / 'momo-checkpoints.sqlite3')
    model_calls = []

    class Model:
        def chat(self, messages, tools=None):
            model_calls.append(messages)
            return SimpleNamespace(content='请选择订单', tool_calls=[])

        def cancel(self):
            pass

    client.app.dependency_overrides[get_query_model] = Model
    switched = client.post(base + '/switches', json={
        'opening_id': opening['opening_id'], 'target_role': 'momo', 'accept': True,
    })
    assert switched.status_code == 200, switched.text
    case = client.post('/api/v1/mercury/sessions').json()['session_id']
    decision = route(client, base, opening, role='momo', message=original, role_session_id=case)
    assert decision.status_code == 200, decision.text
    assert calls == [], 'Momo text must never invoke the Coco entry judge'
    assert decision.json()['status'] == 'ready'
    assert decision.json()['authorized_role'] == 'momo'
    assert not decision.json()['continue_original']
    url = '/api/v1/mercury/sessions/' + case + '/turns/stream'
    body = {'request_id': 'one', 'routing_request_id': 'one', 'message': original}
    response = client.post(url, json=body)
    assert response.status_code == 200 and 'turn.completed' in response.text, response.text
    assert len(model_calls) == 1
    assert any(row['role'] == 'user' and row['content'] == original for row in model_calls[0])
    assert client.get(base + '/opening').json()['role'] == 'momo'
    replay = client.post(url, json=body)
    assert replay.status_code == 200 and 'turn.completed' in replay.text, replay.text
    assert len(model_calls) == 1 and calls == []
    returned = client.post(base + '/switches', json={
        'opening_id': opening['opening_id'], 'target_role': 'keke', 'accept': True,
    })
    assert returned.status_code == 200, returned.text
    assert returned.json()['role'] == 'keke' and returned.json()['handoff'] is None
    assert client.get(base.replace('/navigation/', '/guide/')).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []
    assert calls == []


@pytest.mark.parametrize('route_field', [{}, {'routing_request_id': None}])
def test_role_button_never_picks_up_pending_or_accepted_text(role_client, route_field):
    client, base, opening, calls, choice = role_client
    choice['value'] = 'yes'
    suggested = route(client, base, opening, message='查询这笔订单，然后保留饮品采购')
    assert suggested.status_code == 200 and suggested.json()['status'] == 'switch'
    chosen = client.post(base + '/switches', json={
        'opening_id': opening['opening_id'], 'target_role': 'momo', 'accept': True, **route_field,
    })
    assert chosen.status_code == 200, chosen.text
    assert chosen.json()['handoff'] is None
    assert chosen.json()['pending_request_id'] is None
    assert chosen.json()['accepted_request_id'] is None
    returned = client.post(base + '/switches', json={
        'opening_id': opening['opening_id'], 'target_role': 'keke', 'accept': True, **route_field,
    })
    assert returned.status_code == 200 and returned.json()['handoff'] is None
    second = route(client, base, opening, request_id='accepted-text', message='继续查询原订单')
    assert second.status_code == 200 and second.json()['status'] == 'switch'
    accepted = client.post(base + '/switches', json={
        'opening_id': opening['opening_id'], 'target_role': 'momo', 'accept': True,
        'routing_request_id': 'accepted-text',
    })
    assert accepted.status_code == 200 and accepted.json()['handoff'] is not None
    returned = client.post(base + '/switches', json={
        'opening_id': opening['opening_id'], 'target_role': 'keke', 'accept': True, **route_field,
    })
    assert returned.status_code == 200 and returned.json()['handoff'] is None
    assert returned.json()['accepted_request_id'] is None
    reopened = client.post(base + '/switches', json={
        'opening_id': opening['opening_id'], 'target_role': 'momo', 'accept': True, **route_field,
    })
    assert reopened.status_code == 200 and reopened.json()['handoff'] is None
    assert len(calls) == 2
    assert client.get('/api/v1/cart').json()['items'] == []


def test_first_pi_request_keeps_task_question_and_entire_mixed_second_choice(
        pi_client, controlled_kev_transport):
    client, requests = pi_client
    controlled_kev_transport['choose'] = lambda _: 'no'
    seed_drinks(requests)
    task = command(client, 'new_goal', goal='饮品采购', conditions={'budget_fen': 2000}).json()
    requests.answer_hook = drink_hook
    initial = turn(client, '喝点东西', 'drink-question')
    assert initial[-1]['type'] == 'turn.completed', initial
    question = initial[-1]['payload']['active_question']
    assert question['kind'] == 'category' and len(question['options']) == 2
    selected = question['options'][1]
    original = '就第二个，仍然二十元以内，先别加购，再告诉我一般退货政策。'
    requests.clear()
    observed = []

    def respond(body):
        facts = context(body)
        observed.append(facts)
        outputs = [json.loads(row['content']) for row in body['messages'] if row['role'] == 'tool']
        if not outputs:
            if not facts.get('active_question'):
                return answer({'status': 'waiting', 'clarification_slot': 'target'})
            return call(body, 'guide_request', {'kind': 'continue'})
        if len(outputs) == 1:
            return call(body, 'explore_products', {
                'category_id': 'beverage', 'product_type': selected['value'],
                'answer_question_id': question['question_id'],
            })
        if len(outputs) == 2:
            return call(body, 'search_after_sales_policy', {'query': '一般退货政策'})
        return answer({'status': 'completed', 'answer_kind': 'exploration',
                       'exploration_ref': outputs[1]['exploration_ref'], 'policy_ref': outputs[2]['policy_ref']})

    requests.answer_hook = respond
    result = turn(client, original, 'drink-second-and-policy')
    assert observed[0].get('active_question') == question
    assert observed[0]['current_task']['task_id'] == task['task_id']
    assert observed[0]['current_task']['goal'] == '饮品采购'
    assert observed[0]['current_task']['conditions'] == {'budget_fen': 2000}
    assert 'capability' not in observed[0]
    first_tools = {tool['function']['name'] for tool in requests[0]['tools']}
    assert {'guide_request', 'explore_products', 'select_question_products',
            'propose_dish', 'propose_purchase', 'search_after_sales_policy'} <= first_tools
    assert original in json.dumps(requests[0]['messages'], ensure_ascii=False)
    assert result[-1]['type'] == 'turn.completed', result
    final = result[-1]['payload']
    assert 'P-RET-01' in '\n'.join(message['content'] for message in final['messages'])
    state = client.get(BASE).json()
    assert state['task_id'] == task['task_id']
    assert state['conditions'] == {'budget_fen': 2000}
    assert state['question_history'][0]['selected_option_ids'] == [selected['option_id']]
    assert all(option['product']['product_type'] == selected['value'] for option in state['active_question']['options'])
    assert state['plan'] is None and client.get('/api/v1/cart').json()['items'] == []
    assert len(controlled_kev_transport['calls']) == 2


@pytest.mark.parametrize('provider_choice,outcome,reason', [
    ('no', 'no', None),
    ('uncertain', 'uncertain', None),
    (httpx.ReadTimeout('controlled entry timeout'), 'timeout', 'ReadTimeout'),
    (httpx.ConnectError('controlled entry failure'), 'error', 'ConnectError'),
])
def test_non_transfer_and_entry_failures_continue_original_pi_once(
        pi_client, controlled_kev_transport, provider_choice, outcome, reason):
    client, requests = pi_client
    controlled_kev_transport['choose'] = lambda _: provider_choice
    nav = BASE.replace('/guide/', '/navigation/')
    opening = client.post(nav + '/opening', json={'role': 'keke'}).json()
    original = '请查一下可乐的规格和价格，保留当前采购安排，先别加购。'
    decision = route(client, nav, opening, request_id='entry-fallback', message=original)
    assert decision.status_code == 200, decision.text
    payload = decision.json()
    assert payload['status'] == 'ready' and payload['authorized_role'] == 'keke'
    assert payload['entry_judgment']['outcome'] == outcome
    assert payload['entry_judgment']['elapsed_ms'] >= 0
    assert payload['entry_judgment']['reason'] == reason
    body = {'request_id': 'entry-fallback', 'routing_request_id': 'entry-fallback',
            'message': original, 'expected_task_id': None, 'expected_state_version': 0,
            'expected_session_version': 0}
    response = client.post(BASE + '/turns/stream', json=body)
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    assert events[-1]['payload']['product_evidence'][0]['sku_id'] == 'pi-cola'
    assert original in json.dumps(requests[0]['messages'], ensure_ascii=False)
    count = len(requests)
    replay = client.post(BASE + '/turns/stream', json=body)
    replay_events = [json.loads(line[6:]) for line in replay.text.splitlines() if line.startswith('data: ')]
    assert replay_events[-1]['payload'] == events[-1]['payload']
    assert len(requests) == count and len(controlled_kev_transport['calls']) == 1
    assert client.get(nav + '/opening').json()['role'] == 'keke'
    assert client.get('/api/v1/cart').json()['items'] == []


def test_specific_order_fallback_explains_boundary_with_explicit_typed_entry(
        pi_client, controlled_kev_transport):
    client, requests = pi_client
    controlled_kev_transport['choose'] = lambda _: 'uncertain'
    original = '请替我查这笔订单的退款资格，尚未授权提交退款。'

    def boundary(body):
        if not any(row['role'] == 'tool' for row in body['messages']):
            return call(body, 'guide_request', {'kind': 'question'})
        return answer({'status': 'completed', 'answer_kind': 'role_boundary',
                       'message': '退款已经到账', 'target_role': 'keke'})

    requests.answer_hook = boundary
    before = client.get('/api/v1/orders').json()
    events = turn(client, original, 'specific-order-boundary')
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert result['answer_kind'] == 'role_boundary'
    assert '墨墨' in result['message'] and '尚未查询' in result['message']
    assert '退款已经到账' not in result['message']
    nav = BASE.replace('/guide/', '/navigation/')
    opening = client.get(nav + '/opening').json()
    assert opening['role'] == 'keke'
    action = result['navigation_action']
    assert action['type'] == 'switch_role'
    assert action['session_id'] == 'pi-session-a'
    assert action['request'] == {'opening_id': opening['opening_id'], 'target_role': 'momo',
                                 'accept': True, 'routing_request_id': None}
    assert original in json.dumps(requests[0]['messages'], ensure_ascii=False)
    assert len(controlled_kev_transport['calls']) == 1
    assert result['committed'] is False and result['action_results'] == []
    assert client.get('/api/v1/orders').json() == before
    assert client.get('/api/v1/cart').json()['items'] == []
    assert client.get(BASE).json()['task_id'] is None
    assert not any(tool['function']['name'] in {'check_refund_eligibility', 'prepare_aftersales_proposal'}
                   for request in requests for tool in request['tools'])
    chosen = client.post(nav + '/switches', json=action['request'])
    assert chosen.status_code == 200 and chosen.json()['role'] == 'momo'
    assert chosen.json()['handoff'] is None
    assert len(controlled_kev_transport['calls']) == 1


def test_public_navigation_schema_types_ready_switch_and_real_entry_diagnostics(role_client):
    client, _, _, _, _ = role_client
    specification = client.get('/openapi.json').json()
    path = '/api/v1/navigation/sessions/{session_id}/routes'
    response = specification['paths'][path]['post']['responses']['200']['content']['application/json']['schema']
    assert '$ref' in response, 'The existing navigation response needs a public typed contract'
    decision = specification['components']['schemas'][response['$ref'].rsplit('/', 1)[-1]]
    assert set(decision['properties']['status']['enum']) == {'ready', 'switch'}
    assert decision['properties']['capability']['type'] == 'null'
    judgment_ref = next(item['$ref'] for item in decision['properties']['entry_judgment']['anyOf'] if '$ref' in item)
    judgment = specification['components']['schemas'][judgment_ref.rsplit('/', 1)[-1]]
    assert set(judgment['properties']['outcome']['enum']) == {'yes', 'no', 'uncertain', 'timeout', 'error', 'not_attempted'}
    assert {'outcome', 'elapsed_ms', 'reason'} <= set(judgment['required'])
    assert {'original_message', 'routing_request_id', 'opening_id', 'selected_object'} <= set(decision['required'])
    switch_path = '/api/v1/navigation/sessions/{session_id}/switches'
    switch_ref = specification['paths'][switch_path]['post']['requestBody']['content']['application/json']['schema']['$ref']
    switch = specification['components']['schemas'][switch_ref.rsplit('/', 1)[-1]]
    assert set(switch['required']) == {'opening_id', 'target_role', 'accept'}
    assert set(switch['properties']['target_role']['enum']) == {'keke', 'momo'}
    assert switch['properties']['accept']['type'] == 'boolean'
    assert {item['type'] for item in switch['properties']['routing_request_id']['anyOf']} == {'string', 'null'}
    assert switch['additionalProperties'] is False


@pytest.mark.parametrize('failure_kind', ['http', 'validation'])
def test_entry_failure_keeps_correlated_sanitized_causes(role_client, monkeypatch, caplog, failure_kind):
    from app.services import kev_provider
    client, base, opening, _, _ = role_client
    secret = 'private-provider-content-do-not-log'
    sent = []

    def provider(request):
        sent.append(request)
        if failure_kind == 'http':
            return httpx.Response([401, 429][len(sent) - 1], json={'error': secret})
        if len(sent) == 1:
            return httpx.Response(200, json={'model': secret, 'answers': {}})
        return httpx.Response(200, json={'model': 'kev-latest', 'answers': {'service': {
            'type': 'choice', 'choice': secret, 'probabilities': {'yes': 1, 'no': 0, 'uncertain': 0},
        }}})

    cause_fingerprints = []
    with httpx.Client(transport=httpx.MockTransport(provider)) as transport:
        monkeypatch.setattr(kev_provider, 'client', lambda: transport)
        for index in range(2):
            request_id = f'failure-{failure_kind}-{index}'
            response = route(client, base, opening, request_id=request_id, message='保留原购物安排')
            assert response.status_code == 200, response.text
            decision = response.json()
            assert decision['status'] == 'ready' and decision['authorized_role'] == 'keke'
            assert decision['entry_judgment']['outcome'] == 'error'
            assert decision['entry_judgment']['reason'] == ('HTTPStatusError' if failure_kind == 'http' else 'ValidationError')
            diagnostics = [record.getMessage() for record in caplog.records
                           if request_id in record.getMessage() and 'fingerprint' in record.getMessage()]
            assert len(diagnostics) == 1, 'Recovered provider causes must remain correlated and diagnosable'
            diagnostic = diagnostics[0]
            assert base.rsplit('/', 1)[-1] in diagnostic
            fingerprints = re.findall(r"'fingerprint': '([a-f0-9]{64})'", diagnostic)
            assert len(fingerprints) >= 2 and 'frames' in diagnostic
            cause_fingerprints.append(fingerprints[-1])
            assert secret not in diagnostic and secret not in response.text
            assert 'http://' not in diagnostic and 'offline-fixture-key' not in diagnostic
            count = len(caplog.records)
            assert route(client, base, opening, request_id=request_id, message='保留原购物安排').json() == decision
            assert len(caplog.records) == count
    assert len(sent) == 2
    assert len(set(cause_fingerprints)) == 2, 'Distinct provider faults must not collapse into a shared exception class'


@pytest.mark.parametrize('shopping_status', ['completed', 'waiting'])
def test_mixed_fallback_retains_shopping_and_explicit_order_boundary(
        pi_client, controlled_kev_transport, shopping_status):
    client, requests = pi_client
    controlled_kev_transport['choose'] = lambda _: httpx.ReadTimeout('controlled entry timeout')
    seed_drinks(requests)
    task = command(client, 'new_goal', goal='饮品采购', conditions={'budget_fen': 2000}).json()
    original = ('继续选饮品，仍然二十元以内先别加购，也说一下一般退货政策，并查询这笔订单退款资格。'
                if shopping_status == 'completed' else
                '继续选饮品，包装还没决定，仍然二十元以内先别加购，并查询这笔订单退款资格。')

    def mixed(body):
        outputs = [json.loads(row['content']) for row in body['messages'] if row['role'] == 'tool']
        if not outputs:
            return call(body, 'guide_request', {'kind': 'continue'})
        if shopping_status == 'waiting':
            return answer({'status': 'waiting', 'clarification_slot': 'packaging', 'role_boundary': True,
                           'message': '退款已经到账', 'target_role': 'keke'})
        if len(outputs) == 1:
            return call(body, 'explore_products', {'category_id': 'beverage'})
        if len(outputs) == 2:
            return call(body, 'search_after_sales_policy', {'query': '一般退货政策'})
        return answer({'status': 'completed', 'answer_kind': 'exploration',
                       'exploration_ref': outputs[1]['exploration_ref'], 'policy_ref': outputs[2]['policy_ref'],
                       'role_boundary': True, 'message': '退款已经到账', 'target_role': 'keke'})

    requests.answer_hook = mixed
    before_orders = client.get('/api/v1/orders').json()
    request_id = 'mixed-order-' + shopping_status
    body = {'request_id': request_id, 'message': original,
            'expected_task_id': task['task_id'], 'expected_state_version': task['state_version'],
            'expected_session_version': task['session_version']}
    response = client.post(BASE + '/turns/stream', json=body)
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    contents = [message['content'] for message in result['messages']]
    assert any('墨墨' in text and '尚未查询' in text for text in contents)
    assert '退款已经到账' not in json.dumps(events, ensure_ascii=False)
    if shopping_status == 'completed':
        assert result['active_question']['kind'] == 'category'
        assert {option['value'] for option in result['active_question']['options']} == {'tea', 'water'}
        assert result['message'] == result['active_question']['question']
        assert any('P-RET-01' in text for text in contents), 'The existing policy attachment must survive'
    else:
        assert result['runtime_status'] == 'waiting'
        assert result['pending_clarifications'] == [{'slot': 'packaging', 'question': result['message']}]
        assert '瓶装' in result['message'] and result['active_question'] is None
    state = client.get(BASE).json()
    assert state['task_id'] == task['task_id'] and state['conditions'] == {'budget_fen': 2000}
    assert state['plan'] is None
    assert result['committed'] is False and result['action_results'] == []
    assert client.get('/api/v1/orders').json() == before_orders
    assert client.get('/api/v1/cart').json()['items'] == []
    assert original in json.dumps(requests[0]['messages'], ensure_ascii=False)
    assert not any(tool['function']['name'] in {'check_refund_eligibility', 'prepare_aftersales_proposal'}
                   for request in requests for tool in request['tools'])
    nav = BASE.replace('/guide/', '/navigation/')
    opening = client.get(nav + '/opening').json()
    assert opening['role'] == 'keke'
    action = result['navigation_action']
    assert action == {'type': 'switch_role', 'session_id': 'pi-session-a', 'request': {
        'opening_id': opening['opening_id'], 'target_role': 'momo', 'accept': True, 'routing_request_id': None,
    }}
    count = len(requests)
    replay = client.post(BASE + '/turns/stream', json=body)
    replay_events = [json.loads(line[6:]) for line in replay.text.splitlines() if line.startswith('data: ')]
    assert replay_events[-1]['payload'] == result
    assert len(requests) == count and len(controlled_kev_transport['calls']) == 1
    chosen = client.post(nav + '/switches', json=action['request'])
    assert chosen.status_code == 200 and chosen.json()['role'] == 'momo'
    assert chosen.json()['handoff'] is None
    assert client.get('/api/v1/orders').json() == before_orders
    assert client.get('/api/v1/cart').json()['items'] == []


@pytest.mark.parametrize('marker', ['true', 1, {'target_role': 'momo'}])
def test_role_boundary_marker_requires_an_actual_boolean(pi_client, marker):
    client, requests = pi_client

    def malformed(body):
        if not any(row['role'] == 'tool' for row in body['messages']):
            return call(body, 'guide_request', {'kind': 'question'})
        return answer({'status': 'waiting', 'clarification_slot': 'target', 'role_boundary': marker})

    requests.answer_hook = malformed
    events = turn(client, '购物需求还不明确，也请查询订单', 'typed-boundary-marker')
    assert events[-1]['type'] == 'error', events
    assert events[-1]['payload']['code'] == 'PI_ANSWER_INVALID'
    assert not any(event['type'] == 'answer.delta' for event in events)
    assert client.get(BASE).json()['task_id'] is None
    assert client.get('/api/v1/cart').json()['items'] == []

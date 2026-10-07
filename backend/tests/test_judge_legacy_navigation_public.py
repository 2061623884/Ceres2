"""Synthetic pre-upgrade receipts are inputs; all assertions use public APIs."""
import hashlib
import json
import pytest
from app.core.database import get_db
from app.models.guide import GuideCommandReceipt, GuideSession
from test_judge_role_entry_public import role_client, navigation_client
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE
from test_purchase_public import prepare

LEGACY_CRITERIA = 'ceres2-role-capability-v2-explicit-return'
LEGACY_CHOICES = [
    'keke_exploration', 'keke_purchase_modification', 'keke_factual_qa', 'keke_chat',
    'momo', 'clarify', 'return_keke', 'return_keke_exploration',
    'return_keke_purchase_modification', 'return_keke_factual_qa', 'return_keke_chat',
]


def legacy_route_input(client, base, opening, choice):
    """An isolated fixture in the actual old JSON shape, never an active old DB."""
    returning = choice.startswith('return_keke')
    compound = choice.startswith('return_keke_')
    body = {'request_id': 'legacy-text', 'opening_id': opening['opening_id'],
            'role': 'momo' if returning else 'keke', 'message': '旧原文，保留采购与售后条件',
            'selected_object': None, 'role_session_id': None}
    result = {
        'routing_request_id': body['request_id'], 'opening_id': body['opening_id'],
        'original_message': body['message'], 'source_role': body['role'],
        'target_role': 'momo' if choice == 'momo' else 'keke', 'selected_object': None,
        'capability': choice.removeprefix('return_keke_') if compound else choice.removeprefix('keke_') if choice.startswith('keke_') else None,
        'authorized_role': 'keke' if compound or choice.startswith('keke_') else None,
        'show_prompt': choice == 'momo', 'continue_original': compound,
        'criteria_version': LEGACY_CRITERIA, 'anchor': [0, None, 0],
        'status': 'navigation' if returning else 'switch' if choice == 'momo' else 'clarify' if choice == 'clarify' else 'ready',
        'provider_output': {'model': 'kev-latest', 'answers': {'service': {
            'type': 'choice', 'choice': choice, 'probabilities': {key: float(key == choice) for key in LEGACY_CHOICES},
        }}},
    }
    database = client.app.dependency_overrides[get_db]()
    db = next(database)
    session = db.get(GuideSession, base.rsplit('/', 1)[-1])
    context = json.loads(session.entry_context_json)
    context['role_navigation'].update(latest_request_id='legacy-text',
                                      pending_request_id='legacy-text' if choice == 'momo' else None,
                                      accepted_request_id='legacy-text' if compound else None)
    session.entry_context_json = json.dumps(context)
    db.add(GuideCommandReceipt(session_id=session.session_id, request_id='route:legacy-text',
                               digest=hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                               result_json=json.dumps(result, ensure_ascii=False)))
    db.commit()
    database.close()
    return body


@pytest.mark.parametrize('choice', LEGACY_CHOICES)
def test_unfinished_legacy_navigation_explicitly_expires_without_rejudging(role_client, choice):
    client, base, opening, calls, _ = role_client
    body = legacy_route_input(client, base, opening, choice)
    replay = client.post(base + '/routes', json=body)
    assert replay.status_code == 409, replay.text
    assert replay.json()['error']['code'] == 'STALE_NAVIGATION'
    assert '重新' in replay.json()['error']['message']
    restored = client.get(base + '/opening')
    assert restored.status_code == 200, restored.text
    assert restored.json()['role'] == 'keke' and restored.json()['handoff'] is None
    if choice == 'momo' or choice.startswith('return_keke_'):
        accepted = client.post(base + '/switches', json={
            'opening_id': opening['opening_id'], 'target_role': 'momo' if choice == 'momo' else 'keke',
            'accept': True, 'routing_request_id': 'legacy-text',
        })
        assert accepted.status_code == 409 and accepted.json()['error']['code'] == 'STALE_NAVIGATION'
    assert calls == []
    assert client.get('/api/v1/cart').json()['items'] == []
    assert client.get(base.replace('/navigation/', '/guide/')).json()['task_id'] is None


@pytest.mark.parametrize('legacy_choice', ['keke_purchase_modification', 'return_keke_purchase_modification'])
def test_completed_legacy_cart_receipt_replays_without_navigation_or_duplicate_write(
        pi_client, controlled_kev_transport, legacy_choice):
    from sqlalchemy import select
    from sqlalchemy.orm import Session
    from app.models.guide import GuideTurnReceipt
    client, requests = pi_client
    controlled_kev_transport['choose'] = lambda _: 'no'
    state = prepare(client, requests)
    body = {'request_id': 'legacy-confirmed', 'message': '就按这个加购',
            'expected_task_id': state['task_id'], 'expected_state_version': state['state_version'],
            'expected_session_version': state['session_version'],
            'displayed_plan': {'task_id': state['task_id'], 'plan_id': state['plan']['plan_id'],
                               'plan_version': state['plan']['plan_version'],
                               'state_version': state['state_version'], 'session_version': state['session_version']}}
    confirmed = client.post(BASE + '/turns/stream', json=body)
    events = [json.loads(line[6:]) for line in confirmed.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    actual = events[-1]['payload']
    assert actual['confirmation_result']['items_added'] == [{'sku_id': 'pi-cola', 'quantity': 2}]
    cart = client.get('/api/v1/cart').json()
    nav = BASE.replace('/guide/', '/navigation/')
    opening = client.get(nav + '/opening').json()
    route_body = {'request_id': body['request_id'], 'message': body['message'],
                  'opening_id': opening['opening_id'],
                  'role': 'momo' if legacy_choice.startswith('return_') else 'keke',
                  'selected_object': None, 'role_session_id': None}
    # Upgrade input fixture: retain the real completed result/cart untouched,
    # encode only its route and admission metadata in the old stored shape.
    with Session(requests.engine) as db:
        row = db.get(GuideCommandReceipt, ('pi-session-a', 'route:' + body['request_id']))
        saved = json.loads(row.result_json)
        saved.update(criteria_version=LEGACY_CRITERIA, capability='purchase_modification',
                     source_role=route_body['role'], status='navigation' if route_body['role'] == 'momo' else 'ready',
                     continue_original=route_body['role'] == 'momo')
        saved.pop('entry_judgment', None)
        row.result_json = json.dumps(saved, ensure_ascii=False)
        row.digest = hashlib.sha256(json.dumps(route_body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        run = db.scalar(select(GuideTurnReceipt).where(GuideTurnReceipt.session_id == 'pi-session-a',
                                                     GuideTurnReceipt.request_id == body['request_id']))
        old_input = json.loads(run.input_json)
        old_input['_route_capability'] = 'purchase_modification'
        run.input_json = json.dumps(old_input, ensure_ascii=False)
        run.digest = hashlib.sha256(json.dumps(old_input, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        db.commit()
    assert client.delete(nav + '/opening/' + opening['opening_id']).status_code == 200
    reopened = client.post(nav + '/opening', json={'role': 'momo'}).json()
    before_calls, before_models = len(controlled_kev_transport['calls']), len(requests)
    route_replay = client.post(nav + '/routes', json=route_body)
    assert route_replay.status_code == 200, route_replay.text
    assert route_replay.json()['status'] == 'ready'
    assert not route_replay.json()['continue_original'] and not route_replay.json()['show_prompt']
    replay = client.post(BASE + '/turns/stream', json=body)
    replay_events = [json.loads(line[6:]) for line in replay.text.splitlines() if line.startswith('data: ')]
    assert replay_events[-1]['payload'] == actual
    assert client.get(BASE + '/turns/' + body['request_id']).json()['result'] == actual
    assert client.get('/api/v1/cart').json() == cart
    current = client.get(nav + '/opening').json()
    assert current['opening_id'] == reopened['opening_id'] and current['role'] == 'momo'
    assert current['handoff'] is None
    assert len(controlled_kev_transport['calls']) == before_calls and len(requests) == before_models

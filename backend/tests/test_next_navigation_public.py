"""Public opening lifecycle; isolated owner/database, no model or provider network."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.core.database import create_db_engine, init_db, get_db
from app.main import create_app


def test_opening_refresh_preserves_quota_and_only_close_reopens(tmp_path):
    bind = create_db_engine('sqlite:///' + str(tmp_path / 'navigation.sqlite3'))
    init_db(bind)
    factory = sessionmaker(bind=bind, expire_on_commit=False)
    app = create_app(bind)
    def database():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        guide = client.post('/api/v1/guide/sessions', json={'entry_context': {'page': 'home', 'store_id': 'store-default', 'delivery_zone_id': 'zone-default'}}).json()
        base = '/api/v1/navigation/sessions/' + guide['session_id']
        first = client.post(base + '/opening', json={'role': 'keke'})
        assert first.status_code == 200, first.text
        opening = first.json()
        assert not opening['prompt_displayed']
        assert client.get(base + '/opening').json()['opening_id'] == opening['opening_id']
        assert client.post(base + '/opening', json={'role': 'momo'}).json()['opening_id'] == opening['opening_id']
        assert client.delete(base + '/opening/' + opening['opening_id']).status_code == 200
        reopened = client.post(base + '/opening', json={'role': 'momo'}).json()
        assert reopened['opening_id'] != opening['opening_id']
        assert reopened['role'] == 'momo' and not reopened['prompt_displayed']


def test_one_judgment_replay_ack_decline_manual_and_new_opening(tmp_path, controlled_kev_transport):
    calls = controlled_kev_transport['calls']
    controlled_kev_transport['choose'] = lambda state: 'momo'
    bind = create_db_engine('sqlite:///' + str(tmp_path / 'route.sqlite3'))
    init_db(bind)
    factory = sessionmaker(bind=bind, expire_on_commit=False)
    app = create_app(bind)
    def database():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        guide = client.post('/api/v1/guide/sessions', json={'entry_context': {'page': 'home', 'store_id': 'store-default', 'delivery_zone_id': 'zone-default'}}).json()
        base = '/api/v1/navigation/sessions/' + guide['session_id']
        opening = client.post(base + '/opening', json={'role': 'keke'}).json()
        body = {'request_id': 'route-one', 'message': '查询这笔订单退款资格', 'role': 'keke', 'opening_id': opening['opening_id']}
        first = client.post(base + '/routes', json=body)
        assert first.status_code == 200, first.text
        route = first.json()
        assert route['status'] == 'switch' and route['show_prompt']
        assert route['capability'] is None
        assert client.post(base + '/routes', json=body).json() == route
        assert len(calls) == 1
        assert not client.get(base + '/opening').json()['prompt_displayed']
        ack = client.post(base + '/prompt-displayed', json={'opening_id': opening['opening_id'], 'routing_request_id': 'route-one'})
        assert ack.status_code == 200
        assert client.get(base + '/opening').json()['prompt_displayed']
        declined = client.post(base + '/switches', json={'opening_id': opening['opening_id'], 'target_role': 'momo', 'routing_request_id': 'route-one', 'accept': False})
        assert declined.status_code == 200
        assert declined.json()['role'] == 'keke'
        manual = client.post(base + '/switches', json={'opening_id': opening['opening_id'], 'target_role': 'momo', 'accept': True})
        assert manual.status_code == 200 and manual.json()['handoff'] is None
        assert len(calls) == 1
        assert client.get('/api/v1/guide/sessions/' + guide['session_id']).json()['task_id'] is None


import pytest


@pytest.fixture
def navigation_client(tmp_path, controlled_kev_transport):
    calls = controlled_kev_transport['calls']
    choice = {'value': 'momo'}
    controlled_kev_transport['choose'] = lambda state: choice['value']
    bind = create_db_engine('sqlite:///' + str(tmp_path / 'navigation-cases.sqlite3'))
    init_db(bind)
    factory = sessionmaker(bind=bind, expire_on_commit=False)
    app = create_app(bind)
    def database():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        guide = client.post('/api/v1/guide/sessions', json={'entry_context': {'page': 'home', 'store_id': 'store-default', 'delivery_zone_id': 'zone-default'}}).json()
        base = '/api/v1/navigation/sessions/' + guide['session_id']
        opening = client.post(base + '/opening', json={'role': 'keke'}).json()
        yield client, base, opening, calls, choice


def route(client, base, opening, request_id='one', role='keke', message='原始请求', **extra):
    return client.post(base + '/routes', json={'request_id':request_id, 'opening_id':opening['opening_id'], 'role':role, 'message':message, **extra})


def test_pending_handoff_survives_refresh_and_duplicate_accept(navigation_client):
    client, base, opening, calls, _ = navigation_client
    assert route(client, base, opening).json()['status'] == 'switch'
    accepted = client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True, 'routing_request_id':'one'})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()['handoff']['original_message'] == '原始请求'
    refreshed = client.get(base + '/opening').json()
    assert refreshed['role'] == 'momo'
    assert refreshed['handoff'] == accepted.json()['handoff']
    replay = client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True, 'routing_request_id':'one'})
    assert replay.status_code == 200 and replay.json()['handoff'] == accepted.json()['handoff']
    assert len(calls) == 1


def test_new_text_invalidates_old_switch_and_failure_stays_visible(navigation_client):
    from app.services.kev_provider import KevUnavailable
    client, base, opening, calls, choice = navigation_client
    route(client, base, opening)
    choice['value'] = KevUnavailable('controlled unavailable')
    failure = route(client, base, opening, 'two').json()
    assert failure['status'] == 'unavailable' and failure['authorized_role'] is None
    stale = client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True, 'routing_request_id':'one'})
    assert stale.status_code == 409
    manual = client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True})
    assert manual.status_code == 200 and manual.json()['handoff']['routing_request_id'] == 'two'
    assert len(calls) == 2


def test_ack_quota_survives_switch_and_close_is_the_only_reset(navigation_client):
    client, base, opening, calls, choice = navigation_client
    route(client, base, opening)
    client.post(base + '/prompt-displayed', json={'opening_id':opening['opening_id'], 'routing_request_id':'one'})
    client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True, 'routing_request_id':'one'})
    choice['value'] = 'keke_exploration'
    second = route(client, base, opening, 'two', role='momo').json()
    assert second['status'] == 'switch' and not second['show_prompt']
    client.delete(base + '/opening/' + opening['opening_id'])
    reopened = client.post(base + '/opening', json={'role':'momo'}).json()
    assert route(client, base, reopened, 'three', role='momo').json()['show_prompt']
    assert len(calls) == 3


@pytest.mark.parametrize('capability', ['exploration','purchase_modification','factual_qa','chat'])
def test_coco_only_capability_and_original_complex_text_preserved(navigation_client, capability):
    client, base, opening, calls, choice = navigation_client
    choice['value'] = 'keke_' + capability
    text = '预算二十元，选零食，保留原饮品，再说明退货政策'
    result = route(client, base, opening, message=text).json()
    assert result['status'] == 'ready' and result['capability'] == capability
    assert result['original_message'] == calls[0]['state']['message'] == text
    assert client.get(base.replace('/navigation/', '/guide/')).json()['task_id'] is None


def test_explicit_return_navigates_without_confirmation(navigation_client):
    client, base, opening, calls, choice = navigation_client
    client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True})
    choice['value'] = 'return_keke'
    result = route(client, base, opening, role='momo', message='回到购物').json()
    assert result['status'] == 'navigation' and not result['show_prompt']
    assert client.get(base + '/opening').json()['role'] == 'keke'
    assert len(calls) == 1


def test_route_id_cannot_reuse_new_body_or_other_owner(navigation_client):
    client, base, opening, calls, choice = navigation_client
    route(client, base, opening)
    assert route(client, base, opening, message='不同请求').status_code == 409
    client.cookies.clear()
    assert client.get(base + '/opening').status_code == 403
    assert len(calls) == 1


def test_mercury_replay_returns_same_result_without_rerouting_or_reexecution(navigation_client, monkeypatch):
    from app.mercury import router as mercury
    client, base, opening, calls, choice = navigation_client
    executed = []
    def query(owner, case, text, *args):
        executed.append((case['session_id'], text))
        return {'final_text':'一般政策查询完成，不代表订单资格。', 'status':'completed', 'action_results':[]}
    monkeypatch.setattr(mercury, 'run_query', query)
    client.app.dependency_overrides[mercury.get_query_model] = lambda: object()
    client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True})
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    url = '/api/v1/mercury/sessions/' + sid + '/turns/stream'
    body = {'request_id':'mercury-original', 'message':'一般退货政策是什么'}
    first = client.post(url, json=body)
    assert first.status_code == 200 and '一般政策查询完成' in first.text, first.text
    replay = client.post(url, json=body)
    assert replay.status_code == 200 and '一般政策查询完成' in replay.text, replay.text
    assert len(executed) == len(calls) == 1
    assert client.post(url, json={**body, 'message':'另一条请求'}).status_code == 409


def test_closed_opening_cannot_execute_previously_accepted_unadmitted_handoff(navigation_client, monkeypatch):
    from app.mercury import router as mercury
    client, base, opening, calls, choice = navigation_client
    executed = []
    monkeypatch.setattr(mercury, 'run_query', lambda *args: executed.append(args) or {'final_text':'不应执行', 'status':'completed'})
    client.app.dependency_overrides[mercury.get_query_model] = lambda: object()
    route(client, base, opening, message='退款政策')
    client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True, 'routing_request_id':'one'})
    client.delete(base + '/opening/' + opening['opening_id'])
    client.post(base + '/opening', json={'role':'momo'})
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    response = client.post('/api/v1/mercury/sessions/' + sid + '/turns/stream', json={'request_id':'one','routing_request_id':'one','message':'退款政策'})
    assert response.status_code == 409, response.text
    assert executed == []


def test_new_text_invalidates_accepted_but_unadmitted_handoff(navigation_client, monkeypatch):
    from app.mercury import router as mercury
    client, base, opening, calls, choice = navigation_client
    executed = []
    monkeypatch.setattr(mercury, 'run_query', lambda *args: executed.append(args) or {'final_text':'不应执行','status':'completed'})
    client.app.dependency_overrides[mercury.get_query_model] = lambda: object()
    route(client, base, opening, message='退款政策')
    client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True, 'routing_request_id':'one'})
    route(client, base, opening, request_id='new-intent', role='momo', message='先不处理退款，问问物流')
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    response = client.post('/api/v1/mercury/sessions/' + sid + '/turns/stream', json={'request_id':'one','routing_request_id':'one','message':'退款政策'})
    assert response.status_code == 409, response.text
    assert executed == []


def test_new_intent_between_authorization_and_case_reservation_fences_handoff(navigation_client, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from app.mercury import router as mercury
    from app.mercury.store import CaseStore
    client, base, opening, calls, choice = navigation_client
    ready, proceed = Event(), Event()
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    factory = sessionmaker(bind=db.get_bind(), expire_on_commit=False)
    db_generator.close()
    class PausedStore(CaseStore):
        def reserve_query(self, owner, case_id):
            ready.set()
            assert proceed.wait(5), 'test must release admission'
            return super().reserve_query(owner, case_id)
    client.app.dependency_overrides[mercury.get_case_store] = lambda: PausedStore(factory)
    client.app.dependency_overrides[mercury.get_query_model] = lambda: object()
    executed = []
    monkeypatch.setattr(mercury, 'run_query', lambda *args: executed.append(args) or {'final_text':'不应执行','status':'completed'})
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    route(client, base, opening, message='退款政策')
    client.post(base + '/switches', json={'opening_id':opening['opening_id'], 'target_role':'momo', 'accept':True, 'routing_request_id':'one'})
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(client.post, '/api/v1/mercury/sessions/' + sid + '/turns/stream', json={'request_id':'one','routing_request_id':'one','message':'退款政策'})
        try:
            assert ready.wait(5)
            concurrent_client = TestClient(client.app)
            concurrent_client.cookies.update(client.cookies)
            newer = route(concurrent_client, base, opening, request_id='new-intent', role='momo', message='先不处理退款，问物流')
            concurrent_client.close()
            assert newer.status_code == 200
        finally:
            proceed.set()
        response = pending.result(timeout=10)
    assert response.status_code == 409, response.text
    assert executed == []


def test_order_changed_before_query_admission_cannot_retarget_original_handoff(navigation_client, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timezone
    from threading import Event
    from app.mercury import router as mercury
    from app.mercury.store import CaseStore
    from app.mercury.models import SimulatedOrder
    from app.models.guide import GuideSession
    client, base, opening, calls, choice = navigation_client
    ready, proceed = Event(), Event()
    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    owner_id = db.get(GuideSession, base.rsplit('/',1)[-1]).owner_id
    for oid in ('order-a','order-b'):
        db.add(SimulatedOrder(order_id=oid,owner_id=owner_id,status='paid',snapshot_json='{}',total_fen=100,created_at=datetime.now(timezone.utc)))
    db.commit()
    factory = sessionmaker(bind=db.get_bind(), expire_on_commit=False)
    generator.close()
    class PausedStore(CaseStore):
        def reserve_query(self, owner, case_id):
            ready.set()
            assert proceed.wait(5)
            return super().reserve_query(owner, case_id)
    client.app.dependency_overrides[mercury.get_case_store] = lambda: PausedStore(factory)
    client.app.dependency_overrides[mercury.get_query_model] = lambda: object()
    executed = []
    monkeypatch.setattr(mercury,'run_query',lambda *args:executed.append(args) or {'final_text':'不应查错单','status':'completed'})
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    case_url = '/api/v1/mercury/sessions/' + sid
    assert client.put(case_url + '/order',json={'order_id':'order-a','selection_version':0}).status_code == 200
    assert route(client,base,opening,message='查询这笔订单',selected_object={'kind':'order','id':'order-a'}).status_code == 200
    client.post(base + '/switches',json={'opening_id':opening['opening_id'],'target_role':'momo','accept':True,'routing_request_id':'one'})
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(client.post,case_url + '/turns/stream',json={'request_id':'one','routing_request_id':'one','message':'查询这笔订单'})
        try:
            assert ready.wait(5)
            other = TestClient(client.app)
            other.cookies.update(client.cookies)
            changed = other.put(case_url + '/order',json={'order_id':'order-b','selection_version':1})
            other.close()
            assert changed.status_code == 200, changed.text
        finally:
            proceed.set()
        result = pending.result(timeout=10)
    assert result.status_code == 409, result.text
    assert executed == []


def test_task_changed_after_switch_invalidates_unadmitted_handoff(navigation_client, monkeypatch):
    from app.mercury import router as mercury
    client, base, opening, calls, choice = navigation_client
    executed = []
    monkeypatch.setattr(mercury,'run_query',lambda *args:executed.append(args) or {'final_text':'不应执行','status':'completed'})
    client.app.dependency_overrides[mercury.get_query_model] = lambda: object()
    route(client,base,opening,message='退款政策')
    client.post(base + '/switches',json={'opening_id':opening['opening_id'],'target_role':'momo','accept':True,'routing_request_id':'one'})
    guide_url = base.replace('/navigation/','/guide/')
    changed = client.post(guide_url + '/tasks/current',json={'request_id':'change-goal','kind':'new_goal','goal':'新的选购需求','expected_task_id':None,'expected_state_version':0,'expected_session_version':0})
    assert changed.status_code == 200, changed.text
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']
    result = client.post('/api/v1/mercury/sessions/' + sid + '/turns/stream',json={'request_id':'one','routing_request_id':'one','message':'退款政策'})
    assert result.status_code == 409, result.text
    assert executed == []


def test_manual_retry_can_resume_still_valid_unadmitted_accepted_request(navigation_client):
    client, base, opening, calls, choice = navigation_client
    route(client,base,opening,message='查询原请求')
    first = client.post(base + '/switches',json={'opening_id':opening['opening_id'],'target_role':'momo','accept':True,'routing_request_id':'one'})
    assert first.status_code == 200
    retry = client.post(base + '/switches',json={'opening_id':opening['opening_id'],'target_role':'momo','accept':True})
    assert retry.status_code == 200
    assert retry.json()['handoff'] == first.json()['handoff']
    assert len(calls) == 1


def test_visible_prompt_ack_after_decline_still_consumes_opening_quota(navigation_client):
    client, base, opening, calls, choice = navigation_client
    assert route(client,base,opening).json()['show_prompt']
    declined = client.post(base + '/switches',json={'opening_id':opening['opening_id'],'target_role':'momo','accept':False,'routing_request_id':'one'})
    assert declined.status_code == 200
    ack = client.post(base + '/prompt-displayed',json={'opening_id':opening['opening_id'],'routing_request_id':'one'})
    assert ack.status_code == 200, ack.text
    assert client.get(base + '/opening').json()['prompt_displayed']
    assert not route(client,base,opening,'two').json()['show_prompt']


@pytest.mark.parametrize('capability,original', [
    ('exploration','回到购物，买点零食，预算二十元，再告诉我退货政策'),
    ('purchase_modification','回购物，把清单里的可乐改成两瓶，保留预算条件'),
    ('factual_qa','回购物，告诉我这个包装的规格，再说明一般退货政策'),
    ('chat','回到可可，我们继续刚才的聊天'),
])
def test_explicit_return_with_goal_preserves_original_intent_without_new_prompt(navigation_client, capability, original):
    client, base, opening, calls, choice = navigation_client
    client.post(base + '/switches',json={'opening_id':opening['opening_id'],'target_role':'momo','accept':True})
    choice['value'] = 'return_keke_' + capability
    result = route(client,base,opening,role='momo',message=original).json()
    assert result['status'] == 'navigation', result
    assert result['target_role'] == result['authorized_role'] == 'keke'
    assert result['capability'] == capability
    assert result['continue_original'] and not result['show_prompt']
    restored = client.get(base + '/opening').json()
    assert restored['role'] == 'keke'
    assert restored['handoff']['original_message'] == original
    assert len(calls) == 1
    assert client.get(base.replace('/navigation/','/guide/')).json()['task_id'] is None

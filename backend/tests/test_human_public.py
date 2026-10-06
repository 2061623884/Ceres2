"""TASK15 fresh public HTTP behavior; isolated synthetic owners/operator only."""
import json
from datetime import datetime, timezone
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def human_client(tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.core.database import create_db_engine, get_db, init_db
    from app.models.identity import Owner
    from app.mercury.models import SimulatedOrder
    from app.mercury.router import router as mercury_router
    from app.human.router import router as human_router
    monkeypatch.setattr(get_settings(), 'human_operator_token', 'synthetic-operator-only')
    monkeypatch.setattr(get_settings(), 'mercury_checkpoint_path', tmp_path / 'graph.sqlite3')
    engine = create_db_engine(f'sqlite:///{tmp_path / "human.sqlite3"}')
    init_db(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        db.add_all([Owner(id='human-owner-a'), Owner(id='human-owner-b')]); db.flush()
        db.add(SimulatedOrder(order_id='human-order', owner_id='human-owner-a', status='paid',
            total_fen=1200, created_at=datetime.now(timezone.utc), snapshot_json=json.dumps({'items': [
                {'sku_id': 'cup', 'name': '杯子', 'quantity': 1, 'unit_price_fen': 1200,
                 'returnable': True, 'return_policy_source': 'synthetic'}]})))
        db.commit()
    app = FastAPI(); app.include_router(mercury_router); app.include_router(human_router)
    def database():
        with sessions() as db: yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        client.cookies.set('sg_owner_id', 'human-owner-a')
        sid = client.post('/api/v1/mercury/sessions').json()['session_id']
        url = f'/api/v1/mercury/sessions/{sid}'
        assert client.put(url + '/order', json={'order_id': 'human-order', 'selection_version': 0}).status_code == 200
        yield client, app, url, sessions
    engine.dispose()


def test_explicit_ticket_operator_progress_isolation_and_fence(human_client):
    client, app, url, sessions = human_client
    assert client.get(url + '/human-ticket').json() is None
    before = client.get(url).json()
    created = client.post(url + '/human-ticket', json={'summary': '请人工核实这个问题'})
    assert created.status_code == 200
    ticket = created.json()
    assert ticket['order_id'] == 'human-order' and ticket['order_summary']['items'][0]['name'] == '杯子'
    assert ticket['status'] == 'open'
    assert client.post(url + '/human-ticket', json={'summary': '再次请求人工'}).json()['ticket_id'] == ticket['ticket_id']
    hold = client.get(url).json()
    assert hold['responsibility'] == 'human' and hold['responsibility_generation'] > before['responsibility_generation']
    assert client.post(url + '/turns/stream', json={'message': '退款', 'request_id': 'held'}).status_code == 409
    assert client.get('/api/v1/mercury/operator/tickets').status_code == 403
    client.cookies.set('sg_owner_id', 'human-owner-b')
    assert client.get(url + '/human-ticket').status_code == 404
    assert client.post(url + '/human-ticket/messages', json={'ticket_id': ticket['ticket_id'], 'content': '偷改', 'version': 1}).status_code == 404
    operator = {'X-Internal-Token': 'synthetic-operator-only'}
    listing = client.get('/api/v1/mercury/operator/tickets', headers=operator).json()
    assert len(listing) == 1
    target = f"/api/v1/mercury/operator/tickets/{ticket['ticket_id']}/messages"
    asked = client.post(target, headers=operator, json={'action': 'ask', 'content': '请补充问题细节', 'version': ticket['version']})
    assert asked.status_code == 200 and asked.json()['status'] == 'waiting_user'
    client.cookies.set('sg_owner_id', 'human-owner-a')
    progress = client.get(url + '/human-ticket').json()
    assert progress['messages'][-1]['content'] == '请补充问题细节'
    replied = client.post(url + '/human-ticket/messages', json={'ticket_id': progress['ticket_id'], 'content': '这是补充细节', 'version': progress['version']}).json()
    assert replied['status'] == 'open'
    resolved = client.post(target, headers=operator, json={'action': 'resolve', 'content': '问题已解释清楚，无退款操作', 'version': replied['version']})
    assert resolved.status_code == 200 and resolved.json()['status'] == 'resolved'
    after = client.get(url).json()
    assert after['responsibility'] == 'agent' and after['responsibility_generation'] > hold['responsibility_generation']
    assert client.post(target, headers=operator, json={'action': 'reply', 'content': '过期回复', 'version': replied['version']}).status_code == 409
    from app.mercury.models import SimulatedOrder
    with sessions() as db: assert db.get(SimulatedOrder, 'human-order').status == 'paid'


@pytest.mark.parametrize('failure_type', [RuntimeError, TimeoutError])
def test_policy_unknown_and_repeated_service_failure_trigger_from_actual_graph(human_client, failure_type):
    from types import SimpleNamespace
    from app.mercury.router import get_query_model, get_order_service
    from app.mercury.models import SimulatedOrder
    client, app, url, sessions = human_client
    class BrokenModel:
        def chat(self, messages, tools=None):
            return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='read', function=SimpleNamespace(
                name='get_order_details', arguments='{\"order_id\":\"human-order\"}'))])
        def cancel(self): pass
    class BrokenService:
        def read(self, name, owner_id, order_id): raise failure_type('synthetic business service unavailable')
    app.dependency_overrides[get_order_service] = BrokenService
    app.dependency_overrides[get_query_model] = BrokenModel
    client.post(url + '/turns/stream', json={'message': '查询退款资格', 'request_id': 'failure-1'})
    assert client.get(url + '/human-ticket').json() is None
    client.post(url + '/turns/stream', json={'message': '重试', 'request_id': 'failure-2'})
    ticket = client.get(url + '/human-ticket').json()
    assert ticket is not None and ticket['reason'] == 'persistent_service_failure'
    assert client.get(url).json()['responsibility'] == 'human'
    app.dependency_overrides.pop(get_order_service)
    sid = client.post('/api/v1/mercury/sessions').json()['session_id']; other = f'/api/v1/mercury/sessions/{sid}'
    assert client.put(other + '/order', json={'order_id': 'human-order', 'selection_version': 0}).status_code == 200
    with sessions() as db:
        order = db.get(SimulatedOrder, 'human-order'); order.status = 'delivered'; order.delivered_at = datetime.now(timezone.utc)
        data = json.loads(order.snapshot_json); data['items'][0]['returnable'] = None
        order.snapshot_json = json.dumps(data); db.commit()
    class PolicyModel:
        def chat(self, messages, tools=None):
            if messages[-1]['role'] == 'tool': return SimpleNamespace(content='done', tool_calls=[])
            return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='policy', function=SimpleNamespace(
                name='check_return_eligibility', arguments='{"order_id":"human-order"}'))])
        def cancel(self): pass
    app.dependency_overrides[get_query_model] = PolicyModel
    client.post(other + '/turns/stream', json={'message': '退货资格', 'request_id': 'unknown'})
    assert client.get(other + '/human-ticket').json()['reason'] == 'policy_indeterminate'


def test_operator_requires_separate_credential_and_rejects_stale_actions(human_client, monkeypatch):
    from app.core.config import get_settings
    client, app, url, sessions = human_client
    settings = get_settings()
    monkeypatch.setattr(settings, 'openai_api_key', 'synthetic-provider-key')
    assert client.get('/api/v1/mercury/operator/tickets', headers={'X-Internal-Token': 'synthetic-provider-key'}).status_code == 403
    monkeypatch.setattr(settings, 'human_operator_token', 'synthetic-provider-key')
    assert client.get('/api/v1/mercury/operator/tickets', headers={'X-Internal-Token': 'synthetic-provider-key'}).status_code == 403
    monkeypatch.setattr(settings, 'human_operator_token', '')
    assert client.get('/api/v1/mercury/operator/tickets', headers={'X-Internal-Token': ''}).status_code == 403
    monkeypatch.setattr(settings, 'human_operator_token', 'synthetic-operator-only')
    assert client.post(url + '/human-ticket', json={'summary': '  '}).status_code == 422
    assert client.post(url + '/human-ticket', json={'summary': 'help', 'owner_id': 'human-owner-b'}).status_code == 422
    ticket = client.post(url + '/human-ticket', json={'summary': '请人工处理'}).json()
    target = f"/api/v1/mercury/operator/tickets/{ticket['ticket_id']}/messages"
    headers = {'X-Internal-Token': 'synthetic-operator-only'}
    assert client.post(target, headers=headers, json={'action': 'refund', 'content': '退款', 'version': 1}).status_code == 422
    answer = client.post(target, headers=headers, json={'action': 'reply', 'content': '仅回复', 'version': 1}).json()
    assert answer['status'] == 'open' and client.get(url).json()['responsibility'] == 'human'
    assert client.post(target, headers=headers, json={'action': 'close', 'content': '旧版本', 'version': 1}).status_code == 409
    closed = client.post(target, headers=headers, json={'action': 'close', 'content': '已说明，关闭', 'version': answer['version']}).json()
    assert closed['status'] == 'closed'
    reopened = client.post(url + '/human-ticket', json={'summary': '新问题'}).json()
    assert reopened['ticket_id'] != ticket['ticket_id'] and reopened['generation'] > closed['generation']


def test_ineligibility_clarification_and_invalid_model_arguments_do_not_handoff(human_client):
    from types import SimpleNamespace
    from app.mercury.router import get_query_model
    from app.mercury.models import SimulatedOrder
    client, app, url, sessions = human_client
    with sessions() as db:
        order = db.get(SimulatedOrder, 'human-order'); order.status = 'shipped'; db.commit()
    class Model:
        name = 'check_refund_eligibility'
        arguments = '{"order_id":"human-order"}'
        def chat(self, messages, tools=None):
            if messages[-1]['role'] == 'tool': return SimpleNamespace(content='done', tool_calls=[])
            return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='read', function=SimpleNamespace(name=self.name, arguments=self.arguments))])
        def cancel(self): pass
    model = Model(); app.dependency_overrides[get_query_model] = lambda: model
    client.post(url + '/turns/stream', json={'message': '退款资格', 'request_id': 'ineligible'})
    assert client.get(url + '/human-ticket').json() is None
    model.name = 'request_clarification'; model.arguments = '{"slot":"item"}'
    client.post(url + '/turns/stream', json={'message': '咨询', 'request_id': 'clarification'})
    assert client.get(url).json()['status'] == 'awaiting_details'
    assert client.get(url + '/human-ticket').json() is None
    model.name = 'get_order_details'; model.arguments = '{bad'
    for index in range(2):
        client.post(url + '/turns/stream', json={'message': '杯子', 'request_id': f'invalid-{index}'})
    assert client.get(url + '/human-ticket').json() is None


def test_handoff_fences_inflight_query_publication_and_survives_restart(human_client):
    from app.mercury.store import CaseStore
    client, app, url, sessions = human_client
    case_id = url.rsplit('/', 1)[1]; store = CaseStore(sessions)
    old = store.read_case('human-owner-a', case_id)
    run = store.reserve_query('human-owner-a', case_id)
    ticket = client.post(url + '/human-ticket', json={'summary': '现在请人工处理'}).json()
    assert not store.publish_result('human-owner-a', old, run, {'status': 'completed',
        'messages': [{'role': 'assistant', 'content': 'STALE RESPONSE'}], 'rounds': 1})
    with TestClient(app) as restarted:
        restarted.cookies.set('sg_owner_id', 'human-owner-a')
        assert restarted.get(url + '/human-ticket').json()['ticket_id'] == ticket['ticket_id']
        case = restarted.get(url).json()
        assert case['responsibility'] == 'human'
        assert not any('STALE RESPONSE' in message['content'] for message in case['messages'])


def test_additive_schema_repeat_preserves_old_synthetic_facts(tmp_path):
    from sqlalchemy import text, inspect
    from app.core.database import create_db_engine, init_db
    engine = create_db_engine(f'sqlite:///{tmp_path / "old-synthetic-human.sqlite3"}')
    with engine.begin() as db:
        db.execute(text('CREATE TABLE existing_business_fact (id INTEGER PRIMARY KEY, value TEXT)'))
        db.execute(text("INSERT INTO existing_business_fact VALUES (1, 'keep-before-human')"))
    init_db(engine); init_db(engine)
    with engine.connect() as db:
        assert db.execute(text('SELECT value FROM existing_business_fact')).scalar_one() == 'keep-before-human'
        assert db.execute(text('SELECT count(*) FROM human_tickets')).scalar_one() == 0
        assert db.execute(text("SELECT count(*) FROM schema_migrations WHERE version='0015_async_human_tickets'")).scalar_one() == 1
    assert {'human_tickets', 'human_handoff_states'}.issubset(inspect(engine).get_table_names())
    engine.dispose()


def test_provider_failure_does_not_auto_escalate_and_application_routes_exist(human_client):
    from app.mercury.router import get_query_model
    from app.main import create_app
    from app.core.database import get_db
    client, app, url, sessions = human_client
    class BrokenProvider:
        def chat(self, messages, tools=None): raise RuntimeError('synthetic provider outage')
        def cancel(self): pass
    app.dependency_overrides[get_query_model] = BrokenProvider
    for index in range(2):
        response = client.post(url + '/turns/stream', json={'message': '查询', 'request_id': f'provider-{index}'})
        assert 'query_failed' in response.text
    assert client.get(url + '/human-ticket').json() is None
    application = create_app(sessions.kw['bind'])
    application.dependency_overrides[get_db] = app.dependency_overrides[get_db]
    with TestClient(application) as composed:
        composed.cookies.set('sg_owner_id', 'human-owner-a')
        assert composed.get(url + '/human-ticket').status_code == 200
        assert composed.get('/api/v1/mercury/operator/tickets').status_code == 403


def test_concurrent_duplicate_requests_have_one_open_ticket(human_client):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from app.human.models import HumanTicket
    client, app, url, sessions = human_client
    barrier = Barrier(2)
    def request():
        with TestClient(app) as other:
            other.cookies.set('sg_owner_id', 'human-owner-a')
            barrier.wait()
            result = other.post(url + '/human-ticket', json={'summary': '同一个问题请人工处理'})
            assert result.status_code == 200
            return result.json()['ticket_id']
    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = pool.submit(request), pool.submit(request)
        assert a.result() == b.result()
    with sessions() as db: assert db.query(HumanTicket).count() == 1


@pytest.mark.parametrize('arguments', ['{"query":"   "}', '{"query":"退货","category":"invented"}'])
def test_malformed_policy_lookup_does_not_claim_policy_uncertainty(human_client, arguments):
    from types import SimpleNamespace
    from app.mercury.router import get_query_model
    client, app, url, sessions = human_client
    class Model:
        def chat(self, messages, tools=None):
            if messages[-1]['role'] == 'tool': return SimpleNamespace(content='done', tool_calls=[])
            return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='bad-policy', function=SimpleNamespace(
                name='search_after_sales_policy', arguments=arguments))])
        def cancel(self): pass
    app.dependency_overrides[get_query_model] = Model
    client.post(url + '/turns/stream', json={'message': '咨询政策', 'request_id': 'malformed-policy'})
    assert client.get(url + '/human-ticket').json() is None
    assert client.get(url).json()['status'] == 'query_failed'


def test_old_user_draft_cannot_reply_into_replacement_ticket(human_client):
    client, app, url, sessions = human_client
    old = client.post(url + '/human-ticket', json={'summary': '旧事项'}).json()
    headers = {'X-Internal-Token': 'synthetic-operator-only'}
    assert client.post(f"/api/v1/mercury/operator/tickets/{old['ticket_id']}/messages", headers=headers,
        json={'action': 'close', 'content': '旧事项已关闭', 'version': old['version']}).status_code == 200
    new = client.post(url + '/human-ticket', json={'summary': '新事项'}).json()
    assert new['ticket_id'] != old['ticket_id'] and new['version'] == old['version']
    stale_body = {'content': '旧标签页里正在写的消息', 'version': old['version']}
    assert client.post(url + '/human-ticket/messages', json=stale_body).status_code in (409, 422)
    assert client.post(url + '/human-ticket/messages', json={**stale_body, 'ticket_id': old['ticket_id']}).status_code == 409
    assert client.get(url + '/human-ticket').json()['messages'] == []

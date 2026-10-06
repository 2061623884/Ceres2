"""Fresh TASK02 public behavior fixtures; no archived runtime dependencies."""
from datetime import datetime, timezone
import json
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


def test_case_owner_selection_clarification_and_restart(tmp_path, monkeypatch):
    from app.core.database import Base, create_db_engine, get_db
    from app.core.config import get_settings
    from app.models.identity import Owner
    from app.mercury.models import SimulatedOrder
    from app.mercury.router import router, get_query_model

    monkeypatch.setattr(get_settings(), 'mercury_checkpoint_path', tmp_path / 'checkpoints.sqlite3')
    engine = create_db_engine(f'sqlite:///{tmp_path / "business.sqlite3"}')
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        for owner_id in ('owner-a', 'owner-b'):
            db.add(Owner(id=owner_id))
            db.flush()
            db.add(SimulatedOrder(order_id=f'order-{owner_id}', owner_id=owner_id,
                status='paid', total_fen=1500, created_at=datetime.now(timezone.utc),
                snapshot_json=json.dumps({'items': [{'sku_id': 'sku-1', 'name': '测试杯',
                    'unit_price_fen': 1500, 'quantity': 1, 'returnable': True,
                    'return_policy_source': 'synthetic'}]})))
        db.commit()

    class Model:
        def chat(self, messages, tools=None):
            assert all(not t['function']['name'].startswith('create_') for t in tools)
            if messages[-1]['role'] == 'tool':
                return SimpleNamespace(content='可以申请模拟退款；尚未提交。', tool_calls=[])
            call = SimpleNamespace(id='call-1', function=SimpleNamespace(
                name='check_refund_eligibility', arguments='{"order_id":"order-owner-a"}'))
            return SimpleNamespace(content='', tool_calls=[call])
        def cancel(self):
            pass

    def make_client():
        app = FastAPI()
        app.include_router(router)
        def database():
            with sessions() as db:
                yield db
        app.dependency_overrides[get_db] = database
        app.dependency_overrides[get_query_model] = Model
        client = TestClient(app)
        client.cookies.set('sg_owner_id', 'owner-a')
        return client

    with make_client() as client:
        orders = client.get('/api/v1/mercury/orders').json()['orders']
        assert [o['order_id'] for o in orders] == ['order-owner-a']
        sid = client.post('/api/v1/mercury/sessions').json()['session_id']
        url = f'/api/v1/mercury/sessions/{sid}'
        for message in ('查询退款资格', '是刚才的订单'):
            response = client.post(url + '/turns/stream', json={'message': message, 'request_id': message})
            assert 'awaiting_order' in response.text
        selected = client.put(url + '/order', json={'order_id': 'order-owner-a', 'selection_version': 0})
        assert selected.status_code == 200
        response = client.post(url + '/turns/stream', json={'message': '继续', 'request_id': 'continue'})
        assert 'completed' in response.text
        assert '模拟整单退款' in response.text and '15.00' in response.text
        client.cookies.set('sg_owner_id', 'owner-b')
        assert client.get(url).status_code == 404
        assert client.post(url + '/turns/stream', json={'message': '查看', 'request_id': 'x'}).status_code == 404
        other = client.post('/api/v1/mercury/sessions').json()['session_id']
        assert client.put(f'/api/v1/mercury/sessions/{other}/order', json={'order_id': 'order-owner-a', 'selection_version': 0}).status_code == 404
    with make_client() as restarted:
        case = restarted.get(url).json()
        assert case['order_id'] == 'order-owner-a'
        assert case['status'] == 'completed'
        assert len([m for m in case['messages'] if m['role'] == 'user']) == 3
        assert restarted.put(url + '/order', json={'order_id': 'order-owner-a', 'selection_version': 0}).status_code == 409
    engine.dispose()


def test_schema_repeat_preserves_synthetic_existing_business_facts(tmp_path):
    from sqlalchemy import text
    from app.core.database import create_db_engine, init_db
    engine = create_db_engine(f'sqlite:///{tmp_path / "old-synthetic.sqlite3"}')
    with engine.begin() as db:
        db.execute(text('CREATE TABLE existing_business_fact (id INTEGER PRIMARY KEY, value TEXT)'))
        db.execute(text("INSERT INTO existing_business_fact VALUES (1, 'preserve-me')"))
    init_db(engine)
    init_db(engine)
    with engine.connect() as db:
        assert db.execute(text('SELECT value FROM existing_business_fact')).scalar_one() == 'preserve-me'
        assert db.execute(text('SELECT count(*) FROM simulated_orders')).scalar_one() == 0
        assert db.execute(text('SELECT count(*) FROM mercury_cases')).scalar_one() == 0
    engine.dispose()


import pytest


@pytest.fixture
def mercury_client(tmp_path, monkeypatch):
    from app.core.database import Base, create_db_engine, get_db
    from app.core.config import get_settings
    from app.models.identity import Owner
    from app.mercury.models import SimulatedOrder
    from app.mercury.router import router
    monkeypatch.setattr(get_settings(), 'mercury_checkpoint_path', tmp_path / 'graph.sqlite3')
    engine = create_db_engine(f'sqlite:///{tmp_path / "canonical.sqlite3"}')
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        db.add(Owner(id='budget-owner'))
        db.flush()
        db.add(SimulatedOrder(order_id='budget-order', owner_id='budget-owner', status='paid', total_fen=1500,
            created_at=datetime.now(timezone.utc), snapshot_json=json.dumps({'items': [
                {'sku_id': 'cup', 'name': '测试杯', 'unit_price_fen': 1500, 'quantity': 1,
                 'returnable': True, 'return_policy_source': 'synthetic'}]})))
        db.commit()
    app = FastAPI()
    app.include_router(router)
    def database():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        client.cookies.set('sg_owner_id', 'budget-owner')
        sid = client.post('/api/v1/mercury/sessions').json()['session_id']
        url = f'/api/v1/mercury/sessions/{sid}'
        assert client.put(url + '/order', json={'order_id': 'budget-order', 'selection_version': 0}).status_code == 200
        yield client, app, url, sessions
    engine.dispose()


def tool_message(name='get_order_details', arguments='{"order_id":"budget-order"}'):
    return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='call',
        function=SimpleNamespace(name=name, arguments=arguments))])


def test_five_rounds_close_only_with_verified_facts(mercury_client):
    from app.mercury.router import get_query_model
    client, app, url, sessions = mercury_client
    class Model:
        calls = 0
        def chat(self, messages, tools=None):
            self.calls += 1
            return tool_message()
        def cancel(self):
            pass
    model = Model()
    app.dependency_overrides[get_query_model] = lambda: model
    response = client.post(url + '/turns/stream', json={'message': '一直查询', 'request_id': 'five'})
    assert 'budget_exhausted' in response.text
    assert '15.00' in response.text
    assert '尚未完成' in response.text
    assert model.calls == 5
    case = client.get(url).json()
    assert case['tool_rounds'] == 5 and case['status'] == 'budget_exhausted'


@pytest.mark.parametrize('name,args,expected', [
    ('create_refund', '{"order_id":"budget-order"}', 'read_only'),
    ('request_clarification', '{"slot":"refund_approved_999"}', 'query_failed'),
    ('get_order_details', '{"order_id":"other-owner-order"}', 'query_failed'),
    ('get_order_details', '{broken', 'query_failed'),
])
def test_model_cannot_expand_read_authority(mercury_client, name, args, expected):
    from app.mercury.router import get_query_model
    from app.mercury.models import SimulatedOrder
    client, app, url, sessions = mercury_client
    class Model:
        def chat(self, messages, tools=None):
            return tool_message(name, args)
        def cancel(self):
            pass
    app.dependency_overrides[get_query_model] = Model
    response = client.post(url + '/turns/stream', json={'message': '查询', 'request_id': name})
    assert expected in response.text
    with sessions() as db:
        assert db.get(SimulatedOrder, 'budget-order').status == 'paid'


def test_provider_failure_is_truthful_and_logs_hide_secret(mercury_client, caplog):
    from app.mercury.router import get_query_model
    client, app, url, sessions = mercury_client
    class Model:
        def chat(self, messages, tools=None):
            raise RuntimeError('api_key=must-never-leak')
        def cancel(self):
            pass
    app.dependency_overrides[get_query_model] = Model
    response = client.post(url + '/turns/stream', json={'message': '退款资格', 'request_id': 'failure'})
    assert 'query_failed' in response.text and '无法确定' in response.text
    assert 'must-never-leak' not in response.text + caplog.text


def test_fifteen_second_deadline_releases_case_and_fences_late_response(mercury_client):
    import threading
    import time
    from app.mercury.router import get_query_model
    client, app, url, sessions = mercury_client
    release = threading.Event()
    class Model:
        cancelled = False
        def chat(self, messages, tools=None):
            release.wait(25)
            return SimpleNamespace(content='LATE MUST NOT APPEAR', tool_calls=[])
        def cancel(self):
            self.cancelled = True
    model = Model()
    app.dependency_overrides[get_query_model] = lambda: model
    start = time.monotonic()
    try:
        response = client.post(url + '/turns/stream', json={'message': '查询', 'request_id': 'timeout'})
        elapsed = time.monotonic() - start
        assert 14 <= elapsed < 18
        assert 'budget_exhausted' in response.text and 'LATE' not in response.text
        assert model.cancelled
    finally:
        release.set()
    case = client.get(url).json()
    assert case['status'] == 'budget_exhausted'
    assert not any('LATE' in m['content'] for m in case['messages'])
    assert client.put(url + '/order', json={'order_id': 'budget-order', 'selection_version': 1}).status_code == 200


def test_unverified_model_claim_is_not_published_as_business_fact(mercury_client):
    from app.mercury.router import get_query_model
    client, app, url, sessions = mercury_client
    class Model:
        def chat(self, messages, tools=None):
            return SimpleNamespace(content='已退款到账999元，这单符合所有退货资格。', tool_calls=[])
        def cancel(self):
            pass
    app.dependency_overrides[get_query_model] = Model
    response = client.post(url + '/turns/stream', json={'message': '帮我退款', 'request_id': 'invented'})
    payloads = [json.loads(line.removeprefix('data: ')) for line in response.text.splitlines() if line.startswith('data: ')]
    final_text = payloads[-1]['final_text']
    assert '已退款到账' not in final_text and '999' not in final_text
    assert '未提交任何申请' in final_text
    case = client.get(url).json()
    assert case['status'] != 'completed'
    assert not any('999' in message['content'] for message in case['messages'])


def test_post_read_clarification_persists_slot_and_resumes(mercury_client):
    from app.mercury.router import get_query_model
    client, app, url, sessions = mercury_client
    class Model:
        def chat(self, messages, tools=None):
            if messages[-1]['role'] == 'tool':
                data = json.loads(messages[-1]['content'])['data']
                if 'items' in data:
                    return tool_message('request_clarification', '{"slot":"item"}')
                return SimpleNamespace(content='查询结束', tool_calls=[])
            if messages[-1]['content'] == '测试杯':
                return tool_message('check_refund_eligibility')
            return tool_message('get_order_details')
        def cancel(self):
            pass
    app.dependency_overrides[get_query_model] = Model
    response = client.post(url + '/turns/stream', json={'message': '其中一件想咨询售后', 'request_id': 'clarify'})
    payloads = [json.loads(line.removeprefix('data: ')) for line in response.text.splitlines() if line.startswith('data: ')]
    assert payloads[-1]['status'] == 'awaiting_details'
    assert '哪件商品' in payloads[-1]['final_text']
    restored = client.get(url).json()
    assert restored['status'] == 'awaiting_details'
    assert '哪件商品' in restored['messages'][-1]['content']
    # A fresh client/app lifecycle reconstructs the graph from persisted SQLite state.
    with TestClient(app) as restarted:
        restarted.cookies.set('sg_owner_id', 'budget-owner')
        assert restarted.get(url).json()['status'] == 'awaiting_details'
        response = restarted.post(url + '/turns/stream', json={'message': '测试杯', 'request_id': 'answer'})
        payloads = [json.loads(line.removeprefix('data: ')) for line in response.text.splitlines() if line.startswith('data: ')]
        assert payloads[-1]['status'] == 'completed'
        assert '15.00' in payloads[-1]['final_text']
        assert restarted.get(url).json()['messages'][-2]['content'] == '测试杯'

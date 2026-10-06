"""TASK14 fresh public HTTP contracts, fixed UTC facts and separate owners."""
import json
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.core.database import create_db_engine, get_db, init_db
from app.core.config import get_settings
from app.main import create_app
from app.mercury.models import MercuryCase, SimulatedOrder

NOW = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)

@pytest.fixture
def web(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), 'mercury_checkpoint_path', tmp_path / 'graph.sqlite')
    from app.mercury import orders
    monkeypatch.setattr(orders, 'utc_now', lambda: NOW)
    engine = create_db_engine(f"sqlite:///{tmp_path / 'business.sqlite'}")
    init_db(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    app = create_app(database_engine=engine)
    def database():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with TestClient(app, raise_server_exceptions=False) as client:
        client.get('/api/v1/bootstrap')
        sid = client.post('/api/v1/mercury/sessions').json()['session_id']
        with sessions.begin() as db:
            owner = db.get(MercuryCase, sid).owner_id
            for oid, status, days, returnable in [('normal', 'submitted', None, True), ('signed', 'delivered', 7, True), ('expired', 'delivered', 8, True), ('denied', 'delivered', 1, False)]:
                db.add(SimulatedOrder(order_id=oid, owner_id=owner, status=status, version=1,
                    total_fen=1234, created_at=NOW-timedelta(days=10),
                    delivered_at=NOW-timedelta(days=days) if days else None,
                    snapshot_json=json.dumps({'items':[{'sku_id':'sku', 'name':'面粉', 'quantity':2, 'unit_price_fen':617, 'returnable':returnable,'return_policy_source':'fixture'}]})))
        url = '/api/v1/mercury/sessions/' + sid
        assert client.put(url+'/order', json={'order_id':'normal','selection_version':0}).status_code == 200
        yield client, sessions, url
    engine.dispose()


def proposal(client, url, kind='refund', version=1, reason='不需要了', item_id=None):
    return client.post(url+'/proposals', json={'kind':kind,'item_id':item_id,'reason':reason,'selection_version':version})


def confirm(client, url, pid, key='one', **extra):
    return client.post(url+'/confirm', json={'proposal_id':pid,'idempotency_key':key,'confirmed':True,**extra})


def test_preview_confirmation_and_replay(web):
    client, _, url = web
    response = proposal(client,url)
    assert response.status_code == 200, response.text
    p = response.json()
    assert p['status'] == 'awaiting_confirmation'
    assert p['amount_fen'] == 1234 and p['items'][0]['quantity'] == 2
    assert p['reason'] == '不需要了' and p['policy_id'] == 'P-REF-01'
    assert client.get(url+'/aftersales').json()['receipts'] == []
    assert confirm(client,url,p['proposal_id'],confirmed=False).status_code == 422
    result = confirm(client,url,p['proposal_id'])
    assert result.status_code == 200, result.text
    receipt = result.json()
    assert receipt['status'] == 'requested' and receipt['simulated'] is True
    assert confirm(client,url,p['proposal_id']).json() == receipt
    assert confirm(client,url,p['proposal_id'],key='different').status_code == 409
    assert len(client.get(url+'/aftersales').json()['receipts']) == 1
    assert proposal(client,url).status_code == 409


def test_old_proposal_selection_and_key_conflicts(web):
    client, _, url = web
    old = proposal(client,url).json()['proposal_id']
    new = proposal(client,url,reason='改原因').json()['proposal_id']
    assert confirm(client,url,old).status_code == 409
    assert confirm(client,url,new).status_code == 200
    assert confirm(client,url,old).status_code == 409
    assert client.put(url+'/order',json={'order_id':'signed','selection_version':1}).status_code == 200
    p = proposal(client,url,'return',2,item_id='sku').json()['proposal_id']
    assert client.put(url+'/order',json={'order_id':'normal','selection_version':2}).status_code == 200
    assert confirm(client,url,p,key='return').status_code == 409


@pytest.mark.parametrize('oid,expected',[('signed',200),('expired',409),('denied',409)])
def test_return_policy_whole_line_only(web,oid,expected):
    client, _, url = web
    client.put(url+'/order',json={'order_id':oid,'selection_version':1})
    response=proposal(client,url,'return',2,item_id='sku')
    assert response.status_code == expected, response.text
    if expected == 200:
        assert response.json()['items'][0]['quantity'] == 2
        assert confirm(client,url,response.json()['proposal_id']).status_code == 200
        assert proposal(client,url,'return',2,item_id='sku').status_code == 409


def test_owner_human_and_late_facts_fences(web):
    client,sessions,url=web
    p=proposal(client,url).json()['proposal_id']
    with sessions.begin() as db:
        row=db.get(SimulatedOrder,'normal'); row.status='shipped'; row.version+=1
    assert confirm(client,url,p).status_code == 409
    with sessions.begin() as db:
        row=db.get(SimulatedOrder,'normal'); row.status='submitted'; row.version+=1
    p=proposal(client,url).json()['proposal_id']
    with sessions.begin() as db:
        case=db.get(MercuryCase,url.split('/')[-1]); case.responsibility='human'; case.responsibility_generation+=1
    assert confirm(client,url,p).status_code == 409
    client.cookies.clear(); client.get('/api/v1/bootstrap')
    assert client.get(url+'/aftersales').status_code == 404
    assert confirm(client,url,p).status_code == 404


def test_real_graph_interrupt_model_proposal_never_submits(web):
    from types import SimpleNamespace
    from app.mercury.router import get_query_model
    from app.mercury.aftersales_graph import application_graph
    from app.mercury.aftersales import AfterSalesService
    client,sessions,url=web
    class Model:
        def chat(self,messages,tools=None):
            assert not any(t['function']['name'] in ('submit','create_refund','confirm_aftersales') for t in tools)
            return SimpleNamespace(content='',tool_calls=[SimpleNamespace(id='proposal',function=SimpleNamespace(
                name='prepare_aftersales_proposal',arguments=json.dumps({'order_id':'normal','kind':'refund','reason':'不需要了'})))])
        def cancel(self): pass
    client.app.dependency_overrides[get_query_model]=Model
    response=client.post(url+'/turns/stream',json={'message':'我要退款，不需要了','request_id':'first'})
    assert 'awaiting_confirmation' in response.text, response.text
    saved=client.get(url+'/aftersales').json()
    assert saved['receipts'] == []
    pid=saved['proposal']['proposal_id']; sid=url.split('/')[-1]
    with sessions() as db: owner=db.get(MercuryCase,sid).owner_id
    with application_graph(AfterSalesService(sessions),owner,sid) as graph:
        assert graph.get_state({'configurable':{'thread_id':f'aftersales:{sid}:{pid}'}}).next == ('await_confirmation',)
    assert confirm(client,url,pid).status_code == 200


def test_atomic_precommit_failure_then_retry(web,monkeypatch):
    from sqlalchemy.orm import Session
    from app.mercury.aftersales_models import AfterSalesApplication,AfterSalesReceipt
    client,sessions,url=web
    pid=proposal(client,url).json()['proposal_id']
    original=Session.commit
    def fail_commit(db):
        if any(isinstance(row,AfterSalesReceipt) for row in db.new):
            raise RuntimeError('approved unit-of-work precommit fault')
        return original(db)
    with monkeypatch.context() as patch:
        patch.setattr(Session,'commit',fail_commit)
        assert confirm(client,url,pid).status_code == 500
    with sessions() as db:
        assert db.query(AfterSalesApplication).count() == 0
        assert db.query(AfterSalesReceipt).count() == 0
    assert confirm(client,url,pid).status_code == 200


def test_committed_receipt_survives_response_and_checkpoint_loss(web,monkeypatch):
    from app.mercury.aftersales import AfterSalesService
    client,_,url=web
    pid=proposal(client,url).json()['proposal_id']
    submit=AfterSalesService.submit
    def lost_response(self,*args):
        submit(self,*args)
        raise RuntimeError('approved postcommit response/checkpoint fault')
    with monkeypatch.context() as patch:
        patch.setattr(AfterSalesService,'submit',lost_response)
        assert confirm(client,url,pid).status_code == 500
    receipts=client.get(url+'/aftersales').json()['receipts']
    assert len(receipts)==1
    # Business receipt replay does not require any graph checkpoint recovery.
    get_settings().mercury_checkpoint_path.unlink()
    assert confirm(client,url,pid).json() == receipts[0]


def test_simultaneous_confirmation_has_one_receipt(web):
    from concurrent.futures import ThreadPoolExecutor
    client,sessions,url=web
    pid=proposal(client,url).json()['proposal_id']
    with ThreadPoolExecutor(max_workers=2) as workers:
        results=list(workers.map(lambda _:confirm(client,url,pid),range(2)))
    assert [r.status_code for r in results] == [200,200], [r.text for r in results]
    assert results[0].json()==results[1].json()
    from app.mercury.aftersales_models import AfterSalesApplication
    with sessions() as db: assert db.query(AfterSalesApplication).count()==1


def test_return_window_expires_between_preview_and_confirmation(web,monkeypatch):
    from app.mercury import orders
    client,_,url=web
    client.put(url+'/order',json={'order_id':'signed','selection_version':1})
    pid=proposal(client,url,'return',2,item_id='sku').json()['proposal_id']
    monkeypatch.setattr(orders,'utc_now',lambda:NOW+timedelta(microseconds=1))
    assert confirm(client,url,pid).status_code == 409
    assert client.get(url+'/aftersales').json()['receipts']==[]


def test_application_read_eligibility_and_immutable_order_snapshot(web):
    from app.mercury.orders import MercuryOrderService
    client,sessions,url=web
    with sessions() as db:
        original=db.get(SimulatedOrder,'normal').snapshot_json
        owner=db.get(MercuryCase,url.split('/')[-1]).owner_id
    pid=proposal(client,url).json()['proposal_id']
    receipt=confirm(client,url,pid).json()
    service=MercuryOrderService(sessions)
    assert service.read('check_refund_eligibility',owner,'normal')['data']['eligible'] is False
    assert service.read('get_refund_status',owner,'normal')['data']==[receipt]
    with sessions() as db:
        assert db.get(SimulatedOrder,'normal').snapshot_json==original
        assert db.get(SimulatedOrder,'normal').status=='submitted'


def test_no_partial_quantity_unknown_item_or_foreign_proposal(web):
    client,_,url=web
    assert client.post(url+'/proposals',json={'kind':'refund','item_id':'sku','reason':'x','selection_version':1}).status_code==422
    assert client.post(url+'/proposals',json={'kind':'refund','quantity':1,'reason':'x','selection_version':1}).status_code==422
    client.put(url+'/order',json={'order_id':'signed','selection_version':1})
    assert proposal(client,url,'return',2,item_id='unknown').status_code==404
    assert proposal(client,url,'return',2).status_code==422
    assert confirm(client,url,'foreign-proposal').status_code==404


def test_already_refunded_and_unknown_return_policy_do_not_submit(web):
    client,sessions,url=web
    with sessions.begin() as db:
        db.get(SimulatedOrder,'normal').status='refunded'
        signed=db.get(SimulatedOrder,'signed'); snapshot=json.loads(signed.snapshot_json)
        snapshot['items'][0]['returnable']=None; signed.snapshot_json=json.dumps(snapshot)
    assert proposal(client,url).status_code==409
    client.put(url+'/order',json={'order_id':'signed','selection_version':1})
    assert proposal(client,url,'return',2,item_id='sku').status_code==409
    assert client.get(url+'/aftersales').json()['receipts']==[]


def test_late_model_proposal_cannot_cross_human_generation(web,monkeypatch):
    from threading import Event
    from concurrent.futures import ThreadPoolExecutor
    from types import SimpleNamespace
    from app.mercury.router import get_query_model
    client,_,url=web
    entered,release=Event(),Event()
    monkeypatch.setattr(get_settings(),'human_operator_token','fixture-operator')
    class Model:
        def chat(self,messages,tools=None):
            entered.set(); assert release.wait(5)
            return SimpleNamespace(content='',tool_calls=[SimpleNamespace(id='late',function=SimpleNamespace(
                name='prepare_aftersales_proposal',arguments=json.dumps({'order_id':'normal','kind':'refund','reason':'不需要'})))])
        def cancel(self): pass
    client.app.dependency_overrides[get_query_model]=Model
    with ThreadPoolExecutor(max_workers=1) as pool:
        running=pool.submit(lambda:client.post(url+'/turns/stream',json={'message':'申请退款','request_id':'late'}))
        assert entered.wait(5)
        ticket=client.post(url+'/human-ticket',json={'summary':'由人工处理'}).json()
        closed=client.post('/api/v1/mercury/operator/tickets/'+ticket['ticket_id']+'/messages',
            headers={'X-Internal-Token':'fixture-operator'},json={'action':'close','content':'已处理','version':ticket['version']})
        assert closed.status_code==200,closed.text
        release.set();running.result(timeout=10)
    assert client.get(url+'/aftersales').json()=={'proposal':None,'receipts':[],'simulated':True}


def test_maintenance_readonly_preserves_new_applications_receipts_and_orders(web):
    import sqlite3
    client,sessions,url=web
    pid=proposal(client,url).json()['proposal_id']
    receipt=confirm(client,url,pid).json()
    with sessions() as db:
        original=db.get(SimulatedOrder,'normal').snapshot_json
    # Maintenance procedure: no more app requests/writers; open the upgraded
    # business file read-only rather than restoring a backup losing new writes.
    path=sessions.kw['bind'].url.database
    with sqlite3.connect(f'file:{path}?mode=ro',uri=True) as readonly:
        assert readonly.execute('SELECT COUNT(*) FROM aftersales_applications').fetchone()==(1,)
        assert readonly.execute('SELECT COUNT(*) FROM aftersales_receipts').fetchone()==(1,)
        saved=json.loads(readonly.execute('SELECT result_json FROM aftersales_receipts').fetchone()[0])
        assert saved==receipt
        assert readonly.execute("SELECT snapshot_json FROM simulated_orders WHERE order_id='normal'").fetchone()==(original,)
        with pytest.raises(sqlite3.OperationalError,match='readonly'):
            readonly.execute('DELETE FROM aftersales_receipts')
        assert readonly.execute('SELECT COUNT(*) FROM aftersales_receipts').fetchone()==(1,)


def test_proposal_service_failure_uses_existing_human_handoff(web,monkeypatch):
    from types import SimpleNamespace
    from app.mercury.router import get_query_model
    from app.mercury.aftersales import AfterSalesService
    client,_,url=web
    class Model:
        def chat(self,messages,tools=None):
            return SimpleNamespace(content='',tool_calls=[SimpleNamespace(id='proposal',function=SimpleNamespace(
                name='prepare_aftersales_proposal',arguments=json.dumps({'order_id':'normal','kind':'refund','reason':'不需要'})))])
        def cancel(self): pass
    def unavailable(*args,**kwargs): raise RuntimeError('fixture business failure private detail')
    client.app.dependency_overrides[get_query_model]=Model
    monkeypatch.setattr(AfterSalesService,'propose',unavailable)
    for count in (1,2):
        result=client.post(url+'/turns/stream',json={'message':'申请退款','request_id':str(count)})
        assert 'query_failed' in result.text and 'private detail' not in result.text
        ticket=client.get(url+'/human-ticket').json()
        assert ticket is None if count==1 else ticket['reason']=='persistent_service_failure'
    assert client.get(url+'/aftersales').json()['receipts']==[]


def test_pending_proposal_checkpoint_loss_requires_explicit_confirmation(web):
    client,_,url=web
    pid=proposal(client,url).json()['proposal_id']
    get_settings().mercury_checkpoint_path.unlink()
    state=client.get(url+'/aftersales').json()
    assert state['proposal']['proposal_id']==pid and state['receipts']==[]
    assert confirm(client,url,pid,confirmed=False).status_code==422
    response=confirm(client,url,pid)
    assert response.status_code==200,response.text
    assert len(client.get(url+'/aftersales').json()['receipts'])==1


def test_rejected_replacement_intent_invalidates_previous_proposal(web):
    client,_,url=web
    old=proposal(client,url).json()['proposal_id']
    malformed=client.post(url+'/proposals',json={'kind':'refund','quantity':1,'reason':'x','selection_version':1})
    assert malformed.status_code==422
    assert client.get(url+'/aftersales').json()['proposal']['proposal_id']==old
    assert proposal(client,url,'return',1,item_id=None).status_code==422
    assert client.get(url+'/aftersales').json()['proposal']['proposal_id']==old
    # This is a well-formed explicit change to a different aftersales scope.
    # The selected unshipped order is ineligible for delivered-line return.
    replacement=proposal(client,url,'return',1,reason='改变为退货',item_id='sku')
    assert replacement.status_code==409
    assert client.get(url+'/aftersales').json()['proposal'] is None
    assert confirm(client,url,old).status_code==409
    assert client.get(url+'/aftersales').json()['receipts']==[]


def test_earlier_inflight_proposal_cannot_survive_newer_denied_intent(web,monkeypatch):
    from threading import Event
    from concurrent.futures import ThreadPoolExecutor
    from app.mercury.aftersales import AfterSalesService
    client,_,url=web
    entered,release=Event(),Event()
    original=AfterSalesService.propose
    def delayed(self,owner_id,case_id,request,*args,**kwargs):
        if request['reason']=='earlier':
            entered.set(); assert release.wait(5)
        return original(self,owner_id,case_id,request,*args,**kwargs)
    monkeypatch.setattr(AfterSalesService,'propose',delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first=pool.submit(lambda:proposal(client,url,reason='earlier'))
        assert entered.wait(5)
        newer=proposal(client,url,'return',1,reason='newer',item_id='sku')
        assert newer.status_code==409
        release.set();older=first.result(timeout=10)
    assert older.status_code==409,older.text
    assert client.get(url+'/aftersales').json()=={'proposal':None,'receipts':[],'simulated':True}

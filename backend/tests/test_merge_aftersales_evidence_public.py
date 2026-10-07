"""T07 public HTTP evidence boundaries; all state is synthetic and disposable."""
import base64
import json
import pytest
from pathlib import Path
from test_aftersales_public import web, confirm
from app.core.config import get_settings

PHOTO_FIXTURES = Path(__file__).parent / 'fixtures' / 't07'
PNG = (PHOTO_FIXTURES / 'valid-tiny.png').read_bytes()
OPERATOR = {'X-Internal-Token': 't07-synthetic-operator'}


def upload(client, url, version=2):
    response = client.post(url + '/photos', json={'content_type': 'image/png',
        'data_base64': base64.b64encode(PNG).decode(), 'selection_version': version})
    assert response.status_code == 200, response.text
    return response.json()['photo_id']


def problem(client, url, photos, kind='quality', **overrides):
    return client.post(url + '/proposals', json={'kind': kind, 'item_id': 'sku',
        'reason': '包装破损', 'selection_version': 2, 'problem_quantity': 1,
        'photo_ids': photos, **overrides})


@pytest.mark.parametrize('kind', ['quality', 'fulfillment'])
def test_confirmed_ticket_exposes_only_its_application_evidence(web, monkeypatch, kind):
    client, _, url = web
    monkeypatch.setattr(get_settings(), 'human_operator_token', OPERATOR['X-Internal-Token'])
    assert client.put(url + '/order', json={'order_id': 'denied', 'selection_version': 1}).status_code == 200
    attached = upload(client, url)
    unrelated = upload(client, url)
    proposed = problem(client, url, [attached], kind)
    assert proposed.status_code == 200, proposed.text
    p = proposed.json()
    assert p['amount_fen'] == 617 and p['problem_quantity'] == 1
    assert client.get(url + '/human-ticket').json() is None
    assert client.get(url + '/aftersales').json()['receipts'] == []
    assert confirm(client, url, p['proposal_id'], confirmed=False).status_code == 422
    receipt = confirm(client, url, p['proposal_id'])
    assert receipt.status_code == 200, receipt.text
    assert confirm(client, url, p['proposal_id']).json() == receipt.json()
    ticket = client.get(url + '/human-ticket').json()
    assert [a['application_id'] for a in ticket['applications']] == [receipt.json()['application_id']]
    assert [photo['photo_id'] for photo in ticket['photos']] == [attached]
    target = '/api/v1/mercury/operator/tickets/' + ticket['ticket_id']
    assert client.get(target + '/photos/' + attached).status_code == 403
    assert client.get(target + '/photos/' + attached, headers=OPERATOR).content == PNG
    assert client.get(target + '/photos/' + unrelated, headers=OPERATOR).status_code == 404
    closed = client.post(target + '/messages', headers=OPERATOR,
        json={'action': 'close', 'content': '模拟核对结束', 'version': ticket['version']})
    assert closed.status_code == 200, closed.text
    later = upload(client, url)
    newer = client.post(url + '/human-ticket', json={'summary': '另一事项'}).json()
    assert newer['photos'] == [] and newer['applications'] == []
    old = next(t for t in client.get('/api/v1/mercury/operator/tickets', headers=OPERATOR).json()
        if t['ticket_id'] == ticket['ticket_id'])
    assert [photo['photo_id'] for photo in old['photos']] == [attached]
    assert client.get(target + '/photos/' + later, headers=OPERATOR).status_code == 404


def test_demo_order_progress_is_sequential_versioned_owned_and_snapshot_preserving(web):
    client, _, _ = web
    path = '/api/v1/orders/normal'
    original = client.get(path).json()
    assert client.post(path + '/demo-state', json={'expected_version': 1, 'status': 'delivered'}).status_code == 409
    shipped = client.post(path + '/demo-state', json={'expected_version': 1, 'status': 'shipped'})
    assert shipped.status_code == 200, shipped.text
    assert shipped.json()['version'] == 2 and shipped.json()['status'] == 'shipped'
    assert client.post(path + '/demo-state', json={'expected_version': 1, 'status': 'delivered'}).status_code == 409
    delivered = client.post(path + '/demo-state', json={'expected_version': 2, 'status': 'delivered'})
    assert delivered.status_code == 200, delivered.text
    assert delivered.json()['version'] == 3 and delivered.json()['delivered_at']
    assert delivered.json()['items'] == original['items']
    assert delivered.json()['total_fen'] == original['total_fen']
    assert client.post(path + '/demo-state', json={'expected_version': 3, 'status': 'shipped'}).status_code == 409
    client.cookies.clear()
    client.get('/api/v1/bootstrap')
    assert client.post(path + '/demo-state', json={'expected_version': 3, 'status': 'shipped'}).status_code == 404


@pytest.mark.parametrize('quantity', [None, 0, -1, 3, True, '1', 1.5])
def test_problem_quantity_requires_explicit_in_range_sales_packages(web, quantity):
    client, _, url = web
    client.put(url + '/order', json={'order_id': 'denied', 'selection_version': 1})
    response = problem(client, url, [], problem_quantity=quantity)
    assert response.status_code == 422, response.text
    assert client.get(url + '/aftersales').json()['receipts'] == []
    assert client.get(url + '/human-ticket').json() is None


@pytest.mark.parametrize('content_type,content', [
    ('image/png', b'not a png'), ('image/jpeg', PNG), ('image/gif', b'GIF89a'),
    ('image/png', PNG + b'x' * 4194304),
])
def test_photo_type_signature_and_size_rejections(web, content_type, content):
    client, _, url = web
    response = client.post(url + '/photos', json={'content_type': content_type,
        'data_base64': base64.b64encode(content).decode(), 'selection_version': 1})
    assert response.status_code == 422, response.text


def test_photo_encoding_count_and_scope_rejections(web):
    client, _, url = web
    assert client.post(url + '/photos', json={'content_type': 'image/png',
        'data_base64': '%%%bad%%%', 'selection_version': 1}).status_code == 422
    stale = upload(client, url, 1)
    client.put(url + '/order', json={'order_id': 'denied', 'selection_version': 1})
    assert problem(client, url, [stale]).status_code == 422
    assert client.post(url + '/photos', json={'content_type': 'image/png',
        'data_base64': base64.b64encode(PNG).decode(), 'selection_version': 1}).status_code == 409
    current = upload(client, url)
    assert problem(client, url, [current] * 4).status_code == 422
    other_url = '/api/v1/mercury/sessions/' + client.post('/api/v1/mercury/sessions').json()['session_id']
    client.put(other_url + '/order', json={'order_id': 'denied', 'selection_version': 0})
    other_case_photo = upload(client, other_url, 1)
    assert problem(client, url, [other_case_photo]).status_code == 422
    assert client.get(other_url + '/photos/' + current).status_code == 404
    client.put(url + '/order', json={'order_id': 'signed', 'selection_version': 2})
    assert problem(client, url, [current], selection_version=3).status_code == 422
    assert client.get(url + '/aftersales').json()['receipts'] == []
    client.cookies.clear()
    client.get('/api/v1/bootstrap')
    assert client.get(url + '/photos/' + current).status_code == 404
    assert client.post(url + '/photos', json={'content_type': 'image/png',
        'data_base64': base64.b64encode(PNG).decode(), 'selection_version': 3}).status_code == 404


def test_closed_ticket_and_new_same_order_application_have_separate_evidence(web, monkeypatch):
    import json
    from app.mercury.models import SimulatedOrder
    client, sessions, url = web
    # Fixture facts contain two distinct order lines before any HTTP operation.
    with sessions.begin() as db:
        order = db.get(SimulatedOrder, 'denied')
        snapshot = json.loads(order.snapshot_json)
        snapshot['items'].append({**snapshot['items'][0], 'sku_id': 'second-sku'})
        order.snapshot_json = json.dumps(snapshot)
        order.total_fen = 2468
    monkeypatch.setattr(get_settings(), 'human_operator_token', OPERATOR['X-Internal-Token'])
    client.put(url + '/order', json={'order_id': 'denied', 'selection_version': 1})
    first_photo = upload(client, url)
    p1 = problem(client, url, [first_photo]).json()['proposal_id']
    r1 = confirm(client, url, p1).json()
    first = client.get(url + '/human-ticket').json()
    # An open ticket owns the matter; no new proposal/confirmation bypasses it.
    assert problem(client, url, [], item_id='second-sku').status_code == 409
    assert confirm(client, url, p1, key='different').status_code == 409
    first_target = '/api/v1/mercury/operator/tickets/' + first['ticket_id']
    client.post(first_target + '/messages', headers=OPERATOR,
        json={'action': 'close', 'content': '结束第一事项', 'version': first['version']})
    second_photo = upload(client, url)
    p2 = problem(client, url, [second_photo], item_id='second-sku').json()['proposal_id']
    r2 = confirm(client, url, p2, key='second').json()
    second = client.get(url + '/human-ticket').json()
    assert second['generation'] == first['generation'] + 2
    assert [a['application_id'] for a in second['applications']] == [r2['application_id']]
    assert [p['photo_id'] for p in second['photos']] == [second_photo]
    assert confirm(client, url, p1).json() == r1
    first_after = next(t for t in client.get('/api/v1/mercury/operator/tickets', headers=OPERATOR).json()
        if t['ticket_id'] == first['ticket_id'])
    assert [a['application_id'] for a in first_after['applications']] == [r1['application_id']]
    assert [p['photo_id'] for p in first_after['photos']] == [first_photo]
    assert client.get(first_target + '/photos/' + second_photo, headers=OPERATOR).status_code == 404
    second_target = '/api/v1/mercury/operator/tickets/' + second['ticket_id']
    assert client.get(second_target + '/photos/' + first_photo, headers=OPERATOR).status_code == 404


def test_ticket_failure_rolls_back_application_receipt_and_responsibility(web, monkeypatch):
    from app.human import service
    client, _, url = web
    client.put(url + '/order', json={'order_id': 'denied', 'selection_version': 1})
    photo = upload(client, url)
    pid = problem(client, url, [photo]).json()['proposal_id']
    before = client.get(url).json()
    original = service.create_ticket
    def fail_after_ticket(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('synthetic transaction interruption')
    monkeypatch.setattr(service, 'create_ticket', fail_after_ticket)
    assert confirm(client, url, pid).status_code == 500
    assert client.get(url + '/aftersales').json()['receipts'] == []
    assert client.get(url + '/human-ticket').json() is None
    after = client.get(url).json()
    assert after['responsibility'] == 'agent'
    assert after['responsibility_generation'] == before['responsibility_generation']
    monkeypatch.setattr(service, 'create_ticket', original)
    receipt = confirm(client, url, pid)
    assert receipt.status_code == 200, receipt.text
    assert len(client.get(url + '/aftersales').json()['receipts']) == 1


@pytest.mark.parametrize('kind,reason,policy_id', [('quality','商品发霉','P-QUA-01'),
    ('fulfillment','漏送一个包装','P-FUL-01')])
def test_problem_quantity_clarification_resumes_without_submission(web, kind, reason, policy_id):
    from types import SimpleNamespace
    from app.mercury.router import get_query_model
    client, _, url = web
    assert client.put(url+'/order', json={'order_id':'denied','selection_version':1}).status_code == 200
    class Model:
        def chat(self, messages, tools=None):
            if messages[-1]['content'] == '1个销售包装':
                name = 'prepare_aftersales_proposal'
                arguments = {'order_id':'denied','kind':kind,'item_id':'sku',
                    'problem_quantity':1,'reason':reason}
            else:
                name, arguments = 'request_clarification', {'slot':'problem_quantity'}
            return SimpleNamespace(content='', tool_calls=[SimpleNamespace(id='quality',
                function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))])
        def cancel(self): pass
    client.app.dependency_overrides[get_query_model] = Model
    response = client.post(url+'/turns/stream', json={'message':f'面粉{reason}，申请处理','request_id':'problem-missing-count'})
    assert 'awaiting_details' in response.text and '销售包装' in response.text, response.text
    assert client.get(url+'/aftersales').json() == {'proposal':None,'receipts':[],'simulated':True}
    response = client.post(url+'/turns/stream', json={'message':'1个销售包装','request_id':'problem-count'})
    assert 'awaiting_confirmation' in response.text, response.text
    saved = client.get(url+'/aftersales').json()
    assert saved['receipts'] == []
    assert saved['proposal']['kind'] == kind and saved['proposal']['problem_quantity'] == 1
    assert saved['proposal']['policy_id'] == policy_id
    assert saved['proposal']['amount_fen'] == 617
    receipt = confirm(client, url, saved['proposal']['proposal_id']).json()
    assert receipt['status'] == 'requested' and receipt['problem_quantity'] == 1
    assert confirm(client, url, saved['proposal']['proposal_id']).json() == receipt
    assert client.get(url).json()['responsibility'] == 'human'
    assert client.get(url + '/human-ticket').json()['reason'] == kind + '_application'



@pytest.mark.parametrize('handoff', ['quality', 'manual'])
def test_prior_return_in_same_generation_is_not_associated_with_new_ticket(web, handoff):
    from app.mercury.models import SimulatedOrder
    client, sessions, url = web
    with sessions.begin() as db:
        order = db.get(SimulatedOrder, 'signed')
        snapshot = json.loads(order.snapshot_json)
        snapshot['items'].append({**snapshot['items'][0], 'sku_id': 'second-sku'})
        order.snapshot_json = json.dumps(snapshot)
        order.total_fen = 2468
    client.put(url + '/order', json={'order_id': 'signed', 'selection_version': 1})
    proposed = client.post(url + '/proposals', json={'kind': 'return', 'item_id': 'sku',
        'reason': '第一行无理由退货', 'selection_version': 2})
    assert proposed.status_code == 200, proposed.text
    prior = confirm(client, url, proposed.json()['proposal_id']).json()
    assert client.get(url + '/human-ticket').json() is None
    if handoff == 'quality':
        proposed = problem(client, url, [], item_id='second-sku')
        assert proposed.status_code == 200, proposed.text
        current = confirm(client, url, proposed.json()['proposal_id'], key='quality').json()
        expected = [current['application_id']]
    else:
        assert client.post(url + '/human-ticket', json={'summary': '独立人工咨询'}).status_code == 200
        expected = []
    ticket = client.get(url + '/human-ticket').json()
    assert [a['application_id'] for a in ticket['applications']] == expected
    # Precise ticket filtering never deletes the owner's independent history.
    assert prior in client.get(url + '/aftersales').json()['receipts']


@pytest.mark.parametrize('extension', ['png', 'jpeg', 'webp'])
def test_real_image_upload_roundtrip_preserves_valid_image(web, extension):
    client, _, url = web
    content = (PHOTO_FIXTURES / f'valid-tiny.{extension}').read_bytes()
    response = client.post(url + '/photos', json={'content_type': 'image/' + extension,
        'data_base64': base64.b64encode(content).decode(), 'selection_version': 1})
    assert response.status_code == 200, response.text
    fetched = client.get(url + '/photos/' + response.json()['photo_id'])
    assert fetched.content == content
    assert fetched.headers['content-type'] == 'image/' + extension


@pytest.mark.parametrize('content_type,content', [
    ('image/png', b'\x89PNG\r\n\x1a\n'),
    ('image/jpeg', b'\xff\xd8\xffgarbage'),
    ('image/webp', b'RIFF\x00\x00\x00\x00WEBPgarbage'),
    ('image/png', (PHOTO_FIXTURES / 'valid-tiny.png').read_bytes()[:40]),
    ('image/jpeg', (PHOTO_FIXTURES / 'valid-tiny.jpeg').read_bytes()[:400]),
    ('image/webp', (PHOTO_FIXTURES / 'valid-tiny.webp').read_bytes()[:25]),
])
def test_signature_matching_but_undecodable_image_is_rejected(web, content_type, content):
    client, _, url = web
    response = client.post(url + '/photos', json={'content_type': content_type,
        'data_base64': base64.b64encode(content).decode(), 'selection_version': 1})
    assert response.status_code == 422, response.text
    assert response.json()['error']['code'] == 'PHOTO_INVALID'

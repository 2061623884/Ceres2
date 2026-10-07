"""T07 public HTTP evidence boundaries; all state is synthetic and disposable."""
import base64
import pytest
from test_aftersales_public import web, confirm
from app.core.config import get_settings

PNG = b'\x89PNG\r\n\x1a\nsynthetic-photo'
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

"""Public cross-turn comparison evidence fences and failure behavior."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_comparison_public import comparison_hook, seed_multipack, posted_turn, select_hook


def compare(client, requests, *, view_context=None):
    seed_multipack(requests)
    command(client,'new_goal',goal='比较可乐')
    requests.answer_hook = comparison_hook
    events = posted_turn(client,'比较饮料','safe-compare',view_context=view_context)
    assert events[-1]['type'] == 'turn.completed', events
    return events[-1]['payload']['product_cards']


@pytest.mark.parametrize('change', ['unshown','task','conditions','page','owner'])
def test_candidate_evidence_cannot_cross_display_owner_task_version_or_page(pi_client, change):
    client, requests = pi_client
    cards = compare(client,requests,view_context={'page':'category','category_id':'beverage'})
    ref = cards[0]['ref']
    requests.answer_hook = select_hook(ref)
    shown = [c['ref'] for c in cards]
    page = {'page':'category','category_id':'beverage'}
    if change == 'unshown':
        shown = []
    elif change == 'task':
        command(client,'new_goal',goal='买水果')
    elif change == 'conditions':
        command(client,'amend',conditions={'budget_fen':2000})
    elif change == 'page':
        page = {'page':'category','category_id':'fruit'}
    else:
        from sqlalchemy.orm import Session
        from app.models.cart import Cart
        with Session(requests.engine) as db:
            db.add(Cart(owner_id='pi-owner-b',store_id='pi-store',version=1))
            db.commit()
        client.cookies.set('sg_owner_id','pi-owner-b')
        state = client.get('/api/v1/guide/sessions/pi-session-b').json()
        response = client.post('/api/v1/guide/sessions/pi-session-b/turns/stream',json={
            'request_id':'other-owner-select','message':f'选择候选 {ref}',
            'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],
            'expected_session_version':state['session_version'],'displayed_candidate_refs':shown,'view_context':page})
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'COMPARISON_STALE'
        assert client.get('/api/v1/guide/sessions/pi-session-b').json()['plan'] is None
        assert client.get('/api/v1/cart').json()['items'] == []
        return
    events = posted_turn(client,f'选择候选 {ref}','invalid-'+change,shown,page)
    assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'COMPARISON_STALE', events
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_provider_failure_before_any_tool_retires_prior_displayed_candidates(pi_client):
    client, requests = pi_client
    cards = compare(client,requests)
    events = posted_turn(client,'模型认证失败，重新比较','comparison-provider-failure',[c['ref'] for c in cards])
    assert events[-1]['type'] == 'error', events
    assert client.get(BASE).json()['product_cards'] == []
    requests.answer_hook = select_hook(cards[0]['ref'])
    events = posted_turn(client,'选择先前候选','after-failed-comparison',[c['ref'] for c in cards])
    assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'COMPARISON_STALE'
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_repeated_proposal_keeps_display_fence_and_late_failure_preserves_new_cards(pi_client):
    client, requests = pi_client
    cards = compare(client,requests)
    ref = cards[0]['ref']
    def concurrent_hook(body):
        user = json.dumps([m['content'] for m in body['messages'] if m['role'] == 'user'],ensure_ascii=False)
        if '替换显示' in user:
            return comparison_hook(body)
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            return select_hook(ref)(body)
        if len(outputs) == 2:
            return {'role':'assistant','tool_calls':[{'index':0,'id':'second-proposal','type':'function','function':{'name':'propose_purchase','arguments':json.dumps({'ref':ref,'quantity':1})}}]}, 'tool_calls'
        requests.started.set()
        requests.release.wait(timeout=10)
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'purchase_plan','proposal_ref':outputs[-1]['proposal_ref']})}, 'stop'
    requests.answer_hook = concurrent_hook
    state = client.get(BASE).json()
    admitted = client.post(BASE+'/runs',json={'request_id':'repeat-proposal','message':f'选择候选 {ref}',
        'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],
        'expected_session_version':state['session_version'],'displayed_candidate_refs':[c['ref'] for c in cards]})
    assert admitted.status_code == 202, admitted.text
    assert requests.started.wait(timeout=5)
    events = posted_turn(client,'替换显示，重新比较','replacement-display')
    assert events[-1]['type'] == 'turn.completed', events
    newer = events[-1]['payload']['product_cards']
    assert newer and newer[0]['ref'] != ref
    requests.release.set()
    response = client.get(BASE+'/runs/'+admitted.json()['run_id']+'/stream')
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'COMPARISON_STALE', events
    state = client.get(BASE).json()
    assert state['product_cards'] == newer
    assert state['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_comparison_cannot_publish_products_from_a_later_unfiltered_search(pi_client):
    client, requests = pi_client
    seed_multipack(requests)
    command(client,'new_goal',goal='只比较多件装',conditions={'pack_count_mode':'multi'})
    def mixed(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if len(outputs) < 2:
            return comparison_hook(body)
        if len(outputs) == 2:
            return {'role':'assistant','tool_calls':[{'index':0,'id':'unfiltered-search','type':'function','function':{'name':'search_products','arguments':json.dumps({'query':'测试可乐'})}}]}, 'tool_calls'
        return {'role':'assistant','content':json.dumps({'status':'completed','answer_kind':'comparison','product_refs':[outputs[-1]['products'][0]['ref'] if outputs[-1]['products'] else 'unfiltered-candidate']})}, 'stop'
    requests.answer_hook = mixed
    events = turn(client,'只比较多件装，不放宽条件','mixed-comparison')
    assert events[-1]['type'] == 'error' and events[-1]['payload']['code'] == 'PI_UNKNOWN_REFERENCE', events
    assert client.get(BASE).json()['product_cards'] == []
    assert client.get(BASE).json()['plan'] is None


def test_reentry_in_different_page_does_not_restore_other_category_cards(pi_client):
    client, requests = pi_client
    cards = compare(client,requests,view_context={'page':'category','category_id':'beverage'})
    assert cards
    response = client.post('/api/v1/guide/sessions',json={'entry_context':{'page':'category','category_id':'fruit','store_id':'pi-store','delivery_zone_id':'zone-default'}})
    assert response.status_code == 200
    assert response.json()['product_cards'] == []
    assert response.json()['plan'] is None


@pytest.mark.parametrize('protected_status',['tool_budget','deadline'])
def test_protected_comparison_close_retires_old_snapshot(pi_client, protected_status):
    client, requests = pi_client
    cards = compare(client,requests)
    def exhausted(body):
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return comparison_hook(body)
        if protected_status == 'deadline' and len(outputs) >= 2:
            requests.release.wait(timeout=20)
        return {'role':'assistant','tool_calls':[{'index':0,'id':f'keep-comparing-{len(outputs)}','type':'function','function':{'name':'compare_products','arguments':json.dumps({'category_id':'beverage'})}}]}, 'tool_calls'
    requests.answer_hook = exhausted
    events = posted_turn(client,'重新比较，核对更多候选','protected-'+protected_status,[card['ref'] for card in cards])
    requests.release.set()
    assert events[-1]['type'] == 'turn.completed', events
    assert events[-1]['payload']['runtime_status'] == protected_status
    assert client.get(BASE).json()['product_cards'] == []
    assert client.get(BASE).json()['plan'] is None
    assert client.get('/api/v1/cart').json()['items'] == []


def test_late_protected_comparison_does_not_retire_newer_display(pi_client):
    client, requests = pi_client
    cards = compare(client,requests)
    def interleaved(body):
        user = json.dumps([m['content'] for m in body['messages'] if m['role'] == 'user'],ensure_ascii=False)
        if '新比较B' in user:
            return comparison_hook(body)
        outputs = [json.loads(m['content']) for m in body['messages'] if m['role'] == 'tool']
        if not outputs:
            return comparison_hook(body)
        if len(outputs) == 4:
            requests.started.set()
            requests.release.wait(timeout=10)
        return {'role':'assistant','tool_calls':[{'index':0,'id':f'comparison-{len(outputs)}','type':'function','function':{'name':'compare_products','arguments':json.dumps({'category_id':'beverage'})}}]}, 'tool_calls'
    requests.answer_hook = interleaved
    state = client.get(BASE).json()
    admitted = client.post(BASE+'/runs',json={'request_id':'protected-old','message':'旧比较A继续核对',
        'expected_task_id':state['task_id'],'expected_state_version':state['state_version'],
        'expected_session_version':state['session_version'],'displayed_candidate_refs':[card['ref'] for card in cards]})
    assert admitted.status_code == 202, admitted.text
    assert requests.started.wait(timeout=5)
    events = posted_turn(client,'新比较B','protected-replacement')
    assert events[-1]['type'] == 'turn.completed', events
    newer = events[-1]['payload']['product_cards']
    requests.release.set()
    response = client.get(BASE+'/runs/'+admitted.json()['run_id']+'/stream')
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['payload']['runtime_status'] == 'tool_budget'
    assert client.get(BASE).json()['product_cards'] == newer
    assert client.get(BASE).json()['plan'] is None

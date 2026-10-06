"""Explicit compound navigation keeps all text and reaches Pi once, without consent inflation."""
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import command, BASE
from test_guide_semantics import turn
from test_next_snack_public import seed_snacks, exploration_hook


def test_explicit_return_and_buy_reaches_guide_without_second_kev(pi_client, controlled_kev_transport):
    client, requests = pi_client
    seed_snacks(requests)
    command(client,'new_goal',goal='零食')
    requests.answer_hook = exploration_hook
    nav = BASE.replace('/guide/','/navigation/')
    opening = client.post(nav + '/opening',json={'role':'momo'}).json()
    controlled_kev_transport['choose'] = lambda state:'return_keke_exploration'
    original = '回到购物，来点零食，预算二十元，保留其他条件'
    result = client.post(nav + '/routes',json={'request_id':'explicit-return','opening_id':opening['opening_id'],'role':'momo','message':original}).json()
    assert result['status'] == 'navigation', result
    assert result['continue_original'] and not result['show_prompt']
    completed = turn(client,original,'explicit-return')
    assert completed[-1]['type'] == 'turn.completed', completed
    assert len(controlled_kev_transport['calls']) == 1
    assert any(original in str(request['messages']) for request in requests)
    before = len(requests)
    replay = turn(client,original,'explicit-return')
    assert replay[-1]['payload'] == completed[-1]['payload']
    assert len(requests) == before and len(controlled_kev_transport['calls']) == 1
    assert client.get('/api/v1/cart').json()['items'] == []

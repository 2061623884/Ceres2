"""Return words stay with Momo; a button and a fresh request reach Coco."""
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import command, BASE
from test_guide_semantics import turn
from test_next_snack_public import seed_snacks, exploration_hook


def test_compound_return_does_not_replay_shopping_after_button(pi_client, controlled_kev_transport):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='零食')
    requests.answer_hook = exploration_hook
    nav = BASE.replace('/guide/', '/navigation/')
    opening = client.post(nav + '/opening', json={'role': 'momo'}).json()
    original = '回到购物，来点零食，预算二十元，保留其他条件'
    result = client.post(nav + '/routes', json={'request_id': 'return-text',
        'opening_id': opening['opening_id'], 'role': 'momo', 'message': original}).json()
    assert result['status'] == 'ready' and result['authorized_role'] == 'momo', result
    assert not result['continue_original'] and not result['show_prompt']
    assert controlled_kev_transport['calls'] == [] and requests == []
    blocked = turn(client, original, 'return-text')
    assert blocked[-1]['type'] == 'error' and requests == []
    returned = client.post(nav + '/switches', json={'opening_id': opening['opening_id'],
        'target_role': 'keke', 'accept': True})
    assert returned.status_code == 200 and returned.json()['handoff'] is None
    assert requests == [] and controlled_kev_transport['calls'] == []
    completed = turn(client, '来点零食，预算二十元，保留其他条件', 'fresh-shopping')
    assert completed[-1]['type'] == 'turn.completed', completed
    assert len(controlled_kev_transport['calls']) == 1
    before = len(requests)
    replay = turn(client, '来点零食，预算二十元，保留其他条件', 'fresh-shopping')
    assert replay[-1]['payload'] == completed[-1]['payload']
    assert len(requests) == before and len(controlled_kev_transport['calls']) == 1
    assert client.get('/api/v1/cart').json()['items'] == []

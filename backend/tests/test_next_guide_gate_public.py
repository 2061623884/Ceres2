"""Public guide ingress cannot bypass the single role decision."""
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_next_snack_public import seed_snacks, exploration_hook


def test_direct_guide_text_is_judged_once_and_replay_reuses_decision(pi_client, controlled_kev_transport):
    client, requests = pi_client
    seed_snacks(requests)
    command(client, 'new_goal', goal='零食')
    requests.answer_hook = exploration_hook
    controlled_kev_transport['choose'] = lambda state:'momo'
    rejected = turn(client, '我要查退款资格', 'direct-wrong-role')
    assert rejected[-1]['type'] == 'error', rejected
    assert rejected[-1]['payload']['code'] == 'ROLE_NAVIGATION_REQUIRED'
    assert len(controlled_kev_transport['calls']) == 1
    assert requests == [], 'Wrong role must not secretly execute the guide model'
    controlled_kev_transport['choose'] = lambda state:'keke_exploration'
    first = turn(client, '来点零食', 'direct-allowed')
    assert first[-1]['type'] == 'turn.completed', first
    assert len(controlled_kev_transport['calls']) == 2
    before = len(requests)
    again = turn(client, '来点零食', 'direct-allowed')
    assert again[-1]['payload'] == first[-1]['payload']
    assert len(controlled_kev_transport['calls']) == 2
    assert len(requests) == before
    assert client.get('/api/v1/cart').json()['items'] == []

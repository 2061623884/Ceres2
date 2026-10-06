"""Known task amount is reused for one SKU, never multiplied across selections."""
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE, command
from test_guide_semantics import turn
from test_next_snack_public import seed_snacks, exploration_hook, answer_question, selection_hook


def products(client, requests):
    seed_snacks(requests)
    command(client, 'new_goal', goal='买两包零食', conditions={'quantity':2})
    requests.answer_hook = exploration_hook
    category = turn(client, '买两包零食', 'known-total')[-1]['payload']['active_question']
    chips = next(o for o in category['options'] if o['label'] == '薯片')
    return answer_question(client, category, [chips['option_id']], 'known-type').json()['active_question']


def test_product_question_preserves_known_total_for_single_choice(pi_client):
    client, requests = pi_client
    question = products(client, requests)
    assert question['known_total_quantity'] == 2
    assert question.get('known_quantities', {}) == {}, 'No per-SKU allocation has been supplied'
    selected = question['options'][0]
    requests.answer_hook = selection_hook(question['question_id'], [{'option_id':selected['option_id']}])
    result = turn(client, '选这款', 'known-single')[-1]['payload']
    assert [(r['sku_id'],r['quantity']) for r in result['plan']['items']] == [(selected['value'],2)]
    assert client.get('/api/v1/cart').json()['items'] == []


def test_multi_product_text_selection_requires_distribution_of_known_total(pi_client):
    client, requests = pi_client
    question = products(client, requests)
    requests.answer_hook = selection_hook(question['question_id'], [{'option_id':o['option_id']} for o in question['options']])
    result = turn(client, '这两款都选', 'known-many')[-1]['payload']
    assert result['plan'] is None
    assert result['active_question']['kind'] == 'quantity'
    assert result['active_question'].get('known_quantities', {}) == {}
    assert result['active_question']['known_total_quantity'] == 2
    assert client.get(BASE).json()['conditions']['quantity'] == 2
    assert client.get('/api/v1/cart').json()['items'] == []

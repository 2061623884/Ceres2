"""Explicit user role choice for inherited cross-role public journeys.

Only the production navigation API is used. This does not judge text, mutate
internal session state, resume a pending request, or replace business assertions.
"""


def choose_public_role(client, guide_url, role):
    navigation_url = guide_url.replace('/guide/', '/navigation/')
    opened = client.get(navigation_url + '/opening')
    assert opened.status_code == 200, opened.text
    before = opened.json()
    switched = client.post(navigation_url + '/switches', json={
        'opening_id': before['opening_id'], 'target_role': role, 'accept': True,
    })
    assert switched.status_code == 200, switched.text
    after = switched.json()
    assert after['role'] == role
    assert after['opening_id'] == before['opening_id']
    assert after['prompt_displayed'] == before['prompt_displayed']
    assert after['handoff'] is None, 'This fixture chooses a page, not an old business request'
    assert client.get(navigation_url + '/opening').json()['role'] == role

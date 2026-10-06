"""Fresh/synthetic-old schema, repeated upgrades, and old shopping facts preserved."""
from sqlalchemy import inspect, text
from app.core.database import create_db_engine, init_db
from test_runtime_pi_product_query import pi_client


def test_comparison_schema_is_additive_and_repeatable(tmp_path):
    engine = create_db_engine(f'sqlite:///{tmp_path}/old.sqlite3')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE owners (id VARCHAR(80) PRIMARY KEY)'))
        connection.execute(text("INSERT INTO owners VALUES ('existing-owner')"))
    init_db(engine)
    init_db(engine)
    with engine.connect() as connection:
        assert 'comparison_displays' in inspect(connection).get_table_names()
        assert connection.execute(text('SELECT id FROM owners')).scalar_one() == 'existing-owner'
        assert connection.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='0008_category_comparison'")).scalar_one() == 1
        assert connection.execute(text('SELECT COUNT(*) FROM comparison_displays')).scalar_one() == 0
    engine.dispose()


def test_comparison_and_existing_plan_cart_receipt_survive_upgrade(pi_client):
    from test_purchase_public import prepare, confirmation_body
    from test_guide_lifecycle import BASE
    from test_comparison_public import comparison_hook
    from test_guide_semantics import turn
    client, requests = pi_client
    state = prepare(client, requests)
    url = '/api/v1/guide/tasks/'+state['task_id']+'/confirm'
    response = client.post(url,json=confirmation_body(state),headers={'Idempotency-Key':'comparison-upgrade-purchase'})
    assert response.status_code == 200
    receipt = response.json()
    requests.answer_hook = comparison_hook
    events = turn(client,'再比较饮料','comparison-upgrade')
    assert events[-1]['type'] == 'turn.completed', events
    before = client.get(BASE).json()
    assert before['product_cards']
    init_db(requests.engine)
    init_db(requests.engine)
    after = client.get(BASE).json()
    assert after['product_cards'] == before['product_cards']
    assert after['plan'] == before['plan']
    assert after['confirmation_result'] == receipt
    assert client.get('/api/v1/cart').json()['items'][0]['quantity'] == 2

"""Expression failures retain safe internal causes while facts remain authoritative."""
import json
import pytest
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE
from test_next_result_stream_public import _prepare_cards, _terminal


@pytest.mark.parametrize('mode,code', [
    ('parse', 'expression_parse'),
    ('unit', 'invalid_unit'),
    ('validator_parse', 'validation_parse'),
    ('validator_reject', 'validation_rejected'),
    ('provider', 'generation_provider'),
    ('stderr', 'worker_stderr'),
])
def test_expression_failure_journals_safe_cause_without_exposing_provider_text(pi_client, monkeypatch, tmp_path, caplog, mode, code):
    client, requests = pi_client
    snapshot = _prepare_cards(client, requests)
    secret = 'private-provider-response-do-not-log'
    def expression(body):
        checking = 'CERES_GENERAL_CLAIM_CHECK' in json.dumps(body['messages'])
        if checking:
            content = secret if mode == 'validator_parse' else json.dumps({'merchant_claims':mode == 'validator_reject', 'execution_claims':False})
        else:
            content = secret if mode == 'parse' else json.dumps({'text':secret, 'fact_ref':'foreign' if mode == 'unit' else 'result'})+'\n'
        return {'role':'assistant','content':content}, 'stop'
    requests.answer_hook = expression
    if mode == 'provider':
        from app.core.config import get_settings
        monkeypatch.setenv('OPENAI_BASE_URL', 'http://127.0.0.1:1/v1')
        get_settings.cache_clear()
    elif mode == 'stderr':
        from app.services import result_expression_runtime
        worker = tmp_path / 'expression-crash.js'
        worker.write_text("process.stdin.once('data',()=>{process.stderr.write('TypeError: " + secret + " offline-fixture-key\\n');process.exit(1)});")
        monkeypatch.setattr(result_expression_runtime, 'WORKER', worker)
    response = client.post(BASE+'/result-introductions', json={'source_kind':'question_answer','source_id':'intro-type'})
    assert response.status_code == 202, response.text
    events = _terminal(client, response.json()['run_id'])
    assert events[-1]['payload']['expression_status'] == 'failed', events
    assert not any(event['type'] == 'answer.delta' for event in events)
    assert code in caplog.text
    assert secret not in caplog.text and 'offline-fixture-key' not in caplog.text
    assert secret not in json.dumps(events) and code not in json.dumps(events)
    assert client.get(BASE).json()['active_question'] == snapshot['active_question']
    assert client.get('/api/v1/cart').json()['items'] == []

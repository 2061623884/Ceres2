"""Final projection retains the current bounded diagnostic tail, not an old alias."""
import json

from test_runtime_pi_product_query import pi_client
from test_integration_reviewed_interim_public import install_model
from test_guide_lifecycle import BASE


def test_saturated_tail_includes_final_projection_in_sse_receipt_and_export(pi_client, monkeypatch, tmp_path):
    from sqlalchemy.orm import sessionmaker
    from app.core import database
    from app.evaluation.export_runs import export_runs
    from app.services.pi_product_runtime import PiProductRuntime
    from app.services.product_question_service import ProductQuestionService
    from app.services.knowledge_service import knowledge, KnowledgeService

    client, requests = pi_client
    install_model(requests)
    state = client.get(BASE).json()
    active = {}
    record = PiProductRuntime._record_event
    def observe(runtime, event):
        active['runtime'] = runtime
        record(runtime, event)
        if event['type'] == 'agent_end':
            # Saturate before the host constructs its final result object.
            for index in range(300):
                record(runtime, {'type': 'controlled_tail_marker', 'sequence': index})
    monkeypatch.setattr(PiProductRuntime, '_record_event', observe)
    monkeypatch.setattr(knowledge, 'search', KnowledgeService.search.__get__(knowledge, KnowledgeService))
    monkeypatch.setattr(knowledge, '_query', lambda *args, **kwargs: {
        'hits': [], 'manifest': {'corpus_revision': 'final-projection-source'}})
    projection = ProductQuestionService.projection
    def project(questions, session_id, **kwargs):
        # Initial context runs before Pi emits anything; only the final public
        # projection performs this actual search against the saturated tail.
        if 'runtime' in active and questions.deadline is not None:
            knowledge.search('final projection', 'product', deadline=questions.deadline,
                             should_stop=questions.should_stop)
        return projection(questions, session_id, **kwargs)
    monkeypatch.setattr(ProductQuestionService, 'projection', project)
    response = client.post(BASE + '/turns/stream', json={
        'request_id': 'final-saturated-tail', 'message': '看看进展',
        'expected_task_id': state['task_id'], 'expected_state_version': state['state_version'],
        'expected_session_version': state['session_version']})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
    assert events[-1]['type'] == 'turn.completed', events
    result = events[-1]['payload']
    assert len(result['runtime_events']) == 256
    assert result['runtime_events'][-1]['type'] == 'retrieval_end'
    assert result['runtime_events'][-1]['source_revision'] == 'final-projection-source'
    assert result['runtime_summary']['events_truncated'] is True
    assert result['runtime_summary']['retrieval_calls']['product']['completed'] == 1
    persisted = client.get(BASE + '/turns/final-saturated-tail').json()['result']
    assert persisted['runtime_events'] == result['runtime_events'] == active['runtime'].events
    monkeypatch.setattr(database, 'SessionLocal', sessionmaker(bind=requests.engine))
    output = tmp_path / 'synthetic-final-tail.jsonl'
    export_runs('pi-owner-a', output)
    captured = json.loads(output.read_text().splitlines()[0])
    assert len(captured['runtime_events']) == 256
    assert captured['runtime_events'][-1]['type'] == 'retrieval_end'
    assert captured['runtime_summary']['retrieval_calls']['product']['completed'] == 1

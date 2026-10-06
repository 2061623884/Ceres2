"""Controlled OpenAI port verifies independent configured calls, not live quality."""
import json
from types import SimpleNamespace
from test_runtime_pi_product_query import pi_client
from test_guide_semantics import turn
from test_memory_public import memory_turn
from app.services.memory_background import MemoryWorker


def test_independently_configured_extraction_and_dream_models_publish_only_sql_results(pi_client, monkeypatch):
    from app.core.config import get_settings
    from app.services import memory_model
    client, requests = pi_client
    settings = get_settings()
    assert settings.memory_extraction_model == settings.memory_dream_model == 'qwen3.8-27b'
    monkeypatch.setattr(settings,'memory_extraction_model','controlled-extraction')
    monkeypatch.setattr(settings,'memory_dream_model','controlled-dream')
    calls = []
    def create(**arguments):
        calls.append(arguments)
        source = json.loads(arguments['messages'][-1]['content'])
        if arguments['model'] == 'controlled-extraction':
            assert set(source) == {'role','text'}
            result = {'records':[{'category':'user','domain':'shopping','key':f'wire-{i}',
                'content':f'长期偏好{i}无糖','source_quote':f'长期偏好{i}无糖','scope':'durable'} for i in range(10)]}
        else:
            row = next(row for row in source['records'] if row['key']=='wire-0')
            result = {'records':[{'memory_id':row['memory_id'],'content':'长期偏好0：无糖'}]}
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(result)))])
    class Provider:
        def __init__(self, **_):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=create))
        def __enter__(self): return self
        def __exit__(self,*_): pass
    monkeypatch.setattr(memory_model,'OpenAI',Provider)
    source = '；'.join(f'长期偏好{i}无糖' for i in range(10))
    assert turn(client,source,'independent-model-source')[-1]['type'] == 'turn.completed'
    worker = MemoryWorker(requests.engine)
    assert worker.run_once()
    assert worker.run_once()
    assert [call['model'] for call in calls] == ['controlled-extraction','controlled-dream']
    assert all(call['model'] != settings.llm_model for call in calls)
    records = memory_turn(client,requests,'查看全部记忆',{'action':'list'},'wire-list')['records']
    assert len(records) == 10
    assert next(row for row in records if row['key']=='wire-0')['content'] == '长期偏好0：无糖'


def test_missing_extraction_model_never_falls_back_to_working_chat_model(pi_client, monkeypatch):
    from app.core.config import get_settings
    from app.services import memory_model
    client, requests = pi_client
    monkeypatch.setattr(get_settings(),'memory_extraction_model','')
    calls = []
    def forbidden_client(**arguments):
        calls.append(arguments)
        raise AssertionError('No provider may be called without its independent model configuration')
    monkeypatch.setattr(memory_model,'OpenAI',forbidden_client)
    assert turn(client,'我平时喜欢无糖可乐','missing-extraction-config')[-1]['type'] == 'turn.completed'
    worker = MemoryWorker(requests.engine)
    assert worker.run_once()
    assert memory_turn(client,requests,'查看全部记忆',{'action':'list'},'missing-config-list')['records'] == []
    assert calls == []


def test_additive_job_upgrade_preserves_preexisting_memory_and_repeats_safely(pi_client):
    from sqlalchemy import text
    from app.core.database import init_db
    client, requests = pi_client
    saved = memory_turn(client,requests,'记住回复要简短',{'action':'save','category':'feedback',
        'domain':'communication','key':'style','content':'回复要简短','source_quote':'回复要简短'},'before-upgrade')['records'][0]
    # A synthetic TASK09 database: no TASK10 table or migration marker.
    with requests.engine.begin() as db:
        db.execute(text('DROP TABLE memory_jobs'))
    init_db(requests.engine)
    init_db(requests.engine)
    assert memory_turn(client,requests,'查看全部记忆',{'action':'list'},'after-upgrade')['records'] == [saved]
    with requests.engine.connect() as db:
        assert db.execute(text("SELECT COUNT(*) FROM schema_migrations WHERE version='0010_recoverable_memory'")).scalar_one() == 1
        assert db.execute(text('SELECT COUNT(*) FROM memory_jobs')).scalar_one() == 0
        names = [row[1] for row in db.execute(text('PRAGMA index_list(memory_jobs)'))]
        assert 'one_active_memory_dream' in names


def test_installed_openai_sdk_uses_two_independent_nonstreaming_memory_calls(pi_client, monkeypatch):
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from app.core.config import get_settings
    client, requests = pi_client
    captured = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_): pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            captured.append(body)
            source = json.loads(body['messages'][-1]['content'])
            if 'text' in source:
                result = {'records':[{'category':'user','domain':'shopping','key':f'http-{i}',
                    'content':f'长期偏好{i}无糖','source_quote':f'长期偏好{i}无糖','scope':'durable'} for i in range(10)]}
            else:
                row = next(row for row in source['records'] if row['key']=='http-0')
                result = {'records':[{'memory_id':row['memory_id'],'content':'长期偏好0：无糖'}]}
            response = {'id':'controlled-memory-http','object':'chat.completion','created':1800000000,
                'model':body['model'],'choices':[{'index':0,'finish_reason':'stop',
                    'message':{'role':'assistant','content':json.dumps(result)}}]}
            data = json.dumps(response).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try:
        assert turn(client,'；'.join(f'长期偏好{i}无糖' for i in range(10)),'real-sdk-memory-source')[-1]['type'] == 'turn.completed'
        with monkeypatch.context() as configuration:
            configuration.setattr(get_settings(),'openai_base_url',f'http://127.0.0.1:{server.server_port}/v1')
            worker = MemoryWorker(requests.engine)
            assert worker.run_once()
            assert worker.run_once()
        assert [body['model'] for body in captured] == ['qwen3.8-27b','qwen3.8-27b']
        assert all(body.get('stream',False) is False for body in captured)
        assert 'text' in json.loads(captured[0]['messages'][-1]['content'])
        assert 'records' in json.loads(captured[1]['messages'][-1]['content'])
        records = memory_turn(client,requests,'查看全部记忆',{'action':'list'},'http-model-list')['records']
        assert next(row for row in records if row['key']=='http-0')['content'] == '长期偏好0：无糖'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

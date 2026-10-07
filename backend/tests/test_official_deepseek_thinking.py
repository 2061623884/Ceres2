"""Installed SDK wire contracts with synthetic, offline provider transports."""
import json
import os
import subprocess
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest

from test_mercury_public import mercury_client


HOSTS = [
    pytest.param('https://api.deepseek.com/v1', True, id='official'),
    pytest.param('https://API.DEEPSEEK.COM/v1', True, id='normalized-official'),
    pytest.param('http://provider-fixture.invalid/v1', False, id='other-provider'),
    pytest.param('https://api.deepseek.com.evil.example/v1', False, id='suffix-lookalike'),
]


def _sdk_transport(monkeypatch, module, response):
    """Keep the real OpenAI serializer and intercept only its HTTP boundary."""
    real_openai = module.OpenAI
    requests = []
    clients = []

    def handle(request):
        body = json.loads(request.content)
        requests.append(body)
        message = response(body)
        return httpx.Response(200, json={
            'id': 'controlled-wire', 'object': 'chat.completion', 'created': 0,
            'model': body['model'], 'choices': [{'index': 0,
                'finish_reason': 'tool_calls' if message.get('tool_calls') else 'stop',
                'message': message}],
            'usage': {'prompt_tokens': 3, 'completion_tokens': 1, 'total_tokens': 4},
        })

    def client(**options):
        transport = httpx.Client(transport=httpx.MockTransport(handle))
        clients.append((options, transport))
        return real_openai(**options, http_client=transport)

    monkeypatch.setattr(module, 'OpenAI', client)
    return requests, clients


def _assert_profile(body, official):
    if official:
        assert body['thinking'] == {'type': 'disabled'}
    else:
        assert 'thinking' not in body
    assert 'reasoning_effort' not in body


@pytest.mark.parametrize('base_url,official', HOSTS)
def test_momo_public_query_disables_thinking_only_on_official_host(
        mercury_client, monkeypatch, base_url, official):
    from app.core.config import get_settings
    from app.mercury import provider

    client, app, url, sessions = mercury_client
    settings = get_settings()
    monkeypatch.setattr(settings, 'openai_base_url', base_url)
    monkeypatch.setattr(settings, 'openai_api_key', 'synthetic-not-a-real-key')
    monkeypatch.setattr(settings, 'llm_model', 'controlled-chat')

    def response(body):
        if body['messages'][-1]['role'] == 'tool':
            return {'role': 'assistant', 'content': '订单详情已整理。'}
        return {'role': 'assistant', 'content': None, 'tool_calls': [{
            'id': 'order-query', 'type': 'function', 'function': {
                'name': 'get_order_details', 'arguments': '{"order_id":"budget-order"}'}}]}

    requests, clients = _sdk_transport(monkeypatch, provider, response)
    result = client.post(url + '/turns/stream', json={
        'message': '查看订单', 'request_id': 'official-thinking-wire'})
    assert result.status_code == 200
    frames = [json.loads(line.removeprefix('data: ')) for line in result.text.splitlines()
              if line.startswith('data: ')]
    assert frames[-1]['status'] == 'completed'
    assert '15.00' in result.text and '测试杯' in result.text
    assert len(requests) == 2
    for body in requests:
        _assert_profile(body, official)
        assert body['model'] == 'controlled-chat'
        assert body['temperature'] == 0.2
        assert body['tool_choice'] == 'auto'
        assert 'response_format' not in body
        assert 'max_tokens' not in body and 'max_completion_tokens' not in body
        assert body.get('stream', False) is False
    assert requests[1]['messages'][-1]['role'] == 'tool'
    assert json.loads(requests[1]['messages'][-1]['content'])['data']['total'] == '15.00'
    assert len(clients) == 2
    assert all(options['timeout'] == 15 and options['max_retries'] == 0
               and transport.is_closed for options, transport in clients)


@pytest.mark.parametrize('base_url,official', HOSTS)
@pytest.mark.parametrize('operation,model,source', [
    ('extract_memory', 'controlled-extraction', {'role': 'momo', 'text': '长期希望回复简短'}),
    ('dream_memory', 'controlled-dream', {'records': []}),
])
def test_independent_memory_calls_disable_thinking_only_on_official_host(
        monkeypatch, base_url, official, operation, model, source):
    from app.core.config import get_settings
    from app.services import memory_model

    settings = get_settings()
    monkeypatch.setattr(settings, 'llm_mode', 'live')
    monkeypatch.setattr(settings, 'openai_base_url', base_url)
    monkeypatch.setattr(settings, 'openai_api_key', 'synthetic-not-a-real-key')
    monkeypatch.setattr(settings, 'llm_model', 'controlled-chat')
    monkeypatch.setattr(settings, 'memory_extraction_model', 'controlled-extraction')
    monkeypatch.setattr(settings, 'memory_dream_model', 'controlled-dream')
    requests, clients = _sdk_transport(monkeypatch, memory_model,
        lambda body: {'role': 'assistant', 'content': '{"records":[]}'})

    assert getattr(memory_model, operation)(source) == {'records': []}
    assert len(requests) == 1
    body = requests[0]
    _assert_profile(body, official)
    assert body['model'] == model
    assert json.loads(body['messages'][-1]['content']) == source
    assert body['temperature'] == 0
    assert body['response_format'] == {'type': 'json_object'}
    assert 'max_tokens' not in body and 'max_completion_tokens' not in body
    assert 'tools' not in body
    assert body.get('stream', False) is False
    assert len(clients) == 1
    options, transport = clients[0]
    assert options['timeout'] == 20 and options['max_retries'] == 0
    assert transport.is_closed


LOOPBACK_PRELOAD = '''
const originalFetch = globalThis.fetch;
const expectedOrigin = new URL(process.env.CERES_WIRE_BASE).origin;
globalThis.fetch = (input, options) => {
  const url = new URL(input instanceof Request ? input.url : input);
  if (url.origin !== expectedOrigin) throw new Error('Unexpected provider origin');
  const target = new URL(url.pathname + url.search, process.env.CERES_WIRE_LOOPBACK);
  return originalFetch(input instanceof Request ? new Request(target, input) : target, options);
};
'''


@contextmanager
def _expression_server():
    """Real HTTP/SSE for the installed Pi and OpenAI SDKs, never a live model."""
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            if len(requests) == 1:
                content = '{"text":"按你的需要来就好。","fact_ref":"result"}\n'
            else:
                content = '{"merchant_claims":false,"execution_claims":false}'
            chunks = [
                {'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': content},
                              'finish_reason': None}]},
                {'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}],
                 'usage': {'prompt_tokens': 3, 'completion_tokens': 1, 'total_tokens': 4,
                           'prompt_tokens_details': {'cached_tokens': 0}}},
            ]
            data = ''.join('data: ' + json.dumps({
                'id': 'controlled-stream', 'object': 'chat.completion.chunk',
                'created': 0, 'model': body['model'], **chunk}) + '\n\n' for chunk in chunks)
            data += 'data: [DONE]\n\n'
            encoded = data.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize('base_url,official', HOSTS)
def test_expression_and_validator_disable_thinking_on_actual_sdk_wire(
        tmp_path, base_url, official):
    script = Path(__file__).resolve().parents[2] / 'runtime/pi/dist/result-expression.js'
    assert script.is_file(), 'Tester must build this worktree before the wire test'
    preload = tmp_path / 'loopback-fetch.mjs'
    preload.write_text(LOOPBACK_PRELOAD)
    start = {'run_id': 'expression-wire', 'facts': {'result': '已准备模拟清单'},
             'prompt': '只输出一行JSON', 'timeoutMs': 8000,
             'model': {'id': 'controlled-expression', 'baseUrl': base_url,
                       'apiKey': 'synthetic-not-a-real-key'}}
    with _expression_server() as (loopback, requests):
        completed = subprocess.run(['node', '--import', str(preload), str(script)],
            input=json.dumps(start, ensure_ascii=False) + '\n', capture_output=True,
            text=True, timeout=12, env={**{key: os.environ[key] for key in ('PATH', 'NODE_OPTIONS') if key in os.environ},
                'CERES_WIRE_BASE': base_url, 'CERES_WIRE_LOOPBACK': loopback})
    assert completed.returncode == 0, completed.stderr
    frames = [json.loads(line) for line in completed.stdout.splitlines()]
    assert frames[-1]['type'] == 'result' and frames[-1]['status'] == 'completed'
    assert [(frame['text'], frame['fact_ref']) for frame in frames if frame['type'] == 'unit'] == [
        ('按你的需要来就好。', 'result')]
    assert len(requests) == 2
    for body, limit in zip(requests, (512, 256)):
        _assert_profile(body, official)
        assert body['model'] == 'controlled-expression'
        # SDK compatibility chooses one cap field; neither path may raise its cap.
        assert [body[key] for key in ('max_tokens', 'max_completion_tokens') if key in body] == [limit]
        assert body['stream'] is True
        assert not body.get('tools')
        assert 'response_format' not in body
    usage = [frame for frame in frames if frame.get('phase') in ('generation_usage', 'validation_usage')]
    assert {frame['phase'] for frame in usage} == {'generation_usage', 'validation_usage'}
    assert all(frame['usage_source'] == 'provider' and frame['input_tokens'] == 3
               and frame['output_tokens'] == 1 and frame['cache_read_tokens'] == 0
               and frame['cache_write_tokens'] is None for frame in usage)

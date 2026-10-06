"""Installed OpenAI SDK -> controlled local HTTP transport -> real LangGraph/API.

This is wire compatibility with a deterministic fixture, not live qwen quality.
"""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from test_mercury_public import mercury_client


@contextmanager
def provider_server():
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            if body['messages'][-1]['role'] == 'tool':
                message = {'role': 'assistant', 'content': '已退款到账999元。'}
                finish = 'stop'
            else:
                message = {'role': 'assistant', 'content': None, 'tool_calls': [
                    {'id': 'read-order', 'type': 'function', 'function': {
                        'name': 'get_order_details', 'arguments': '{"order_id":"budget-order"}'}}]}
                finish = 'tool_calls'
            data = json.dumps({'id': 'fixture-completion', 'object': 'chat.completion',
                'created': 0, 'model': 'qwen3.8-27b', 'choices': [
                    {'index': 0, 'message': message, 'finish_reason': finish}]}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1', requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_public_query_uses_installed_sdk_http_tool_contract(mercury_client, monkeypatch):
    from app.core.config import get_settings
    client, app, url, sessions = mercury_client
    settings = get_settings()
    with provider_server() as (base_url, requests):
        monkeypatch.setattr(settings, 'openai_base_url', base_url)
        monkeypatch.setattr(settings, 'openai_api_key', 'synthetic-fixture-key')
        monkeypatch.setattr(settings, 'llm_model', 'qwen3.8-27b')
        response = client.post(url + '/turns/stream', json={'message': '查看订单', 'request_id': 'wire'})
    assert response.status_code == 200
    payloads = [json.loads(line.removeprefix('data: ')) for line in response.text.splitlines() if line.startswith('data: ')]
    assert payloads[-1]['status'] == 'completed'
    assert '15.00' in response.text and '测试杯' in response.text
    assert '999' not in payloads[-1]['final_text'] and '已退款到账' not in payloads[-1]['final_text']
    assert len(requests) == 2
    assert all(request['model'] == 'qwen3.8-27b' for request in requests)
    assert all(not tool['function']['name'].startswith('create_') for tool in requests[0]['tools'])
    assert requests[1]['messages'][-1]['role'] == 'tool'
    assert json.loads(requests[1]['messages'][-1]['content'])['data']['total'] == '15.00'
    assert client.get(url).json()['status'] == 'completed'

"""Controlled transport for the official DeepSeek thinking profile.

Captures safe request fields only. No provider credentials, headers, or message text.
"""
import json
import os
import selectors
import subprocess
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / 'runtime' / 'pi' / 'dist' / 'worker.js'
EXPRESSION = ROOT / 'runtime' / 'pi' / 'dist' / 'result-expression.js'
SYNTHETIC_KEY = 'synthetic-not-a-real-key'
PRELOAD = r'''
import { appendFileSync } from 'node:fs';

const capturePath = process.env.CERES_TRANSPORT_CAPTURE;
let toolSent = false;

function chunk(delta, finish) {
  return {id:'c', object:'chat.completion.chunk', created:1, model:'deepseek-flash', choices:[{index:0, delta, finish_reason:finish}]};
}
function sse(parts) {
  return parts.map((part) => 'data: ' + JSON.stringify(part)).join('\n\n') + '\n\ndata: [DONE]\n\n';
}
function withUsage(part, completionTokens) {
  return {...part, usage:{prompt_tokens:3, completion_tokens:completionTokens, total_tokens:3 + completionTokens, completion_tokens_details:{reasoning_tokens:0}}};
}
function textChunks(text) {
  return sse([chunk({role:'assistant', content:''}, null), chunk({content:text}, null), withUsage(chunk({}, 'stop'), 1)]);
}
function toolChunks() {
  return sse([
    chunk({role:'assistant', tool_calls:[{index:0, id:'call_1', type:'function', function:{name:'validate_general_text', arguments:''}}]}, null),
    chunk({tool_calls:[{index:0, function:{arguments:'{"messages":["hi"]}'}}]}, null),
    withUsage(chunk({}, 'tool_calls'), 8),
  ]);
}

globalThis.fetch = async (_url, init) => {
  const raw = typeof init.body === 'string' ? init.body : Buffer.from(init.body).toString('utf8');
  const body = JSON.parse(raw);
  const limit = Object.hasOwn(body, 'max_tokens') ? body.max_tokens : (body.max_completion_tokens ?? null);
  const record = {
    model: body.model,
    limit,
    max_tokens: Object.hasOwn(body, 'max_tokens') ? body.max_tokens : null,
    max_completion_tokens: Object.hasOwn(body, 'max_completion_tokens') ? body.max_completion_tokens : null,
    thinking: Object.hasOwn(body, 'thinking') ? body.thinking : null,
    reasoning_effort: Object.hasOwn(body, 'reasoning_effort') ? body.reasoning_effort : null,
    response_format: Object.hasOwn(body, 'response_format') ? body.response_format : null,
    tool_choice: Object.hasOwn(body, 'tool_choice') ? body.tool_choice : null,
    stream: body.stream === true,
    tool_count: Array.isArray(body.tools) ? body.tools.length : 0,
  };
  appendFileSync(capturePath, JSON.stringify(record) + '\n');
  let payload = textChunks('ok');
  if (limit === 1536 && record.tool_count > 0 && !toolSent) {
    toolSent = true;
    payload = toolChunks();
  } else if (limit === 256) {
    payload = textChunks('{"merchant_claims":false,"execution_claims":false}');
  } else if (limit === 512) {
    payload = textChunks('{"text":"已准备清单","fact_ref":"plan"}\n');
  }
  return new Response(payload, {status:200, headers:{'content-type':'text/event-stream'}});
};
'''


def _safe(body):
    return {
        'model': body.get('model'),
        'thinking': body.get('thinking') if 'thinking' in body else None,
        'reasoning_effort': body.get('reasoning_effort') if 'reasoning_effort' in body else None,
        'max_tokens': body.get('max_tokens') if 'max_tokens' in body else None,
        'max_completion_tokens': body.get('max_completion_tokens') if 'max_completion_tokens' in body else None,
        'response_format': body.get('response_format') if 'response_format' in body else None,
        'temperature': body.get('temperature'),
        'stream': body.get('stream', False),
    }


def _configure(monkeypatch, base_url):
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, 'llm_mode', 'live')
    monkeypatch.setattr(settings, 'openai_base_url', base_url)
    monkeypatch.setattr(settings, 'openai_api_key', SYNTHETIC_KEY)
    monkeypatch.setattr(settings, 'llm_model', 'deepseek-flash')
    monkeypatch.setattr(settings, 'memory_extraction_model', 'deepseek-flash')
    monkeypatch.setattr(settings, 'memory_dream_model', 'deepseek-flash')


def _bind(monkeypatch, module, captured):
    real = module.OpenAI

    def handler(request):
        body = json.loads(request.content.decode())
        captured.append(_safe(body))
        content = '{"records":[]}'
        return httpx.Response(200, json={
            'id': 'controlled', 'object': 'chat.completion', 'created': 1, 'model': body.get('model'),
            'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': content}}],
            'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2},
        })

    def wrapped(**kwargs):
        kwargs['http_client'] = httpx.Client(transport=httpx.MockTransport(handler))
        return real(**kwargs)

    monkeypatch.setattr(module, 'OpenAI', wrapped)


def _python_bodies(monkeypatch, base_url):
    from app.mercury.provider import QueryChatClient
    from app.services import memory_model
    captured = []
    _configure(monkeypatch, base_url)
    _bind(monkeypatch, __import__('app.mercury.provider', fromlist=['provider']), captured)
    _bind(monkeypatch, memory_model, captured)
    QueryChatClient().chat([{'role': 'user', 'content': '查询'}], tools=[])
    assert memory_model.extract_memory({'role': 'user', 'text': '长期偏好无糖'}) == {'records': []}
    assert memory_model.dream_memory({'records': []}) == {'records': []}
    return captured


@pytest.mark.parametrize('base_url', ['https://api.deepseek.com/v1', 'https://API.DEEPSEEK.COM/v1'])
def test_python_official_deepseek_disables_thinking(monkeypatch, base_url):
    mercury, extract, dream = _python_bodies(monkeypatch, base_url)
    disabled = {'type': 'disabled'}
    assert mercury['model'] == extract['model'] == dream['model'] == 'deepseek-flash'
    assert mercury['thinking'] == extract['thinking'] == dream['thinking'] == disabled
    assert mercury['reasoning_effort'] is extract['reasoning_effort'] is dream['reasoning_effort'] is None
    assert mercury['max_tokens'] is extract['max_tokens'] is dream['max_tokens'] is None
    assert mercury['temperature'] == 0.2 and mercury['response_format'] is None and mercury['stream'] is False
    assert extract['temperature'] == dream['temperature'] == 0
    assert extract['response_format'] == dream['response_format'] == {'type': 'json_object'}
    assert extract['stream'] is dream['stream'] is False


@pytest.mark.parametrize('base_url', [
    'http://provider-fixture.invalid/v1',
    'https://api.deepseek.com.evil.example/v1',
])
def test_python_non_official_host_omits_thinking(monkeypatch, base_url):
    bodies = _python_bodies(monkeypatch, base_url)
    assert len(bodies) == 3
    assert all(body['thinking'] is None and body['reasoning_effort'] is None for body in bodies)
    assert all(body['max_tokens'] is None for body in bodies)


def _records(path):
    text = path.read_text()
    assert SYNTHETIC_KEY not in text
    assert 'authorization' not in text.lower()
    return [json.loads(line) for line in text.splitlines() if line]


def _spawn(script, tmp_path, name):
    directory = tmp_path / name
    directory.mkdir()
    preload = directory / 'transport-preload.mjs'
    capture = directory / 'capture.jsonl'
    stderr_path = directory / 'stderr.txt'
    preload.write_text(PRELOAD)
    stderr = stderr_path.open('wb')
    env = {'PATH': os.environ['PATH'], 'CERES_TRANSPORT_CAPTURE': str(capture)}
    child = subprocess.Popen(
        ['node', '--import', str(preload), str(script)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, env=env, bufsize=0,
    )
    return child, capture, stderr, stderr_path


def _finish(child, stderr, stderr_path):
    if child.poll() is None:
        child.kill()
    child.wait(timeout=5)
    stderr.close()
    tail = stderr_path.read_text(errors='replace')[-2000:].replace(SYNTHETIC_KEY, '[redacted]')
    return tail


def _read_frames(child, send, on_frame):
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ)
    pending = b''
    frames = []
    deadline = time.monotonic() + 10
    try:
        while time.monotonic() < deadline:
            if child.poll() is not None and not selector.select(timeout=0):
                break
            if not selector.select(timeout=0.2):
                continue
            chunk = os.read(child.stdout.fileno(), 65536)
            if not chunk:
                break
            pending += chunk
            while b'\n' in pending:
                raw, pending = pending.split(b'\n', 1)
                frame = json.loads(raw)
                frames.append({key: value for key, value in frame.items() if key in ('type', 'status', 'name', 'code')})
                if on_frame(frame, send):
                    return frames
        return frames
    finally:
        selector.close()


def _run_worker(base_url, tmp_path):
    from app.prompts.experience import keke_modules
    child, capture, stderr, stderr_path = _spawn(WORKER, tmp_path, 'worker')
    sequence = 0

    def send(frame):
        nonlocal sequence
        sequence += 1
        payload = {**frame, 'run_id': 'transport-run', 'sequence': sequence}
        child.stdin.write((json.dumps(payload, ensure_ascii=False) + '\n').encode())
        child.stdin.flush()

    def on_frame(frame, reply):
        if frame.get('type') == 'tool_call' and frame.get('name') == 'validate_general_text':
            reply({'type': 'tool_result', 'id': frame['id'], 'result': {'general_ref': 'general-transport'}})
        return frame.get('type') in ('result', 'error')

    try:
        send({'type': 'start', 'message': '普通解释', 'categories': [{'id': 'beverage', 'name_zh': '饮料'}],
              'context': {'capability': 'chat', 'has_active_task': False, 'general_history': []},
              'promptModules': keke_modules(), 'maxToolRounds': 5, 'timeoutMs': 8000,
              'model': {'id': 'deepseek-flash', 'baseUrl': base_url, 'apiKey': SYNTHETIC_KEY}})
        frames = _read_frames(child, send, on_frame)
    finally:
        tail = _finish(child, stderr, stderr_path)
    assert any(frame['type'] in ('result', 'error') for frame in frames), tail
    return _records(capture), frames


def _run_expression(base_url, tmp_path):
    child, capture, stderr, stderr_path = _spawn(EXPRESSION, tmp_path, 'expression')
    start = {'run_id': 'expression-transport', 'facts': {'plan': '清单已生成'}, 'prompt': '只输出一行JSON',
             'timeoutMs': 8000, 'model': {'id': 'deepseek-flash', 'baseUrl': base_url, 'apiKey': SYNTHETIC_KEY}}
    try:
        child.stdin.write((json.dumps(start, ensure_ascii=False) + '\n').encode())
        child.stdin.flush()
        frames = _read_frames(child, None, lambda frame, _reply: frame.get('type') == 'result')
    finally:
        tail = _finish(child, stderr, stderr_path)
    assert any(frame['type'] == 'result' for frame in frames), tail
    return _records(capture)


def _assert_disabled(row, limit):
    assert row['model'] == 'deepseek-flash'
    assert row['thinking'] == {'type': 'disabled'}
    assert row['reasoning_effort'] is None
    assert row['stream'] is True
    assert row['limit'] == limit
    assert row['max_tokens'] == limit
    assert row['max_completion_tokens'] is None


def test_node_official_deepseek_disables_thinking_on_pi_and_expression(tmp_path):
    worker, frames = _run_worker('https://API.DEEPSEEK.COM/v1', tmp_path)
    expression = _run_expression('https://api.deepseek.com/v1', tmp_path)
    mains = [row for row in worker if row['limit'] == 1536]
    validators = [row for row in worker if row['limit'] == 256]
    assert mains and validators, frames
    for row in mains:
        _assert_disabled(row, 1536)
        # Native tool arguments carry final refs; JSON mode would constrain
        # the optional prose accompanying an actual tool call (ADR 0004).
        assert row['response_format'] is None
        assert row['tool_choice'] == 'auto'
        assert row['tool_count'] > 0
    for row in validators:
        _assert_disabled(row, 256)
        assert row['response_format'] is None
    assert [row['limit'] for row in expression] == [512, 256]
    _assert_disabled(expression[0], 512)
    _assert_disabled(expression[1], 256)
    assert all(row['response_format'] is None for row in expression)


def test_node_non_official_host_omits_thinking(tmp_path):
    worker, _frames = _run_worker('http://127.0.0.1:9/v1', tmp_path)
    # The installed SDK treats any baseUrl containing "deepseek.com" as DeepSeek for
    # max_tokens. This hostname is still not the official API, so thinking stays omitted.
    expression = _run_expression('https://api.deepseek.com.evil.example/v1', tmp_path)
    assert any(row['limit'] == 1536 and row['max_completion_tokens'] == 1536 and row['max_tokens'] is None for row in worker)
    assert any(row['limit'] == 256 and row['max_completion_tokens'] == 256 and row['max_tokens'] is None for row in worker)
    assert [row['limit'] for row in expression] == [512, 256]
    assert all(row['max_tokens'] == row['limit'] and row['max_completion_tokens'] is None for row in expression)
    for row in worker + expression:
        assert row['thinking'] is None and row['reasoning_effort'] is None and row['response_format'] is None

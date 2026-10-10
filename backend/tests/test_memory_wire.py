"""Installed OpenAI provider SDK feeds a real Mercury memory graph tool."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from test_mercury_public import mercury_client
from test_memory_mercury import payload


@contextmanager
def memory_provider():
    observed=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            observed.append(body)
            command={'action':'save','category':'feedback','domain':'communication','key':'style',
                'content':'请简短回答','source_quote':'记住请简短回答'}
            data=json.dumps({'id':'memory-wire','object':'chat.completion','created':0,'model':'qwen3.8-27b',
                'choices':[{'index':0,'finish_reason':'tool_calls','message':{'role':'assistant','content':None,
                    'tool_calls':[{'id':'memory-command','type':'function','function':{'name':'memory_command',
                        'arguments':json.dumps(command,ensure_ascii=False)}}]}}]}).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try: yield f'http://127.0.0.1:{server.server_port}/v1',observed
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_actual_provider_wire_memory_tool_commits_truthful_receipt(mercury_client,monkeypatch):
    from app.core.config import get_settings
    client,app,url,sessions=mercury_client
    settings=get_settings()
    with memory_provider() as (base_url,observed):
        monkeypatch.setattr(settings,'openai_base_url',base_url)
        monkeypatch.setattr(settings,'openai_api_key','synthetic-memory-wire-key')
        monkeypatch.setattr(settings,'llm_model','qwen3.8-27b')
        result=payload(client.post(url+'/turns/stream',json={'message':'记住请简短回答','request_id':'wire'}))
    assert result['status']=='completed'
    assert result['action_results'][0]['records'][0]['content']=='请简短回答'
    tool=next(t for t in observed[0]['tools'] if t['function']['name']=='memory_command')
    assert tool['function']['parameters']['additionalProperties'] is False
    assert 'owner_id' not in tool['function']['parameters']['properties']
    assert observed[0]['model']=='qwen3.8-27b'
    assert 'thinking' not in observed[0] and 'reasoning_effort' not in observed[0]
    assert '已记住' in client.get(url).json()['messages'][-1]['content']

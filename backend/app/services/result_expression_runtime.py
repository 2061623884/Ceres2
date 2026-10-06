"""Bounded tool-free Pi transport for already-committed result introductions."""
import hashlib
import json
import logging
import re
import os
from pathlib import Path
import selectors
import subprocess
import time

from app.core.config import get_settings
from app.core.errors import AppError
from app.prompts.experience import MODULES

LOGGER = logging.getLogger(__name__)
DIAGNOSTIC_CODES = {'expression_parse', 'invalid_unit', 'validation_parse', 'validation_rejected', 'validation_provider', 'generation_provider', 'aborted', 'deadline', 'validation_tool_call', 'generation_tool_call', 'expression_limit', 'empty_output'}

WORKER = Path(__file__).resolve().parents[3] / 'runtime/pi/dist/result-expression.js'


def generate_introduction(run_id, facts, *, role, deadline, should_stop, on_unit, on_metric):
    settings = get_settings()
    if not settings.is_live_llm_configured() or not WORKER.is_file():
        raise AppError(503, 'EXPRESSION_UNAVAILABLE', '介绍暂时不可用，已有结果保留。')
    env = {key:os.environ[key] for key in ('PATH','SYSTEMROOT','HOME','HTTP_PROXY','HTTPS_PROXY','NO_PROXY','http_proxy','https_proxy','no_proxy','NODE_EXTRA_CA_CERTS') if key in os.environ}
    child = subprocess.Popen(['node', str(WORKER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    selector = selectors.DefaultSelector()
    selector.register(child.stdout, selectors.EVENT_READ, 'stdout')
    selector.register(child.stderr, selectors.EVENT_READ, 'stderr')
    stderr_tail = b''
    pending = b''
    sequence = 0
    try:
        start = {'run_id':run_id, 'facts':facts, 'prompt':MODULES['expression'][role]+MODULES['result_introduction'],
                 'timeoutMs':max(1, int((deadline-time.monotonic())*1000)),
                 'model':{'id':settings.llm_model,'baseUrl':settings.openai_base_url,'apiKey':settings.openai_api_key}}
        child.stdin.write((json.dumps(start, ensure_ascii=False)+'\n').encode()); child.stdin.flush()
        while True:
            if should_stop():
                return 'stopped'
            if time.monotonic() >= deadline:
                return 'deadline'
            ready = selector.select(timeout=min(.05, max(0,deadline-time.monotonic())))
            if not ready:
                if child.poll() is not None:
                    raise AppError(502, 'EXPRESSION_INTERRUPTED', '介绍中断，已有结果保留。')
                continue
            for key, _mask in sorted(ready, key=lambda item:item[0].data != 'stderr'):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if key.data == 'stderr':
                    stderr_tail = (stderr_tail + chunk)[-4096:]
                    if not chunk:
                        selector.unregister(key.fileobj)
                elif not chunk:
                    raise AppError(502, 'EXPRESSION_INTERRUPTED', '介绍中断，已有结果保留。')
                else:
                    pending += chunk
            if len(pending)>262144:
                raise AppError(502, 'EXPRESSION_PROTOCOL_INVALID', '介绍格式无效，已有结果保留。')
            while b'\n' in pending:
                # Earlier callbacks may have waited on the database. Recheck
                # before exposing every buffered frame, not just before select.
                if time.monotonic() >= deadline:
                    return 'deadline'
                raw,pending = pending.split(b'\n',1)
                frame = json.loads(raw)
                sequence += 1
                if frame.get('run_id') != run_id or frame.get('sequence') != sequence:
                    raise AppError(502, 'EXPRESSION_PROTOCOL_INVALID', '介绍关联无效，已有结果保留。')
                if should_stop():
                    return 'stopped'
                if frame['type']=='unit':
                    if set(frame)!={'run_id','sequence','type','text','fact_ref'} or not isinstance(frame['text'],str) or not 0<len(frame['text'])<=100 or frame['fact_ref'] not in facts:
                        raise AppError(502, 'EXPRESSION_PROTOCOL_INVALID', '介绍引用无效，已有结果保留。')
                    on_unit(frame['text'], frame['fact_ref'])
                elif frame['type']=='metric':
                    on_metric({key:value for key,value in frame.items() if key in ('phase','at_ms','model_calls','input_tokens','output_tokens','cache_read_tokens','cache_write_tokens','usage_source','input_token_scope')})
                elif frame['type']=='result' and frame.get('status') in ('completed','failed','deadline'):
                    diagnostic = frame.get('diagnostic')
                    if diagnostic is not None:
                        if not isinstance(diagnostic, dict) or set(diagnostic) != {'code','cause','fingerprint'} or diagnostic['code'] not in DIAGNOSTIC_CODES or diagnostic['cause'] not in ('Error','SyntaxError','TypeError','AbortError') or not isinstance(diagnostic['fingerprint'], str) or not re.fullmatch(r'[0-9a-f]{64}', diagnostic['fingerprint']):
                            raise AppError(502, 'EXPRESSION_PROTOCOL_INVALID', '介绍诊断格式无效，已有结果保留。')
                        LOGGER.error('Expression failure run_id=%s diagnostic=%s', run_id, diagnostic)
                    return frame['status']
                else:
                    raise AppError(502, 'EXPRESSION_PROTOCOL_INVALID', '介绍格式无效，已有结果保留。')
    finally:
        selector.close()
        if child.poll() is None:
            child.kill()
        child.wait()
        child.stdin.close(); child.stdout.close(); child.stderr.close()
        if stderr_tail:
            marker = re.search(rb'\b(ERR_MODULE_NOT_FOUND|MODULE_NOT_FOUND|SyntaxError|TypeError|EACCES|ENOENT)\b', stderr_tail)
            LOGGER.error('Expression failure run_id=%s diagnostic=%s', run_id, {'code':'worker_stderr', 'cause':marker.group(1).decode() if marker else 'WorkerProcessError', 'fingerprint':hashlib.sha256(stderr_tail).hexdigest()})

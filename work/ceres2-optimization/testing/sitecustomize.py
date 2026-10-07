"""Opt-in, test-only safe projection of Pi runtime events for live sampling."""

from __future__ import annotations

import json
import os
import shutil
from collections import Counter
from pathlib import Path
from types import SimpleNamespace


_output = os.environ.get("PI_DIAGNOSTIC_OUT")
if _output:
    import app.services.pi_product_runtime as _runtime_module

    _node_worker_dir = os.environ.get("PI_NODE_SHAPE_WORKER_DIR")
    if _node_worker_dir:
        _root = Path(__file__).resolve().parents[3]
        _source = _root / "runtime/pi/dist"
        _destination = Path(_node_worker_dir)
        shutil.copytree(_source, _destination, dirs_exist_ok=True)
        shutil.copy2(_root / "runtime/pi/package.json", _destination / "package.json")
        (_destination / "node_modules").symlink_to(
            _root / "runtime/pi/node_modules", target_is_directory=True
        )
        _worker = _destination / "worker.js"
        _text = _worker.read_text()
        _needle = "        if (event.type === 'message_end' && event.message.role === 'assistant') {\n            recordUsage('main', event.message.usage);"
        _replacement = """        if (event.type === 'message_end' && event.message.role === 'assistant') {
            const shapeBlocks = event.message.content;
            const shapeText = shapeBlocks.filter(block => block.type === 'text').map(block => block.text).join('');
            let shape = shapeText.trim() ? 'plain_text' : 'empty';
            let observedJsonKeys = [];
            try {
                const parsedShape = JSON.parse(shapeText);
                shape = Array.isArray(parsedShape) ? 'json_array' : parsedShape && typeof parsedShape === 'object' ? 'json_object' : 'json_scalar';
                if (parsedShape && typeof parsedShape === 'object' && !Array.isArray(parsedShape)) {
                    observedJsonKeys = Object.keys(parsedShape).filter(key => ['content', 'tool_calls', 'interim_message', 'status', 'answer_kind'].includes(key)).sort();
                }
            } catch { /* Record only the structural class and allowlisted keys. */ }
            send({ type: 'event', event: { type: 'main_message_shape', stop_reason: event.message.stopReason,
                text_characters: shapeText.length, text_block_count: shapeBlocks.filter(block => block.type === 'text').length,
                tool_call_count: shapeBlocks.filter(block => block.type === 'toolCall').length,
                text_shape: shape, observed_json_keys: observedJsonKeys } });
            recordUsage('main', event.message.usage);"""
        if _needle not in _text:
            raise RuntimeError("Pi worker shape instrumentation insertion point changed")
        _text = _text.replace(_needle, _replacement, 1)
        _rejected_text_path = os.environ.get("PI_REJECTED_INTERIM_TEXT_OUT")
        if _rejected_text_path:
            _fs_import = "import { createHash } from 'node:crypto';"
            if _fs_import not in _text:
                raise RuntimeError("Pi worker rejected-text instrumentation import point changed")
            _text = _text.replace(
                _fs_import,
                _fs_import + "\nimport { appendFileSync } from 'node:fs';",
                1,
            )
            _audit_needle = "                        send({ type: 'event', event: { type: 'interim_audit', message_id: messageId, approved } });"
            _audit_replacement = _audit_needle + "\n            if (!approved) appendFileSync(process.env.PI_REJECTED_INTERIM_TEXT_OUT, JSON.stringify({candidate}) + '\\n', 'utf8');"
            if _audit_needle not in _text:
                raise RuntimeError("Pi worker rejected interim-audit instrumentation insertion point changed")
            _text = _text.replace(_audit_needle, _audit_replacement, 1)
        _worker.write_text(_text)
        _runtime_module.WORKER = _worker

    PiProductRuntime = _runtime_module.PiProductRuntime

    _original_run = PiProductRuntime.run
    _preload = os.environ.get("NODE_OPTIONS")
    _fetch_mode = os.environ.get("PI_FETCH_MODE")
    _fetch_report = os.environ.get("PI_FETCH_DIAGNOSTIC_OUT")
    _rejected_text_path = os.environ.get("PI_REJECTED_INTERIM_TEXT_OUT")
    _child_instrumentation = {
        "worker_launches_matched": 0,
        "node_options_injected": False,
        "fetch_mode_injected": False,
        "fetch_report_path_configured": False,
        "rejected_text_capture_path_injected": False,
    }
    if _preload or _fetch_mode or _fetch_report:
        import subprocess as _subprocess

        _original_popen = _subprocess.Popen

        def _instrumented_popen(command, *args, **kwargs):
            worker = _runtime_module.WORKER
            if (
                isinstance(command, (list, tuple))
                and len(command) >= 2
                and command[0] == "node"
                and Path(command[1]) == Path(worker)
            ):
                _child_instrumentation["worker_launches_matched"] += 1
                child_env = dict(kwargs.get("env") or os.environ)
                if _preload:
                    child_env["NODE_OPTIONS"] = _preload
                    _child_instrumentation["node_options_injected"] = True
                if _fetch_mode:
                    child_env["PI_FETCH_MODE"] = _fetch_mode
                    _child_instrumentation["fetch_mode_injected"] = True
                if _fetch_report:
                    child_env["PI_FETCH_DIAGNOSTIC_OUT"] = _fetch_report
                    _child_instrumentation["fetch_report_path_configured"] = True
                if _rejected_text_path:
                    child_env["PI_REJECTED_INTERIM_TEXT_OUT"] = _rejected_text_path
                    _child_instrumentation["rejected_text_capture_path_injected"] = True
                kwargs["env"] = child_env
            return _original_popen(command, *args, **kwargs)

        _runtime_module.subprocess = SimpleNamespace(Popen=_instrumented_popen, PIPE=_subprocess.PIPE)

    def _capture_runtime_events(self, *args, **kwargs):
        result = None
        error = None
        try:
            result = _original_run(self, *args, **kwargs)
            return result
        except Exception as exc:
            error = exc
            raise
        finally:
            events = list(getattr(self, "events", ()))
            counts = Counter(event.get("type", "unknown") for event in events)
            rows = []
            for event in events:
                kind = event.get("type")
                if kind == "interim_candidate":
                    rows.append({
                        "type": kind,
                        "status": event.get("status"),
                        "text_characters": event.get("text_characters"),
                        "tool_call_count": event.get("tool_call_count"),
                    })
                elif kind == "model_usage":
                    rows.append({key: event.get(key) for key in (
                        "type", "kind", "model", "provider_host", "duration_ms", "usage", "cost"
                    )})
                elif kind == "tool_execution_start":
                    rows.append({"type": kind, "tool_name": event.get("toolName")})
                elif kind == "interim_audit":
                    rows.append({"type": kind, "approved": event.get("approved")})
                elif kind == "main_message_shape":
                    rows.append({key: event.get(key) for key in (
                        "type", "stop_reason", "text_characters", "text_block_count",
                        "tool_call_count", "text_shape", "observed_json_keys",
                    )})
                else:
                    rows.append({"type": kind})

            exception = None
            if error is not None:
                detail = getattr(error, "detail", None)
                error_detail = detail.get("error", {}) if isinstance(detail, dict) else {}
                diagnostic = error_detail.get("diagnostic", {}) if isinstance(error_detail, dict) else {}
                allowlisted = (
                    "kind", "code", "fingerprint", "upstream_http_status", "transport_phase",
                    "transport_error_class", "transport_error_code",
                )
                exception = {
                    "exception_class": type(error).__name__,
                    "error_code": error_detail.get("code") if isinstance(error_detail, dict) else None,
                    "transport_diagnostic": {
                        key: diagnostic.get(key) for key in allowlisted if key in diagnostic
                    } if isinstance(diagnostic, dict) else {},
                }

            capture = {
                "event_type_counts": dict(counts),
                "safe_events": rows,
                "runtime_status": result.get("status") if isinstance(result, dict) else None,
                "exception": exception,
                "test_child_launch_instrumentation": _child_instrumentation,
                "raw_text_or_request_body_recorded": False,
                "provider_secret_recorded": False,
            }
            try:
                destination = Path(_output)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(json.dumps(capture, ensure_ascii=False, indent=2) + "\n")
            except Exception:
                # Diagnostics must never change the observed runtime outcome.
                pass

    PiProductRuntime.run = _capture_runtime_events

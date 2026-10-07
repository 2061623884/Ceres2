"""One actual DeepSeek Pi turn through the public Guide/SSE host boundary."""

from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
TESTING = Path(__file__).resolve().parent
SAMPLE_ID = os.environ.get("PI_REAL_SAMPLE_ID", "soda-revised")
SAMPLES = {
    "soda-revised": "帮我查查可乐有哪些规格和当前模拟价格；先告诉我你准备核对什么，然后继续查询，暂时不要加购。",
    "soda-revised-diagnostic": "帮我查查可乐有哪些规格和当前模拟价格；先告诉我你准备核对什么，然后继续查询，暂时不要加购。",
    "recipe-relations": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-baseline": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-no-json-mode": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-baseline-v2": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-no-json-mode-v2": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-baseline-instrumented": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-no-json-mode-instrumented": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-baseline-fetch": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-no-json-mode-fetch": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-baseline-wire-v2": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-relations-ab-no-json-mode-wire-v2": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "product-policy": "我想买一盒酸奶。先说明你会核对什么，再查合适商品和当前模拟价格，并确认未开封买错时是否有适用的退货政策；不要下单。",
    "product-policy-diagnostic": "我想买一盒酸奶。先说明你会核对什么，再查合适商品和当前模拟价格，并确认未开封买错时是否有适用的退货政策；不要下单。",
    "soda-native-tools-v1": "帮我查查可乐有哪些规格和当前模拟价格；先告诉我你准备核对什么，然后继续查询，暂时不要加购。",
    "product-policy-native-tools-v1": "我想买一盒酸奶。先说明你会核对什么，再查合适商品和当前模拟价格，并确认未开封买错时是否有适用的退货政策；不要下单。",
    "recipe-relations-native-tools-v1": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "soda-native-tools-auto-v1": "帮我查查可乐有哪些规格和当前模拟价格；先告诉我你准备核对什么，然后继续查询，暂时不要加购。",
    "product-policy-native-tools-auto-v1": "我想买一盒酸奶。先说明你会核对什么，再查合适商品和当前模拟价格，并确认未开封买错时是否有适用的退货政策；不要下单。",
    "recipe-relations-native-tools-auto-v1": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "soda-native-tools-production-v2": "帮我查查可乐有哪些规格和当前模拟价格；先告诉我你准备核对什么，然后继续查询，暂时不要加购。",
    "product-policy-native-tools-production-v2": "我想买一盒酸奶。先说明你会核对什么，再查合适商品和当前模拟价格，并确认未开封买错时是否有适用的退货政策；不要下单。",
    "recipe-relations-native-tools-production-v2": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "recipe-facts-native-tools-production-v1": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "soda-native-tools-rejected-audit-capture-v1": "帮我查查可乐有哪些规格和当前模拟价格；先告诉我你准备核对什么，然后继续查询，暂时不要加购。",
    "soda-native-tools-rejected-audit-capture-v2": "帮我查查可乐有哪些规格和当前模拟价格；先告诉我你准备核对什么，然后继续查询，暂时不要加购。",
    "product-policy-rejected-audit-capture-v1": "我想买一盒酸奶。先说明你会核对什么，再查合适商品和当前模拟价格，并确认未开封买错时是否有适用的退货政策；不要下单。",
    "product-policy-rejected-audit-capture-v2": "我想买一盒酸奶。先说明你会核对什么，再查合适商品和当前模拟价格，并确认未开封买错时是否有适用的退货政策；不要下单。",
    "recipe-facts-rejected-audit-capture-v1": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "soda-native-tools-production-v3-current-interim-claim": "帮我查查可乐有哪些规格和当前模拟价格；先告诉我你准备核对什么，然后继续查询，暂时不要加购。",
    "product-policy-native-tools-production-v3-current-interim-claim": "我想买一盒酸奶。先说明你会核对什么，再查合适商品和当前模拟价格，并确认未开封买错时是否有适用的退货政策；不要下单。",
    "recipe-facts-native-tools-production-v2-current-interim-claim": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
    "product-policy-current-v4": "我想买一盒酸奶。先说明你会核对什么，再查合适商品和当前模拟价格，并确认未开封买错时是否有适用的退货政策；不要下单。",
    "recipe-relations-current-v4": "我想做番茄炒蛋和蛋炒饭。先说明你要核对哪些菜谱关系，再查两道菜的食材、用量和鸡蛋有哪些商品规格与模拟价格，不要加购。",
}
if SAMPLE_ID not in SAMPLES:
    raise ValueError("PI_REAL_SAMPLE_ID must name one of the versioned sample cases")
REQUEST_TEXT = SAMPLES[SAMPLE_ID]
PORT = int(os.environ.get("PI_REAL_SAMPLE_PORT", "18014"))
DISABLE_TESTSITE = os.environ.get("PI_REAL_DISABLE_TESTSITE") == "1"
TMP = TESTING / "tmp" / "pi-real-smoke" / SAMPLE_ID
DB = TMP / "business.sqlite3"
CHECKPOINT = TMP / "checkpoint.sqlite3"
BASE_URL = f"http://127.0.0.1:{PORT}"
REQUEST_ID = f"pi-live-{hashlib.sha256(SAMPLE_ID.encode()).hexdigest()[:16]}-20261007"
ELEMENTS = (
    "backend/app/prompts/experience.json",
    "backend/app/prompts/experience.py",
    "backend/app/services/pi_product_runtime.py",
    "backend/app/services/pi_product_turn_service.py",
    "backend/app/services/guide_run_service.py",
    "backend/app/models/guide.py",
    "backend/app/evaluation/export_runs.py",
    "runtime/pi/src/worker.ts",
    "runtime/pi/dist/worker.js",
    "runtime/pi/src/general-claim.ts",
    "runtime/pi/dist/general-claim.js",
    "runtime/pi/src/prompt-modules.ts",
    "work/ceres2-optimization/testing/sitecustomize.py",
    "work/ceres2-optimization/testing/strip_response_format_preload.mjs",
    "data/fixtures/products.json",
    "data/fixtures/recipes.json",
    "data/fixtures/policies.json",
    "evals/ceres2-optimization-retrieval-dev.json",
)


def approved_provider_config() -> dict[str, str]:
    path = Path("/data/amax/Documents/projects/Agent/Agent产品/Ceres2/.env")
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    config = {key: values.get(key, "") for key in ("OPENAI_BASE_URL", "OPENAI_API_KEY", "LLM_MODEL")}
    if not all(config.values()):
        raise RuntimeError("Approved provider settings are incomplete")
    return config


def source_hashes() -> dict[str, str]:
    return {relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() for relative in ELEMENTS}


def json_request(opener: urllib.request.OpenerDirector, method: str, path: str, body: dict | None = None, timeout: int = 30) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    request = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with opener.open(request, timeout=timeout) as response:
        payload = response.read()
    return json.loads(payload)


def wait_health(process: subprocess.Popen, timeout: float = 25) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"isolated uvicorn exited with status {process.returncode}")
        try:
            with urllib.request.urlopen(BASE_URL + "/health", timeout=2) as response:
                return json.loads(response.read())
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    raise RuntimeError("isolated uvicorn did not become ready")


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    output = TESTING / f"pi-real-provider-{SAMPLE_ID}-2026-10-07.json"
    raw_sse = TMP / "guide-sse.jsonl"
    provider = approved_provider_config()
    env = {key: os.environ[key] for key in ("PATH", "HOME", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy", "NODE_EXTRA_CA_CERTS") if key in os.environ}
    env.update(provider)
    env.update({
        "DATABASE_URL": f"sqlite:///{DB}",
        "MERCURY_CHECKPOINT_PATH": str(CHECKPOINT),
        "LLM_MODE": "live",
        # Keep the Pi call live while preventing the unrelated automatic
        # memory worker from making a second model call after this sample.
        "MEMORY_EXTRACTION_MODEL": "",
        "MEMORY_DREAM_MODEL": "",
    })
    seed_env = dict(env, LLM_MODE="demo")
    seed = subprocess.run([str(ROOT / ".venv/bin/python"), "-m", "app.services.seed_service"], cwd=BACKEND, env=seed_env, capture_output=True, text=True, timeout=30)
    if seed.returncode != 0:
        raise RuntimeError(f"isolated fixture import failed with exit {seed.returncode}")
    server_env = dict(env)
    if not DISABLE_TESTSITE:
        server_env.update({
            "PYTHONPATH": os.pathsep.join((str(TESTING), str(BACKEND))),
            "PI_DIAGNOSTIC_OUT": str(TMP / "runtime-event-diagnostics.json"),
        })
        if os.environ.get("PI_CAPTURE_REJECTED_INTERIM_TEXT") == "1":
            server_env["PI_REJECTED_INTERIM_TEXT_OUT"] = str(TMP / "rejected-audit-candidates.jsonl")
    if not DISABLE_TESTSITE and os.environ.get("PI_CAPTURE_NODE_SHAPE") == "1":
        server_env.update({
            "PI_NODE_SHAPE_WORKER_DIR": str(TMP / "instrumented-runtime"),
            "PI_FETCH_DIAGNOSTIC_OUT": str(TMP / "fetch-instrumentation.json"),
            "PI_FETCH_MODE": os.environ.get("PI_FETCH_MODE", "observe"),
            "NODE_OPTIONS": f"--import={TESTING / 'strip_response_format_preload.mjs'}",
        })
    server = subprocess.Popen(
        [str(ROOT / ".venv/bin/python"), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=BACKEND,
        env=server_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    report = {
        "sample_id": SAMPLE_ID,
        "sample_revision": "native-tools-finish-response-interim-audit-v1",
        "instrumentation": {
            "runtime_events_safe_projection": not DISABLE_TESTSITE,
            "test_sitecustomize_enabled": not DISABLE_TESTSITE,
            "node_message_shape": not DISABLE_TESTSITE and os.environ.get("PI_CAPTURE_NODE_SHAPE") == "1",
            "wire_fetch_mode": os.environ.get("PI_FETCH_MODE", "disabled") if not DISABLE_TESTSITE and os.environ.get("PI_CAPTURE_NODE_SHAPE") == "1" else "disabled",
            "wire_override_scope": "tool_choice required to auto only for requests with tools; no response_format or other fields changed" if not DISABLE_TESTSITE and os.environ.get("PI_FETCH_MODE") == "auto" else None,
            "production_worker_modified": False,
        },
        "provider": {
            "configured": True,
            "model_id": provider["LLM_MODEL"],
            "base_hostname": urlsplit(provider["OPENAI_BASE_URL"]).hostname,
            "api_key_value_recorded": False,
        },
        "route": {},
        "request": {"sha256": hashlib.sha256(REQUEST_TEXT.encode()).hexdigest(), "length": len(REQUEST_TEXT)},
        "source_sha256": source_hashes(),
        "observed": {},
        "export": None,
        "raw_sse_ignored_path": str(raw_sse),
        "safe_runtime_diagnostics_path": str(TMP / "runtime-event-diagnostics.json") if not DISABLE_TESTSITE else None,
        "safe_fetch_diagnostics_path": str(TMP / "fetch-instrumentation.json") if not DISABLE_TESTSITE and os.environ.get("PI_CAPTURE_NODE_SHAPE") == "1" else None,
        "owner_id_or_provider_key_recorded": False,
        "result": "running",
    }
    stage = "service_startup"
    try:
        health = wait_health(server)
        report["isolated_service"] = {"health": health["status"], "business_data_mode": health["business_data_mode"], "configured_for_live_provider": health["llm_configured"]}
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        stage = "guide_session_setup"
        bootstrap = json_request(opener, "GET", "/api/v1/bootstrap")
        created = json_request(opener, "POST", "/api/v1/guide/sessions", {
            "entry_context": {
                "page": "home",
                "store_id": bootstrap["store_id"],
                "delivery_zone_id": bootstrap["delivery_zone_id"],
            }
        })
        session_id = created["session_id"]
        opening = json_request(opener, "POST", f"/api/v1/navigation/sessions/{session_id}/opening", {"role": "keke"})
        route = json_request(opener, "POST", f"/api/v1/navigation/sessions/{session_id}/routes", {
            "request_id": REQUEST_ID,
            "opening_id": opening["opening_id"],
            "role": "keke",
            "message": REQUEST_TEXT,
        })
        report["route"] = {"status": route["status"], "manual_role_choice_used": route["status"] == "unavailable"}
        if route["status"] == "unavailable":
            json_request(opener, "POST", f"/api/v1/navigation/sessions/{session_id}/switches", {
                "opening_id": opening["opening_id"],
                "target_role": "keke",
                "accept": True,
                "routing_request_id": REQUEST_ID,
            })
        elif route["status"] == "switch":
            json_request(opener, "POST", f"/api/v1/navigation/sessions/{session_id}/prompt-displayed", {
                "opening_id": opening["opening_id"], "routing_request_id": REQUEST_ID,
            })
            json_request(opener, "POST", f"/api/v1/navigation/sessions/{session_id}/switches", {
                "opening_id": opening["opening_id"], "target_role": "keke", "accept": True,
                "routing_request_id": REQUEST_ID,
            })
        elif route["status"] != "ready":
            raise RuntimeError(f"Role route did not permit a Keke turn: {route['status']}")

        turn_body = {
            "request_id": REQUEST_ID,
            "routing_request_id": REQUEST_ID,
            "message": REQUEST_TEXT,
            "expected_task_id": created.get("task_id"),
            "expected_state_version": created.get("state_version", 0),
            "expected_session_version": created.get("session_version", 0),
            "view_context": {"page": "home"},
        }
        request = urllib.request.Request(
            BASE_URL + f"/api/v1/guide/sessions/{session_id}/turns/stream",
            data=json.dumps(turn_body, ensure_ascii=False).encode(),
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        )
        stage = "guide_turn"
        frames = []
        with raw_sse.open("w") as capture:
            with opener.open(request, timeout=100) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data: "):
                        continue
                    frame = json.loads(line[6:])
                    frames.append(frame)
                    capture.write(json.dumps(frame, ensure_ascii=False) + "\n")
        type_counts = Counter(frame["type"] for frame in frames)
        interim_frames = [frame for frame in frames if frame["type"] == "message.interim"]
        completion = next((frame for frame in reversed(frames) if frame["type"] == "turn.completed"), None)
        error = next((frame for frame in reversed(frames) if frame["type"] == "error"), None)
        runtime_events = (completion or {}).get("payload", {}).get("runtime_events", [])
        usage_rows = [event for event in runtime_events if event.get("type") == "model_usage"]
        interim_candidates = [event for event in runtime_events if event.get("type") == "interim_candidate"]
        candidate_status_counts = Counter(event.get("status", "missing") for event in interim_candidates)
        completion_payload = (completion or {}).get("payload", {})
        report["observed"] = {
            "sse_frame_count": len(frames),
            "event_type_counts": dict(type_counts),
            "terminal_event": completion["type"] if completion else error["type"] if error else (frames[-1]["type"] if frames else None),
            "runtime_status": (completion or {}).get("payload", {}).get("runtime_status"),
            "answer_kind": completion_payload.get("answer_kind"),
            "answer_status": completion_payload.get("answer_status"),
            "finish_response_tool_calls": sum(
                event.get("type") == "tool_execution_start"
                and (event.get("toolName") == "finish_response" or event.get("tool_name") == "finish_response")
                for event in runtime_events
            ),
            "product_card_count": len(completion_payload.get("product_cards") or []),
            "dish_candidate_count": len(completion_payload.get("dish_candidates") or []),
            "final_message_count": len(completion_payload.get("messages") or []),
            "interims_precede_terminal": bool(completion and all(frame.get("sequence", 0) < completion.get("sequence", 0) for frame in interim_frames)),
            "interim_opportunities": len(interim_candidates),
            "interim_candidate_status_counts": dict(candidate_status_counts),
            "interim_candidates": [
                {
                    "status": event.get("status"),
                    "text_characters": event.get("text_characters"),
                    "tool_call_count": event.get("tool_call_count"),
                }
                for event in interim_candidates
            ],
            "interim_published_count": len(interim_frames),
            "answer_delta_characters": sum(
                len(frame.get("payload", {}).get("delta", ""))
                for frame in frames if frame.get("type") == "answer.delta"
            ),
            "interim_records": [
                {
                    "message_id": frame["payload"].get("message_id"),
                    "content_length": len(frame["payload"].get("content", "")),
                    "content_sha256": hashlib.sha256(frame["payload"].get("content", "").encode()).hexdigest(),
                    "host_recorded_at_ms": frame.get("recorded_at_ms"),
                    "host_elapsed_ms": frame.get("elapsed_ms"),
                    "browser_display_time_ms": None,
                }
                for frame in interim_frames
            ],
            "model_usage": [
                {key: event.get(key) for key in ("kind", "model", "provider_host", "duration_ms", "usage", "cost")}
                for event in usage_rows
            ],
            "usage_fields_valid": all(
                event.get("model") == provider["LLM_MODEL"]
                and event.get("provider_host") == urlsplit(provider["OPENAI_BASE_URL"]).hostname
                and (event.get("duration_ms") is None or event["duration_ms"] >= 0)
                and (event.get("usage") is None or event["usage"].get("totalTokens", 0) > 0)
                for event in usage_rows
            ) if usage_rows else False,
            "append_event_host_times_valid": all(
                isinstance(frame.get("recorded_at_ms"), (int, float))
                and (frame.get("elapsed_ms") is None or (
                    isinstance(frame["elapsed_ms"], (int, float)) and frame["elapsed_ms"] >= 0
                ))
                for frame in frames
            ),
            "interim_display_clock_claimed": False,
            "error_code": error.get("payload", {}).get("code") if error else None,
        }
        report["sse_has_terminal_completion"] = completion is not None
        report["export"] = None
        # The capture/export smoke uses the current isolated database and keeps
        # the raw owner identifier in process memory only.
        os.environ.update(env)
        import sys
        sys.path.insert(0, str(BACKEND))
        from sqlalchemy import select
        from app.core.database import SessionLocal
        from app.evaluation.export_runs import export_runs
        from app.models.guide import GuideSession

        with SessionLocal() as db:
            owner_id = db.scalar(select(GuideSession.owner_id).where(GuideSession.session_id == session_id))
        stage = "export_runs"
        captures = ROOT / f"data/generated/evals/pi-real-provider-{SAMPLE_ID}-capture-2026-10-07.jsonl"
        export_summary = export_runs(owner_id, captures)
        lines = [json.loads(line) for line in captures.read_text().splitlines() if line.strip()]
        report["export"] = {
            "schema_version": export_summary["schema_version"],
            "record_count": export_summary["records"],
            "has_observed_usage_field": bool(lines and "observed_usage" in lines[-1]),
            "has_retrieval_field": bool(lines and "retrieval" in lines[-1]),
            "labels_still_null_before_annotation": bool(lines and lines[-1]["labels"] is None),
            "has_source_snapshot": bool(lines and lines[-1]["export_source_snapshot"]),
            "run_started_at_ms_present": bool(lines and isinstance(lines[-1].get("run_started_at_ms"), (int, float))),
            "event_timestamps_are_separate_fields": bool(lines and all(
                "recorded_at_ms" in event and "elapsed_ms" in event
                for event in lines[-1].get("events", [])
            )),
            "raw_capture_path": str(captures),
        }
        report["result"] = "completed" if completion is not None else "failed"
    except Exception as error:
        report["result"] = "failed"
        report["failure_class"] = type(error).__name__
        report["failure_stage"] = stage
        report["failure_fingerprint"] = hashlib.sha256(str(error).encode()).hexdigest()
        if isinstance(error, urllib.error.HTTPError):
            report["failure_http_status"] = error.code
        message = str(error)
        if "isolated uvicorn exited" in message:
            report["server_exit_code"] = server.poll()
        if server.poll() is not None and server.stderr is not None:
            diagnostic = server.stderr.read().decode("utf-8", errors="replace")[-8192:]
            report["server_stderr_fingerprint"] = hashlib.sha256(diagnostic.encode()).hexdigest()
            exception_types = re.findall(r"\b([A-Za-z][A-Za-z0-9_]*(?:Error|Exception))\b", diagnostic)
            report["server_stderr_exception_types"] = exception_types[-3:]
    finally:
        server.terminate()
        try:
            server.wait(timeout=25)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)

    runtime_diagnostics = TMP / "runtime-event-diagnostics.json"
    if runtime_diagnostics.exists():
        report["runtime_events_diagnostic"] = json.loads(runtime_diagnostics.read_text())
    rejected_candidates = TMP / "rejected-audit-candidates.jsonl"
    if rejected_candidates.exists():
        lines = [line for line in rejected_candidates.read_text().splitlines() if line.strip()]
        report["rejected_interim_capture"] = {
            "candidate_count": len(lines),
            "candidate_text_only": all(
                isinstance((record := json.loads(line)).get("candidate"), str)
                and set(record) == {"candidate"}
                for line in lines
            ),
            "sha256": hashlib.sha256(rejected_candidates.read_bytes()).hexdigest(),
            "path": str(rejected_candidates),
        }
    fetch_diagnostics = TMP / "fetch-instrumentation.json"
    if fetch_diagnostics.exists():
        report["fetch_wire_instrumentation"] = json.loads(fetch_diagnostics.read_text())

    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    summary = {
        "provider": report["provider"],
        "route": report["route"],
        "observed": report["observed"],
        "export": report["export"],
        "instrumentation": report["instrumentation"],
        "runtime_events_diagnostic": report.get("runtime_events_diagnostic"),
        "fetch_wire_instrumentation": report.get("fetch_wire_instrumentation"),
        "failure_stage": report.get("failure_stage"),
        "failure_class": report.get("failure_class"),
        "server_exit_code": report.get("server_exit_code"),
        "server_stderr_exception_types": report.get("server_stderr_exception_types"),
        "report_path": str(output),
        "raw_sse_path": str(raw_sse),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if report["result"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

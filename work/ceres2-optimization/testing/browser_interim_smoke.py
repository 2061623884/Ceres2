"""Observe one live Keke interim in native Firefox before the final SSE event."""

from __future__ import annotations

import hashlib
import http.client
import http.server
import json
import os
import queue
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
TESTING = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTING))

import browser_demo_journey as browser  # noqa: E402
from pi_real_provider_smoke import approved_provider_config, source_hashes  # noqa: E402


SAMPLE_ID = os.environ.get("BROWSER_INTERIM_SAMPLE_ID", "streaming-v3")
TMP = TESTING / "tmp" / "browser-interim" / SAMPLE_ID
DB = TMP / "business.sqlite3"
CHECKPOINT = TMP / "checkpoint.sqlite3"
BACKEND_PORT = 18036
FRONTEND_PORT = 18445
GECKO_PORT = 4445
BASE_URL = f"http://127.0.0.1:{FRONTEND_PORT}"
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
REQUEST_TEXT = "我想做番茄炒蛋，请查两人份基准用量和鸡蛋当前规格、模拟价格；先告诉我你准备核对什么，再继续查，不要加购。"
REQUEST_ID = "firefox-native-interim-20261007"

browser.BACKEND_PORT = BACKEND_PORT
browser.FRONTEND_PORT = FRONTEND_PORT
browser.GECKO_PORT = GECKO_PORT
browser.BASE_URL = BASE_URL
browser.BACKEND_URL = BACKEND_URL


class StreamingProxyHandler(browser.ProxyHandler):
    """Keep public SSE incremental while serving the built frontend."""

    protocol_version = "HTTP/1.1"

    def _proxy(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path.endswith("/turns/stream"):
            self.server.stream_started_at = time.monotonic()
            self.server.schedule_thread_dump()
        body = self.rfile.read(int(self.headers.get("Content-Length", "0"))) if self.command in {"POST", "PUT", "PATCH"} else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "connection", "content-length", "accept-encoding"}
        }
        connection = http.client.HTTPConnection("127.0.0.1", BACKEND_PORT, timeout=120)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            status = response.status
            response_headers = response.getheaders()
            is_stream = "text/event-stream" in response.getheader("Content-Type", "")
            self.server.api_calls.append({"method": self.command, "path": parsed.path, "status": status})
            self.send_response(status)
            for key, value in response_headers:
                lower = key.lower()
                if lower in {"connection", "transfer-encoding", "content-encoding", "content-length"}:
                    continue
                self.send_header(key, value)
            if is_stream:
                self.send_header("Transfer-Encoding", "chunked")
                self.send_header("Connection", "close")
                self.end_headers()
                pending = b""

                def write_chunk(data: bytes) -> bool:
                    try:
                        self.wfile.write(f"{len(data):X}\r\n".encode("ascii") + data + b"\r\n")
                        self.wfile.flush()
                        return True
                    except (BrokenPipeError, ConnectionResetError):
                        return False

                def observe_frame(frame_bytes: bytes) -> None:
                    lines = frame_bytes.decode("utf-8", errors="replace").splitlines()
                    data_lines = [line[6:] for line in lines if line.startswith("data: ")]
                    if not data_lines:
                        return
                    try:
                        frame = json.loads("\n".join(data_lines))
                    except json.JSONDecodeError:
                        return
                    observed: dict[str, Any] = {"type": frame.get("type"), "sequence": frame.get("sequence")}
                    if frame.get("type") == "message.interim":
                        content = frame.get("payload", {}).get("content", "")
                        observed.update({
                            "message_id": frame.get("payload", {}).get("message_id"),
                            "content_characters": len(content),
                            "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
                            "recorded_at_ms": frame.get("recorded_at_ms"),
                            "elapsed_ms": frame.get("elapsed_ms"),
                        })
                    if frame.get("type") == "turn.completed":
                        payload = frame.get("payload", {})
                        runtime_events = payload.get("runtime_events", [])
                        observed.update({
                            "runtime_status": payload.get("runtime_status"),
                            "answer_status": payload.get("answer_status"),
                            "finish_response_calls": sum(
                                event.get("type") == "tool_execution_start"
                                and event.get("toolName") == "finish_response"
                                for event in runtime_events
                            ),
                            "candidate_statuses": [
                                event.get("status") for event in runtime_events
                                if event.get("type") == "interim_candidate"
                            ],
                        })
                    self.server.sse_events.append(observed)
                    if frame.get("type") == "message.interim":
                        self.server.interim_notice_queue.put(observed)
                        try:
                            self.server.interim_release_queue.get(timeout=8)
                        except queue.Empty:
                            self.server.interim_gate_timeouts += 1

                while True:
                    chunk = response.read1(4096)
                    if not chunk:
                        break
                    pending += chunk
                    while True:
                        lf_end = pending.find(b"\n\n")
                        crlf_end = pending.find(b"\r\n\r\n")
                        options = [(index, size) for index, size in ((lf_end, 2), (crlf_end, 4)) if index >= 0]
                        if not options:
                            break
                        end, separator_size = min(options, key=lambda item: item[0])
                        frame_bytes = pending[:end + separator_size]
                        pending = pending[end + separator_size:]
                        if not write_chunk(frame_bytes):
                            pending = b""
                            break
                        observe_frame(frame_bytes)
                try:
                    if pending:
                        write_chunk(pending)
                    self.wfile.write(b"0\r\n\r\n")
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                data = response.read()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(data)
        finally:
            connection.close()


def wait_health(process: subprocess.Popen, timeout: float = 25) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"isolated uvicorn exited with status {process.returncode}")
        try:
            with urllib.request.urlopen(BACKEND_URL + "/health", timeout=2) as response:
                return json.loads(response.read())
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    raise RuntimeError("isolated browser backend did not become ready")


def assistant_bubble_snapshot(driver: browser.WebDriver) -> dict[str, Any]:
    result = driver.script(r"""
      const list = document.querySelector('.space-y-5.overflow-y-auto');
      if (!list) return null;
      const rows = [...list.children];
      const assistantRows = rows.filter(row => !row.classList.contains('flex-row-reverse'));
      const bubbles = assistantRows.map(row => [...row.querySelectorAll('div')].find(element => {
        const style = getComputedStyle(element);
        return element.classList.contains('px-4') && element.classList.contains('py-3') &&
          style.backgroundColor === 'rgb(242, 241, 237)' && element.innerText.trim();
      })).filter(Boolean);
      const viewport = list.getBoundingClientRect();
      const windowRect = {left:0, top:0, right:window.innerWidth, bottom:window.innerHeight};
      const intersect = (rect, clip) => {
        const left = Math.max(rect.left, clip.left);
        const top = Math.max(rect.top, clip.top);
        const right = Math.min(rect.right, clip.right);
        const bottom = Math.min(rect.bottom, clip.bottom);
        return {left, top, right, bottom, width:Math.max(0,right-left), height:Math.max(0,bottom-top)};
      };
      const bubbleMetrics = bubbles.map(element => {
        const rect = element.getBoundingClientRect();
        const visibleRect = intersect(intersect(rect, viewport), windowRect);
        const style = getComputedStyle(element);
        const visibleArea = visibleRect.width * visibleRect.height;
        const area = Math.max(1, rect.width * rect.height);
        const visible = style.display !== 'none' && style.visibility !== 'hidden' &&
          Number(style.opacity || 1) > 0.05 && visibleArea >= 800 && visibleArea / area >= 0.1;
        return {
          characters: element.innerText.length,
          visible,
          opacity: Number(style.opacity || 1),
          visible_area_pixels: Math.round(visibleArea),
          visible_fraction: Math.round((visibleArea / area) * 1000) / 1000,
          rect: {left:Math.round(rect.left), top:Math.round(rect.top), right:Math.round(rect.right), bottom:Math.round(rect.bottom)},
          visible_rect: {left:Math.round(visibleRect.left), top:Math.round(visibleRect.top), right:Math.round(visibleRect.right), bottom:Math.round(visibleRect.bottom)},
        };
      });
      return {
        assistant_text_bubble_count: bubbles.length,
        assistant_bubble_character_counts: bubbles.map(element => element.innerText.length),
        assistant_visible_text_bubble_count: bubbleMetrics.filter(item => item.visible).length,
        assistant_bubble_visibility: bubbleMetrics,
        chat_scroll_viewport: {
          left:Math.round(viewport.left), top:Math.round(viewport.top),
          right:Math.round(viewport.right), bottom:Math.round(viewport.bottom),
          scroll_top:list.scrollTop, scroll_height:list.scrollHeight, client_height:list.clientHeight,
          at_bottom:list.scrollHeight - list.scrollTop - list.clientHeight < 4,
        },
        loading_bubble_count: document.querySelectorAll('[aria-label="可可正在输入"]').length,
        progress_indicator_visible: [...document.querySelectorAll('[data-guide-action-line]')]
          .some(element => (element.innerText || '').trim().length > 0),
        input_count: document.querySelectorAll('input[placeholder="问问可可吧…"]').length,
      };
    """)
    return result or {"assistant_text_bubble_count": 0, "assistant_bubble_character_counts": [], "assistant_visible_text_bubble_count": 0, "assistant_bubble_visibility": [], "loading_bubble_count": 0, "progress_indicator_visible": False, "input_count": 0}


def browser_ui_diagnostics(driver: browser.WebDriver) -> dict[str, Any]:
    """Capture visible control state without collecting chat message bodies."""
    result = driver.script(r"""
      const text = selector => [...document.querySelectorAll(selector)]
        .map(element => (element.innerText || '').trim()).filter(Boolean).slice(0, 12);
      return {
        title: document.title,
        body_visible: !!document.body,
        alerts: text('[role="alert"]'),
        statuses: text('[role="status"]'),
        buttons: [...document.querySelectorAll('button')].slice(0, 40).map(button => ({
          label: (button.innerText || '').trim().slice(0, 60), disabled: button.disabled,
          pressed: button.getAttribute('aria-pressed'),
        })),
        inputs: [...document.querySelectorAll('input')].map(input => ({
          type: input.type, placeholder: input.placeholder, disabled: input.disabled,
          value_characters: input.value.length,
        })),
        role_navigation_count: document.querySelectorAll('[aria-label="角色导航"]').length,
        assistant_bubble_state: (() => {
          const list = document.querySelector('.space-y-5.overflow-y-auto');
          return list ? {row_count: list.children.length} : null;
        })(),
      };
    """)
    return result if isinstance(result, dict) else {"diagnostics_unavailable": True}


def api_call_summary(calls: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for call in calls:
        path = call.get("path", "")
        label = path
        label = re.sub(r"(?<=/sessions/)[^/]+", "{session_id}", label)
        label = re.sub(r"(?<=/runs/)[^/]+", "{run_id}", label)
        key = f"{call.get('method')} {label} {call.get('status')}"
        summary[key] = summary.get(key, 0) + 1
    return summary


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    profile_root = TMP / "firefox-profile-root"
    profile_root.mkdir(exist_ok=True)
    provider = approved_provider_config()
    thread_dump = TMP / "backend-thread-dump.txt"
    env = {key: os.environ[key] for key in ("PATH", "HOME", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy", "NODE_EXTRA_CA_CERTS") if key in os.environ}
    env.update(provider)
    env.update({
        "DATABASE_URL": f"sqlite:///{DB}",
        "MERCURY_CHECKPOINT_PATH": str(CHECKPOINT),
        "LLM_MODE": "live",
        "MEMORY_EXTRACTION_MODEL": "",
        "MEMORY_DREAM_MODEL": "",
        "BROWSER_THREAD_DUMP_PATH": str(thread_dump),
        "BROWSER_BACKEND_PORT": str(BACKEND_PORT),
    })
    seed = subprocess.run(
        [str(ROOT / ".venv/bin/python"), "-m", "app.services.seed_service"],
        cwd=BACKEND,
        env=dict(env, LLM_MODE="demo"),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if seed.returncode != 0:
        raise RuntimeError(f"isolated fixture import failed with exit {seed.returncode}")

    backend = subprocess.Popen(
        [str(ROOT / ".venv/bin/python"), str(TESTING / "browser_faulthandler_server.py")],
        cwd=BACKEND,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proxy = http.server.ThreadingHTTPServer(("127.0.0.1", FRONTEND_PORT), StreamingProxyHandler)
    proxy.api_calls = []
    proxy.sse_events = []
    proxy.interim_notice_queue = queue.Queue()
    proxy.interim_release_queue = queue.Queue()
    proxy.interim_gate_timeouts = 0
    proxy.backend_pid = backend.pid
    proxy.stream_started_at = None
    proxy.dump_timer = None

    def schedule_thread_dump() -> None:
        if proxy.dump_timer is not None:
            return
        def dump() -> None:
            try:
                backend.send_signal(signal.SIGUSR1)
            except (OSError, ProcessLookupError):
                pass
        proxy.dump_timer = threading.Timer(30, dump)
        proxy.dump_timer.daemon = True
        proxy.dump_timer.start()

    proxy.schedule_thread_dump = schedule_thread_dump
    proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    proxy_thread.start()
    gecko = subprocess.Popen(
        [str(browser.GECKODRIVER), "--host", "127.0.0.1", "--port", str(GECKO_PORT), "--profile-root", str(profile_root), "--binary", "/usr/bin/firefox", "--log", "error"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    driver: browser.WebDriver | None = None
    report: dict[str, Any] = {
        "browser": "Firefox 136.0 headless through Mozilla geckodriver 0.37.1",
        "provider": {"model_id": provider["LLM_MODEL"], "base_hostname": urlsplit(provider["OPENAI_BASE_URL"]).hostname, "api_key_recorded": False},
        "source_sha256": source_hashes() | {
            relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            for relative in (
                "frontend/src/App.tsx",
                "frontend/src/lib/saleGuide.ts",
                "frontend/dist/index.html",
            )
        },
        "frontend_dist_asset_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / "frontend/dist/assets").glob("*"))
            if path.is_file()
        },
        "production_worker_modified": False,
        "test_preload_or_sitecustomize": False,
        "sse_observation": "Tester proxy forwards complete event frames and pauses after each message.interim until Firefox DOM bubble-count delta is sampled; event payloads are unchanged.",
        "steps": [],
        "manual_role_fallback_used": False,
        "outcome": {},
        "result": "running",
    }
    stage = "service_startup"
    try:
        health = wait_health(backend)
        report["service"] = {"health": health["status"], "business_data_mode": health["business_data_mode"], "configured_for_live_provider": health["llm_configured"], "database": str(DB)}
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{GECKO_PORT}/status", timeout=1) as response:
                    if response.status == 200:
                        break
            except (OSError, urllib.error.URLError):
                time.sleep(0.25)
        else:
            raise RuntimeError("geckodriver did not become ready")

        stage = "firefox_startup"
        created = browser.WebDriver.request("POST", "/session", {
            "capabilities": {"alwaysMatch": {
                "browserName": "firefox",
                "moz:firefoxOptions": {"binary": "/usr/bin/firefox", "args": ["-headless"]},
            }},
        }, timeout=60)
        driver = browser.WebDriver(created["value"]["sessionId"])
        driver.command("POST", "/window/rect", {"width": 1440, "height": 1000, "x": 0, "y": 0})
        driver.command("POST", "/url", {"url": BASE_URL})
        browser.wait_text(driver, "Ceres的朋友")
        report["steps"].append("opened the built Grok-style Ceres UI in native Firefox")

        stage = "open_keke"
        browser.click_button(driver, "商品")
        browser.wait_until(driver, "return !!document.querySelector('input[placeholder=\"搜索有机食材与好物\"]')", "catalog view", 20)
        browser.click_button(driver, "问问可可")
        browser.wait_until(driver, "const i=document.querySelector('input[placeholder=\"问问可可吧…\"]');return !!i && !i.disabled", "ready Keke chat input and session", 30)
        report["steps"].append("opened Keke and waited for its public message input")

        stage = "send_and_manual_role_fallback"
        input_id = driver.element("css selector", 'input[placeholder="问问可可吧…"]')
        driver.send_keys(input_id, REQUEST_TEXT)
        send_button_element = driver.script("return arguments[0].parentElement.querySelector('button')", [{browser.ELEMENT_KEY: input_id}])
        send_button = send_button_element.get(browser.ELEMENT_KEY) if isinstance(send_button_element, dict) else None
        if not send_button:
            raise RuntimeError("Keke send button was not found")
        baseline = assistant_bubble_snapshot(driver)
        sent_at = time.monotonic()
        driver.click(send_button)
        browser.wait_text(driver, "职责判断暂时不可用", 20)
        role_button = driver.element("xpath", "//div[@aria-label='角色导航']//button[normalize-space(.)='可可 · 选购']")
        driver.click(role_button)
        browser.wait_until(driver, "const b=document.querySelector('[aria-label=\"角色导航\"] button[aria-pressed]');return !!b && !b.disabled", "manual Keke role selection after route fallback", 20)
        report["manual_role_fallback_used"] = True
        report["steps"].append("routed once, used the visible manual-role fallback, and resumed the same request")

        stage = "observe_live_sse_and_dom"
        interim_snapshot = None
        interim_dom_records: list[dict[str, Any]] = []
        last_bubble_count = baseline["assistant_text_bubble_count"]
        last_visible_count = baseline["assistant_visible_text_bubble_count"]
        terminal_seen = False
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            snapshot = assistant_bubble_snapshot(driver)
            try:
                interim_notice = proxy.interim_notice_queue.get_nowait()
            except queue.Empty:
                interim_notice = None
            if interim_notice is not None:
                capture_deadline = time.monotonic() + 5
                sampled_snapshot = None
                while time.monotonic() < capture_deadline:
                    snapshot = assistant_bubble_snapshot(driver)
                    busy_visible = snapshot["loading_bubble_count"] > 0 or snapshot["progress_indicator_visible"]
                    if snapshot["assistant_text_bubble_count"] > last_bubble_count and busy_visible:
                        sampled_snapshot = snapshot
                        break
                    time.sleep(0.05)
                if sampled_snapshot is not None:
                    delta = sampled_snapshot["assistant_text_bubble_count"] - last_bubble_count
                    visible_snapshot = sampled_snapshot
                    visible_deadline = time.monotonic() + 2
                    while time.monotonic() < visible_deadline:
                        visible_snapshot = assistant_bubble_snapshot(driver)
                        if (
                            visible_snapshot["assistant_visible_text_bubble_count"] > last_visible_count
                            and (visible_snapshot["loading_bubble_count"] > 0 or visible_snapshot["progress_indicator_visible"])
                        ):
                            break
                        time.sleep(0.05)
                    visible_delta = visible_snapshot["assistant_visible_text_bubble_count"] - last_visible_count
                    preterminal_screenshot = TMP / f"interim-{len(interim_dom_records) + 1}-before-terminal.png"
                    driver.screenshot(preterminal_screenshot)
                    interim_dom_records.append({
                        "message_id": interim_notice.get("message_id"),
                        "sequence": interim_notice.get("sequence"),
                        "bubbles_before": last_bubble_count,
                        "bubbles_after": sampled_snapshot["assistant_text_bubble_count"],
                        "bubble_delta": delta,
                        "one_bubble_for_event": delta == 1,
                        "visible_bubbles_before": last_visible_count,
                        "visible_bubbles_after": visible_snapshot["assistant_visible_text_bubble_count"],
                        "visible_bubble_delta": visible_delta,
                        "one_visible_bubble_for_event": visible_delta == 1,
                        "interim_bubble_visibility": visible_snapshot["assistant_bubble_visibility"][-1:],
                        "chat_scroll_viewport": visible_snapshot.get("chat_scroll_viewport"),
                        "preterminal_screenshot_ignored_path": str(preterminal_screenshot),
                        "loading_or_progress_visible": bool(
                            visible_snapshot["loading_bubble_count"] > 0
                            or visible_snapshot["progress_indicator_visible"]
                        ),
                    })
                    last_bubble_count = sampled_snapshot["assistant_text_bubble_count"]
                    last_visible_count = visible_snapshot["assistant_visible_text_bubble_count"]
                    if interim_snapshot is None:
                        interim_snapshot = visible_snapshot
                else:
                    preterminal_screenshot = TMP / f"interim-{len(interim_dom_records) + 1}-before-terminal.png"
                    driver.screenshot(preterminal_screenshot)
                    interim_dom_records.append({
                        "message_id": interim_notice.get("message_id"),
                        "sequence": interim_notice.get("sequence"),
                        "bubbles_before": last_bubble_count,
                        "bubbles_after": snapshot["assistant_text_bubble_count"],
                        "bubble_delta": snapshot["assistant_text_bubble_count"] - last_bubble_count,
                        "one_bubble_for_event": False,
                        "visible_bubbles_before": last_visible_count,
                        "visible_bubbles_after": snapshot["assistant_visible_text_bubble_count"],
                        "visible_bubble_delta": snapshot["assistant_visible_text_bubble_count"] - last_visible_count,
                        "one_visible_bubble_for_event": False,
                        "preterminal_screenshot_ignored_path": str(preterminal_screenshot),
                        "loading_or_progress_visible": False,
                    })
                proxy.interim_release_queue.put(True)
            terminal_seen = any(event["type"] in {"turn.completed", "error"} for event in proxy.sse_events)
            if terminal_seen and snapshot["loading_bubble_count"] == 0:
                break
            if proxy.stream_started_at is not None and time.monotonic() - proxy.stream_started_at >= 38:
                break
            time.sleep(0.1)

        interim_event = next((event for event in proxy.sse_events if event["type"] == "message.interim"), None)
        interim_events = [event for event in proxy.sse_events if event["type"] == "message.interim"]
        interim_message_ids = [event.get("message_id") for event in interim_events]
        terminal_event = next((event for event in reversed(proxy.sse_events) if event["type"] in {"turn.completed", "error"}), None)
        time.sleep(1.0)
        settled_snapshot = assistant_bubble_snapshot(driver)
        result_intro_calls = [
            call for call in proxy.api_calls
            if call.get("path", "").endswith("/result-introductions")
        ]
        final_screenshot = TMP / "browser-interim-terminal-settled.png"
        if terminal_event is not None:
            driver.screenshot(final_screenshot)
        if interim_event and terminal_event:
            report["outcome"] = {
                "terminal_type": terminal_event["type"],
                "terminal_sequence": terminal_event.get("sequence"),
                "interim_sequence": interim_event.get("sequence"),
                "interim_preceded_terminal": interim_event.get("sequence", 0) < terminal_event.get("sequence", 0),
                "interim_recorded_at_ms": interim_event.get("recorded_at_ms"),
                "interim_elapsed_ms": interim_event.get("elapsed_ms"),
                "interim_content_characters": interim_event.get("content_characters"),
                "interim_content_sha256": interim_event.get("content_sha256"),
                "interim_message_ids": interim_message_ids,
                "interim_message_ids_unique": len(interim_message_ids) == len(set(interim_message_ids)),
                "interim_dom_bubble_records": interim_dom_records,
                "one_bubble_per_interim_event": (
                    len(interim_dom_records) == len(interim_events)
                    and all(record["one_bubble_for_event"] for record in interim_dom_records)
                ),
                "one_visible_bubble_per_interim_event": (
                    len(interim_dom_records) == len(interim_events)
                    and all(record.get("one_visible_bubble_for_event") for record in interim_dom_records)
                ),
                "interim_gate_timeouts": proxy.interim_gate_timeouts,
                "dom_exposes_message_id": False,
                "ui_bubbles_before_terminal": interim_snapshot,
                "ui_bubbles_after_terminal_settled": settled_snapshot,
                "final_screenshot_ignored_path": str(final_screenshot) if terminal_event else None,
                "result_introduction_api_calls": result_intro_calls,
                "fact_only_result_introduction_absent": not result_intro_calls,
                "dom_observed_ms_after_send": round((time.monotonic() - sent_at) * 1000, 1) if interim_snapshot else None,
                "sse_sequence_types": proxy.sse_events,
            }
            report["result"] = "passed" if (
                interim_snapshot
                and interim_snapshot["assistant_text_bubble_count"] > baseline["assistant_text_bubble_count"]
                and (interim_snapshot["loading_bubble_count"] > 0 or interim_snapshot["progress_indicator_visible"])
                and interim_event["sequence"] < terminal_event["sequence"]
                and len(interim_dom_records) == len(interim_events)
                and all(record["one_bubble_for_event"] for record in interim_dom_records)
                and all(record.get("one_visible_bubble_for_event") for record in interim_dom_records)
                and len(interim_message_ids) == len(set(interim_message_ids))
                and proxy.interim_gate_timeouts == 0
            ) else "failed"
        else:
            report["outcome"] = {
                "terminal_type": terminal_event["type"] if terminal_event else None,
                "interim_event_seen": interim_event is not None,
                "ui_bubbles_at_end": assistant_bubble_snapshot(driver),
                "sse_sequence_types": proxy.sse_events,
            }
            report["result"] = "failed"
        report["outcome"]["backend_thread_dump_captured"] = thread_dump.exists() and thread_dump.stat().st_size > 0
        if thread_dump.exists() and thread_dump.stat().st_size > 0:
            report["outcome"]["backend_thread_dump_sha256"] = hashlib.sha256(thread_dump.read_bytes()).hexdigest()
            process_status = subprocess.run(
                ["ps", "--ppid", str(backend.pid), "-o", "pid,ppid,state,etime,comm"],
                capture_output=True, text=True, check=False,
            )
            report["outcome"]["backend_child_process_status"] = process_status.stdout.strip().splitlines()
        report["steps"].append("observed the browser DOM and public SSE event ordering")
        report["api_call_summary"] = api_call_summary(proxy.api_calls)
        if terminal_event is not None and driver is not None:
            screenshot = TMP / "browser-interim-final.png"
            driver.screenshot(screenshot)
            report["final_screenshot_ignored_path"] = str(screenshot)
    except Exception as error:
        report["result"] = "failed"
        report["failure_stage"] = stage
        report["failure_class"] = type(error).__name__
        report["failure_fingerprint"] = hashlib.sha256(str(error).encode()).hexdigest()
        if driver is not None:
            try:
                report["browser_ui_diagnostics"] = browser_ui_diagnostics(driver)
            except Exception:
                report["browser_ui_diagnostics"] = {"diagnostics_unavailable": True}
        report["api_call_summary"] = api_call_summary(proxy.api_calls)
        report["sse_sequence_types"] = proxy.sse_events
    finally:
        if driver is not None:
            try:
                driver.request("DELETE", f"/session/{driver.session_id}", timeout=10)
            except Exception:
                pass
        proxy.shutdown()
        if proxy.dump_timer is not None:
            proxy.dump_timer.cancel()
        proxy.server_close()
        gecko.terminate()
        try:
            gecko.wait(timeout=10)
        except subprocess.TimeoutExpired:
            gecko.kill()
        backend.terminate()
        try:
            backend.wait(timeout=25)
        except subprocess.TimeoutExpired:
            backend.kill()
            backend.wait(timeout=5)

    output = TESTING / f"browser-interim-smoke-{SAMPLE_ID}-2026-10-07.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["result"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

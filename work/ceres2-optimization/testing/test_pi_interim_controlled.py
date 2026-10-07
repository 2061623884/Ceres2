"""Controlled local-provider checks for Pi interim publication semantics."""

import json
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
import uvicorn

pytest_plugins = ["test_runtime_pi_product_query"]

from test_guide_lifecycle import BASE


CANDIDATE = "我先核对一下当前任务状态，再把结果告诉你。"
TRIGGER = "受控中途消息流程"


def parse_events(response):
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


def event_payloads(events, event_type):
    return [event["payload"] for event in events if event["type"] == event_type]


def install_interim_model(requests, *, approved=True, block_final=None):
    def answer(body):
        messages = body["messages"]
        users = [str(message.get("content", "")) for message in messages if message["role"] == "user"]
        tool_messages = [message for message in messages if message["role"] == "tool"]
        if any(CANDIDATE in text for text in users):
            verdict = {"merchant_claims": not approved, "execution_claims": False}
            return {"role": "assistant", "content": json.dumps(verdict)}, "stop"
        if not tool_messages:
            message_id = "interim-progress-1"
            delta = {
                "role": "assistant",
                "content": json.dumps({"interim_message": CANDIDATE}, ensure_ascii=False),
                "tool_calls": [{
                    "index": 0,
                    "id": message_id,
                    "type": "function",
                    "function": {
                        "name": "guide_request",
                        "arguments": json.dumps({"kind": "progress"}),
                    },
                }],
            }
            return delta, "tool_calls"
        if block_final is not None:
            started, release = block_final
            started.set()
            release.wait(timeout=15)
        return {"role": "assistant", "content": json.dumps({"answer_kind": "status"})}, "stop"

    requests.answer_hook = answer


def start_live_server(app):
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off"))
    thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
    thread.start()
    until = time.monotonic() + 5
    while not server.started and time.monotonic() < until:
        time.sleep(0.01)
    assert server.started
    return sock, port, server, thread


def stop_live_server(sock, server, thread):
    server.should_exit = True
    thread.join(timeout=5)
    sock.close()


def authorize_keke_text(client, request_id, message, monkeypatch):
    from app.services import navigation_service

    monkeypatch.setattr(navigation_service, "judge", lambda _state: ("keke_chat", {"controlled": True}))
    opening = client.post(
        "/api/v1/navigation/sessions/pi-session-a/opening",
        json={"role": "keke"},
    )
    assert opening.status_code == 200, opening.text
    routed = client.post(
        "/api/v1/navigation/sessions/pi-session-a/routes",
        json={
            "request_id": request_id,
            "opening_id": opening.json()["opening_id"],
            "role": "keke",
            "message": message,
        },
    )
    assert routed.status_code == 200 and routed.json()["status"] == "ready", routed.text


def test_approved_interim_is_persisted_before_tool_result_and_final(pi_client, monkeypatch):
    client, requests = pi_client
    install_interim_model(requests)
    authorize_keke_text(client, "interim-positive", TRIGGER, monkeypatch)
    response = client.post(
        "/api/v1/guide/sessions/pi-session-a/turns/stream",
        json={"request_id": "interim-positive", "message": TRIGGER, "expected_state_version": 0, "expected_session_version": 0},
    )
    assert response.status_code == 200
    events = parse_events(response)
    assert events and events[-1]["type"] == "turn.completed", json.dumps(events, ensure_ascii=False)
    interims = event_payloads(events, "message.interim")
    completed = event_payloads(events, "turn.completed")
    assert len(interims) == 1
    assert interims[0]["content"] == CANDIDATE
    assert events.index(next(event for event in events if event["type"] == "message.interim")) < events.index(next(event for event in events if event["type"] == "turn.completed"))
    assert len(completed) == 1
    audits = [event for event in completed[0]["runtime_events"] if event.get("type") == "interim_audit"]
    assert len(audits) == 1 and audits[0]["approved"] is True
    history = client.get("/api/v1/guide/sessions/pi-session-a/messages").json()["messages"]
    saved = [row for row in history if row.get("kind") == "interim"]
    assert len(saved) == 1 and saved[0]["message_id"] == interims[0]["message_id"]
    assert len(requests) == 3  # main iteration, audit, then main final; no extra message-generation call


def test_claim_bearing_interim_is_rejected_without_public_message(pi_client, monkeypatch):
    client, requests = pi_client
    install_interim_model(requests, approved=False)
    authorize_keke_text(client, "interim-negative", TRIGGER, monkeypatch)
    response = client.post(
        "/api/v1/guide/sessions/pi-session-a/turns/stream",
        json={"request_id": "interim-negative", "message": TRIGGER, "expected_state_version": 0, "expected_session_version": 0},
    )
    events = parse_events(response)
    assert events and events[-1]["type"] == "turn.completed", json.dumps(events, ensure_ascii=False)
    completed = event_payloads(events, "turn.completed")
    assert len(completed) == 1
    audits = [event for event in completed[0]["runtime_events"] if event.get("type") == "interim_audit"]
    assert len(audits) == 1 and audits[0]["approved"] is False
    assert not event_payloads(events, "message.interim")
    history = client.get("/api/v1/guide/sessions/pi-session-a/messages").json()["messages"]
    assert not any(row.get("kind") == "interim" for row in history)
    assert len(requests) == 3


def test_stop_after_published_interim_keeps_one_message_and_no_late_completion(pi_client, monkeypatch):
    client, requests = pi_client
    final_started = threading.Event()
    final_release = threading.Event()
    install_interim_model(requests, block_final=(final_started, final_release))
    body = {"request_id": "interim-stop", "message": TRIGGER, "expected_state_version": 0, "expected_session_version": 0}
    authorize_keke_text(client, body["request_id"], TRIGGER, monkeypatch)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(client.post, "/api/v1/guide/sessions/pi-session-a/turns/stream", json=body)
        assert final_started.wait(timeout=8)
        before_stop = client.get("/api/v1/guide/sessions/pi-session-a/messages").json()["messages"]
        assert sum(row.get("kind") == "interim" for row in before_stop) == 1
        stop = client.post("/api/v1/guide/sessions/pi-session-a/turns/stop", json={"request_id": body["request_id"]})
        assert stop.status_code == 200 and stop.json()["cancelled"] is True
        final_release.set()
        response = future.result(timeout=5)
    events = parse_events(response)
    assert events[-1]["type"] == "turn.stopped", events[-1]
    assert len(event_payloads(events, "message.interim")) == 1
    assert not event_payloads(events, "turn.completed")
    requests.release.set()
    final_release.set()
    final_history = client.get("/api/v1/guide/sessions/pi-session-a/messages").json()["messages"]
    assert sum(row.get("kind") == "interim" for row in final_history) == 1


def test_sse_reconnect_after_interim_does_not_replay_or_duplicate_bubble(pi_client, monkeypatch):
    client, requests = pi_client
    final_started = threading.Event()
    final_release = threading.Event()
    install_interim_model(requests, block_final=(final_started, final_release))
    authorize_keke_text(client, "interim-reconnect", TRIGGER, monkeypatch)
    sock, port, server, thread = start_live_server(client.app)
    request_id = "interim-reconnect"
    initial = []
    accepted = None
    interim = None
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", cookies={"sg_owner_id": "pi-owner-a"}, timeout=20) as live:
            with live.stream(
                "POST",
                BASE + "/turns/stream",
                json={"request_id": request_id, "message": TRIGGER, "expected_state_version": 0, "expected_session_version": 0},
            ) as response:
                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    event = json.loads(line[6:])
                    initial.append(event)
                    if event["type"] == "accepted":
                        accepted = event
                    if event["type"] == "message.interim":
                        interim = event
                        break
            assert accepted is not None and interim is not None, initial
            assert final_started.wait(timeout=5)
            final_release.set()
            replay = live.get(
                BASE + f"/runs/{accepted['run_id']}/stream",
                params={"after_sequence": interim["sequence"]},
            )
            replay_events = [json.loads(line[6:]) for line in replay.text.splitlines() if line.startswith("data: ")]
            assert replay_events[-1]["type"] == "turn.completed", replay_events
            assert all(event["sequence"] > interim["sequence"] for event in replay_events)
            assert not event_payloads(replay_events, "message.interim")
            journal = live.get(BASE + f"/runs/{accepted['run_id']}/events").json()["events"]
            all_interims = [event for event in journal if event["type"] == "message.interim"]
            assert len(all_interims) == 1
            history = live.get(BASE + "/messages").json()["messages"]
            saved = [row for row in history if row.get("kind") == "interim"]
            assert len(saved) == 1 and saved[0]["message_id"] == interim["payload"]["message_id"]
            assert len(requests) == 3
    finally:
        final_release.set()
        requests.release.set()
        stop_live_server(sock, server, thread)

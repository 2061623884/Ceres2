"""Real local HTTP transport disconnect, actual SDK, controlled provider only."""
import json
import socket
import threading
import time
import httpx
import uvicorn
from test_runtime_pi_product_query import pi_client
from test_guide_lifecycle import BASE


def test_connected_sse_disconnect_keeps_bounded_work_and_replays_original_events(pi_client):
    client, requests = pi_client
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(client.app, log_level='error', lifespan='off'))
    thread = threading.Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
    thread.start()
    until = time.monotonic() + 5
    while not server.started and time.monotonic() < until:
        time.sleep(0.01)
    assert server.started
    try:
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', cookies={'sg_owner_id': 'pi-owner-a'}, timeout=20) as live:
            with live.stream('POST', BASE + '/turns/stream', json={'request_id': 'disconnected', 'message': '受控慢查询可乐', 'expected_state_version': 0, 'expected_session_version': 0}) as response:
                first = next(line for line in response.iter_lines() if line.startswith('data: '))
                accepted = json.loads(first[6:])
                assert accepted['type'] == 'accepted'
            # The real response/socket is closed here. The same admitted run
            # must continue, without a second POST or model retry.
            assert requests.started.wait(timeout=5)
            requests.release.set()
            replay = live.get(BASE + f"/runs/{accepted['run_id']}/stream", params={'after_sequence': accepted['sequence']})
            events = [json.loads(line[6:]) for line in replay.text.splitlines() if line.startswith('data: ')]
            assert events[-1]['type'] == 'turn.completed', events
            assert events[0]['sequence'] == accepted['sequence'] + 1
            assert events[-1]['payload']['runtime_status'] == 'completed'
            assert len(requests) == 3
    finally:
        requests.release.set()
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()

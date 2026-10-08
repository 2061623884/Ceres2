# run_baseline per-capture session history RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k test_baseline_cli_filters_public_session_history_to_each_capture_request`
- Result: exit 1; 1 failed, 6 deselected (1.10s).
- Test source SHA-256: `03be48243fdc8b74891d777d381dcd881736ccfbc40978e3e98ad452fa4c7dc9`.
- Runner SHA-256 (`backend/app/evaluation/run_baseline.py`): `55ea887550261999af626b03092ff6c2a15841ea0903dfd94e714c228216ddd8`.
- The loopback fixture returned two real session-history messages with request IDs. First-capture content was correct, but the follow-up capture also contained the initial turn's user message, so it was not limited to messages for its own `request_id`.
- Raw pytest output: [baseline-session-history-filter-red.log](baseline-session-history-filter-red.log), SHA-256 `f976e78c9c9bdaea521f0421ed97c2ecdae1fe5d304d70fb756846043b39196d`.
- The test-owned loopback `ThreadingHTTPServer` was shut down and joined in `finally`; no live service/provider was used.

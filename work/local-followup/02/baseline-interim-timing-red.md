# Baseline client/SSE timing RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k baseline_cli_measures_client_sse_arrival_and_keeps_missing_interim_unknown`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (current uncommitted implementation slice).
- Test source: `backend/tests/test_local_followup_baseline.py`, SHA-256 `d8b21c6d16f9879960bdb70837676f03d4aa8ebdc114c9655567465c03ebe4ab`.
- Implementation: `backend/app/evaluation/run_baseline.py`, SHA-256 `b03e3a51c3814f32ab5d1b9aa538ba12ae19ba1003ab476852b7e314702ed23e`.
- Result: exit 1; `1 failed, 3 deselected` in 1.21s.
- Sole failure: the returned case record lacks `first_interim_ms`; assertion raises `KeyError: 'first_interim_ms'`.
- Fixture loopback server is shut down/closed and joined in `finally`; the test starts no app server or model provider. Inputs/output live under pytest `tmp_path` (`/tmp/pytest-of-amax/pytest-46/test_baseline_cli_measures_cli0`).

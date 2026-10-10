# Baseline public state/Offer GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k baseline_cli_records_public_before_after_state_and_exact_catalog_offers`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (current uncommitted implementation slice).
- Test source: `backend/tests/test_local_followup_baseline.py`, SHA-256 `419999fcfaaf994ddcff40c388414bbd56494d68d0b6a9e3b4cb9a41ba13fb38`.
- Implementation: `backend/app/evaluation/run_baseline.py`, SHA-256 `b03e3a51c3814f32ab5d1b9aa538ba12ae19ba1003ab476852b7e314702ed23e`.
- Result: exit 0; `1 passed, 2 deselected` in 0.89s.
- The test-owned loopback server is shut down/closed and its thread joined in `finally`; test files use pytest `tmp_path`. No live app server or provider was started.

# Baseline public state/Offer RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k baseline_cli_records_public_before_after_state_and_exact_catalog_offers`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (current uncommitted implementation slice).
- Test source: `backend/tests/test_local_followup_baseline.py`, SHA-256 `419999fcfaaf994ddcff40c388414bbd56494d68d0b6a9e3b4cb9a41ba13fb38`.
- Implementation: `backend/app/evaluation/run_baseline.py`, SHA-256 `63d08e80bfd3826f2b992d5ccf558cf5f89f36c73d726df4bd0eed0d478bf5bb`.
- Result: exit 1; `1 failed, 2 deselected` in 1.02s.
- Sole failure: the successful capture record has no `before` field; test raises `KeyError: 'before'` while checking the public before/after snapshot contract.
- Test-owned loopback server is shut down and closed and its thread joined in `finally`. Input/output live under pytest `tmp_path` (`/tmp/pytest-of-amax/pytest-43/test_baseline_cli_records_publ0`). No live app server or model provider was started.

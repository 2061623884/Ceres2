# Baseline role-choice continuation GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k baseline_cli_preserves_role_choice_and_continues_remaining_cases`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (current uncommitted implementation slice).
- Test source: `backend/tests/test_local_followup_baseline.py`, SHA-256 `bfab2c5be40e65b13e03820c88bf5d715ac2125a25f39f3b105de27bbb7ef744`.
- Implementation: `backend/app/evaluation/run_baseline.py`, SHA-256 `63d08e80bfd3826f2b992d5ccf558cf5f89f36c73d726df4bd0eed0d478bf5bb`.
- Result: exit 0; `1 passed, 1 deselected` in 0.89s.
- The test uses a test-owned loopback fixture and calls `shutdown`, `server_close`, and `thread.join` in `finally`; case and result files stay under pytest `tmp_path`. No live app server or provider was started.

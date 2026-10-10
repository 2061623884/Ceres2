# Baseline role-choice continuation RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k baseline_cli_preserves_role_choice_and_continues_remaining_cases`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (current uncommitted implementation slice).
- Test source: `backend/tests/test_local_followup_baseline.py`, SHA-256 `bfab2c5be40e65b13e03820c88bf5d715ac2125a25f39f3b105de27bbb7ef744`.
- Implementation: `backend/app/evaluation/run_baseline.py`, SHA-256 `e86780db61afd63f8a3448b247b0317181adf73fe19cd0e8ade259122dc0138c`.
- Result: exit 1; `1 failed, 1 deselected` in 0.99s.
- Sole failure: `role-choice-required` raises `RuntimeError` because the baseline runner does not accept role switches; this aborts the batch before it captures the remaining case.
- The test owns a temporary loopback `ThreadingHTTPServer` and always calls `shutdown`, `server_close`, and `thread.join` in `finally`. Its JSON input/output are under pytest `tmp_path` (`/tmp/pytest-of-amax/pytest-40/test_baseline_cli_preserves_ro0`); no app server or provider was started.

Captured failure:

```text
RuntimeError: case 'role-choice-required' requires an explicit role switch; the baseline runner does not accept role switches
```

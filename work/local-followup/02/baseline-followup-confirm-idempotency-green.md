# Baseline declared follow-up/confirm/idempotent replay GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k test_baseline_cli_runs_declared_followup_confirm_and_idempotent_replay`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted runner slice).
- Test source SHA-256: `fd0134e0fcfd3f8542d7d9519ec63b91a960c1f3e492eaabddb9d8355ca35240`.
- Runner `backend/app/evaluation/run_baseline.py` SHA-256: `55ea887550261999af626b03092ff6c2a15841ea0903dfd94e714c228216ddd8`.
- Result: exit 0; `1 passed, 5 deselected` in 0.98s.
- The synthetic loopback test verifies two Guide captures around an explicit follow-up turn, no cart mutation before confirmation, a single cart mutation on confirmation, and identical receipt/body/idempotency key with no additional cart change on replay. It also verifies a fresh owner is not reused. The test `finally` shuts down/closes its HTTP server and joins its thread. No external service or model was used.

# Baseline declared follow-up/confirm/idempotent replay RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k test_baseline_cli_runs_declared_followup_confirm_and_idempotent_replay`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted runner slice).
- Test source: `backend/tests/test_local_followup_baseline.py`, SHA-256 `fd0134e0fcfd3f8542d7d9519ec63b91a960c1f3e492eaabddb9d8355ca35240`.
- Runner: `backend/app/evaluation/run_baseline.py`, SHA-256 `58a58c7ddfc1b78b024b8af3f932c84561cd1f4bbc7aa71a1aa6f4498165a344`.
- Result: pytest exit 1; `1 failed, 5 deselected` in 1.08s. The CLI subprocess itself exited 0, but emitted the first execution as `runner_failed` instead of `guide_run`.
- Root cause from current runner: `_execute_case` rejects any non-empty `steps` field with `NotImplementedError` before starting the case, so follow-up turn, confirmation and idempotent replay never execute.
- Test `finally` shuts down/closes the owned loopback server and joins its thread. Temporary case/batch files are under pytest `tmp_path`; no external service or model was used.

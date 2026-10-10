# Baseline core-repeat/resume plan GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k test_baseline_cli_plans_core_repeats_and_resumes_without_repeating_attempts`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source: `backend/tests/test_local_followup_baseline.py`, SHA-256 `3c71406f125d8e5ac6ea4a26546d49c1dbf0623afcd5650db2340aa0df487697`.
- Runner: `backend/app/evaluation/run_baseline.py`, SHA-256 `58a58c7ddfc1b78b024b8af3f932c84561cd1f4bbc7aa71a1aa6f4498165a344`.
- Result: exit 0; `1 passed, 4 deselected` in 1.14s.
- The synthetic loopback test verifies a stable complete plan, bounded execution, `not_run` retention, resume without repeating prior attempts, and rejection of changed plan/case hash/API base without rewriting saved output. Its `finally` shuts down/closes the owned HTTP server and joins the thread. No external service or model was used.

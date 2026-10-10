# Baseline core-repeat/resume plan RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k test_baseline_cli_plans_core_repeats_and_resumes_without_repeating_attempts`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source: `backend/tests/test_local_followup_baseline.py`, SHA-256 `3c71406f125d8e5ac6ea4a26546d49c1dbf0623afcd5650db2340aa0df487697`.
- Runner: `backend/app/evaluation/run_baseline.py`, SHA-256 `f7ddf61f3ee594833438906a279e39270481025c45ba989b6363aa1d9ac4d592`.
- Result: exit 1; `1 failed, 4 deselected` in 0.89s.
- First failure: CLI rejects `--core-repeats 3 --max-executions 2` as unrecognized arguments (subprocess exit 2), so the core-repeat/resume plan is not implemented.
- The test's `finally` shuts down and closes its owned loopback `ThreadingHTTPServer`, then joins its thread with a 2-second bound. Test data/output use pytest `tmp_path`; no external service or model was used.

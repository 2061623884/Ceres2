# Batch comparison repeated-trial/null-outcome GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_compare_batch_cli_pairs_trials_and_preserves_null_capture_outcomes`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `888b9dbc9e685033b2c6f3437dd557fe86ca324f3b9f3f39a6790e3b80f1027a`.
- Implementation `backend/app/evaluation/compare_runs.py` SHA-256: `1e2d1ecabc3d064610d6fafd6427b41752f5d88b9716cbf68719ad40675a0cf4`.
- Result: exit 0; `1 passed, 7 deselected` in 0.38s.
- This synthetic CLI test verifies planned repeated trials pair by execution ID, absent plan entries are retained, null captures keep their outcome/unknown quality, and input identity compares version plus SHA. No server or provider was started.

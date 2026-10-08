# Batch comparison repeated-trial/null-outcome RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_compare_batch_cli_pairs_trials_and_preserves_null_capture_outcomes`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `888b9dbc9e685033b2c6f3437dd557fe86ca324f3b9f3f39a6790e3b80f1027a`.
- Implementation `backend/app/evaluation/compare_runs.py` SHA-256: `5dae749478c7c40321bd72071177ddc5728c9a05d4f75e90964ba3efd4d8a23d`.
- Public manifest present during this run SHA-256: `ab4c11273e2e5e516418234c5f39457f9c05997b786bb1ec04eebc211e08d0ca` (not used by this synthetic comparison test).
- Result: exit 1; `1 failed, 7 deselected` in 0.54s.
- First failure: `load_batch` rejects the repeated `case_id` (`dev-case-01`) before pairing by `execution_id`, so the comparison never reaches its null-capture, unknown-quality, or cross-input-hash assertions.
- Synthetic JSON files are under pytest `tmp_path`; no server or provider was started.

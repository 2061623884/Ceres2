# Failure intake explicit-failure RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_failure_intake_cli_emits_only_explicitly_failed_captures_with_source_steps`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `35d01481817568da670143731643cf3c2606a00f8ed0f94864ea3b1e0e1a3c46`.
- Result: exit 1; `1 failed, 10 deselected` in 0.42s.
- First failure: CLI subprocess reports `No module named app.evaluation.failure_intake`; the explicit-failure extraction contract is not implemented yet.
- Synthetic case/batch/output files were under pytest `tmp_path`; no server or provider was started.

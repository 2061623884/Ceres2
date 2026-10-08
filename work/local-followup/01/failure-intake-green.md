# Failure intake explicit-failure GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_failure_intake_cli_emits_only_explicitly_failed_captures_with_source_steps`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `35d01481817568da670143731643cf3c2606a00f8ed0f94864ea3b1e0e1a3c46`.
- Implementation `backend/app/evaluation/failure_intake.py` SHA-256: `8ce8d50b034a0d2192bf2dafd02b16fbc42613385422afcd9ca768139d5ce679`.
- Result: exit 0; `1 passed, 10 deselected` in 0.39s.
- The synthetic CLI check verifies that only explicitly failed captures are emitted, while preserving source case steps/checks, source set and batch identity, execution/trial/owner/run, expected behavior, rationale, reviewer, and severity. Pass, needs-review, and unlabelled captures are not emitted. No server or provider was started.

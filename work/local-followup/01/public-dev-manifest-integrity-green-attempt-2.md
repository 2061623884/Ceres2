# Public development manifest integrity GREEN attempt 2 (pre-freeze)

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_public_dev_case_set_has_forty_regression_cases_and_current_fact_pointers`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256 at immediate post-run hash: `bc4a8a32b30567822ada1ebd20efb84cd18e6db85ebbc5ce6069a66990d6e7f4`.
- Manifest SHA-256 at immediate post-run hash: `3a6fd01c6d5ae9d41c608b8a86dc4a07e42a6bcf163572c7edf0266d59639b38`.
- Result: exit 0; `1 passed, 6 deselected` in 0.31s.
- The manifest was edited again after this run/hash (including a version bump). This is a historical pre-freeze pass only; it does not validate the current manifest. The final frozen version/hash must be checked separately.

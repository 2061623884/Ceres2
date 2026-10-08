# `score_batch` wait/unknown/denominator RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_preserves_wait_policy_unknown_and_every_planned_execution`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (current uncommitted evaluation slice).
- Test source: `backend/tests/test_local_followup_evaluation.py`, SHA-256 `620fe5d1b288ea87f6a219b5d5fee8af9b6c125bb4d541747275b0ca39c2ae4b`.
- Implementation: `backend/app/evaluation/score_batch.py`, SHA-256 `e53d574cc0c73faa03122ab087d556cecbc7e1307e0a79ca0a618c74ba9ca8d6`.
- Result: exit 1; `1 failed, 3 deselected` in 0.35s.
- First failure: a hard check with `actual=None` and operator `max` reaches `actual <= expected` and raises `TypeError`. Unknown/null check handling is not implemented; the CLI exits before emitting the expected denominator report.
- The test uses synthetic files under pytest `tmp_path`; no server or provider was started.

# `score_batch_cli` RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k score_batch_cli`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (current uncommitted evaluation slice).
- Test source: `backend/tests/test_local_followup_evaluation.py`, SHA-256 `0ee7bb76b14be900a0ed7cd04544cd611a9feaab5f99ca5f13f1652175cf710f`.
- Result: exit 1; `1 failed, 2 deselected` in 0.33s.
- Sole failure: the test subprocess cannot import `app.evaluation.score_batch` (`No module named app.evaluation.score_batch`). The expected CLI module does not exist in this snapshot.
- The CLI test creates synthetic case/batch JSON under pytest `tmp_path`; it starts no app server and calls no model provider.

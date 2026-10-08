# `annotate_batch_cli` RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k annotate_batch_cli`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (implementation slice under test is the current uncommitted tree).
- Test source: `backend/tests/test_local_followup_evaluation.py`, SHA-256 `bd52cafa05f37ba45d74e00f250179f6899a8f167bce518c0ea833d7c2d029f0`.
- Result: exit 1; `1 failed, 1 deselected`.
- Sole failure: the test subprocess cannot import `app.evaluation.annotate_batch` (`No module named app.evaluation.annotate_batch`). The expected CLI module does not exist in this snapshot.
- The test used its pytest `tmp_path` for capture, annotation, and output files (`/tmp/pytest-of-amax/pytest-39/test_annotate_batch_cli_joins_0`). No application server or live provider was started. Temporary files were owned by pytest; no manual cleanup was performed.

Captured failure detail:

```text
/data/amax/Documents/projects/Agent/Agent产品/Ceres2-integration-20261008/.venv/bin/python: No module named app.evaluation.annotate_batch
```

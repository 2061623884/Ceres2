# `annotate_batch_cli` GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k annotate_batch_cli`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation implementation slice).
- Test source: `backend/tests/test_local_followup_evaluation.py`, SHA-256 `bd52cafa05f37ba45d74e00f250179f6899a8f167bce518c0ea833d7c2d029f0`.
- Implementation: `backend/app/evaluation/annotate_batch.py`, SHA-256 `ef9575a46641851285d084e4b316e09715240691ea07cd11215259b6d002574c`.
- Result: exit 0; `1 passed, 1 deselected` in 0.39s.
- This is the focused CLI contract test only; no application server or live provider was started.

# `score_batch_cli` GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k score_batch_cli`
- Worktree snapshot: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (current uncommitted evaluation slice).
- Test source: `backend/tests/test_local_followup_evaluation.py`, SHA-256 `18e2577d975e37c49bb865f5fb2a1367bb8106d1c7e95e3ccd47794e873228a9`.
- Implementation: `backend/app/evaluation/score_batch.py`, SHA-256 `e53d574cc0c73faa03122ab087d556cecbc7e1307e0a79ca0a618c74ba9ca8d6`.
- Result: exit 0; `1 passed, 2 deselected` in 0.29s.
- This is the focused local CLI contract test with synthetic capture/catalog data; no app server, live catalog, or model provider was started.

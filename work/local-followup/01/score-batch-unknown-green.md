# `score_batch` unknown/wait/denominator GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_preserves_wait_policy_unknown_and_every_planned_execution`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `35ee0254b85f8dda4dc71a1621bd943b0a49bd8cab3402dbe636a4f2dc5a667a`.
- Implementation `backend/app/evaluation/score_batch.py` SHA-256: `879a23361b4a893be594e0df390642cb86e14926026760a3a9600690353e32da`.
- Result: exit 0; `1 passed, 5 deselected` in 0.31s.
- This synthetic CLI check covers role-wait, policy/no-plan, null hard-check unknown, and preservation of planned execution denominator. No server or provider was started.

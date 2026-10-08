# `score_batch` per-step confirmation/replay RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_checks_turn_confirmation_and_replay_at_each_step`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `46676ee946f2cb42fcc7b33c77adea4ad49bcdfbcb715b2839611013139b339a`.
- Scorer `backend/app/evaluation/score_batch.py` SHA-256: `879a23361b4a893be594e0df390642cb86e14926026760a3a9600690353e32da`.
- Result: exit 1; `1 failed, 6 deselected` in 0.41s.
- First failure: the valid case, which confirms once and then repeats the same idempotency key without changing the cart, is scored `fail` instead of `pass`. Current scorer compares only execution-level `before`/`after` cart state and treats the authorized confirmation as `unauthorized_cart_change`; it does not yet inspect declared step boundaries. The second synthetic case is designed to assert critical violations for unauthorized turn-time and repeated-write changes, but was not reached after the first assertion failure.
- This is a synthetic batch/scorer test using pytest `tmp_path`; no server, loopback fixture, or provider was started.

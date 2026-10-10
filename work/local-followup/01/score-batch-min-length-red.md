# `score_batch` public plan `min_length` RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_min_length_check_handles_public_plan_item_arrays`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source: `backend/tests/test_local_followup_evaluation.py`, SHA-256 `eb57a34d7649fd5f289e5b24efd567d762637f305579f879a1c52e7fb05a2eca`.
- Implementation: `backend/app/evaluation/score_batch.py`, SHA-256 `e53d574cc0c73faa03122ab087d556cecbc7e1307e0a79ca0a618c74ba9ca8d6`.
- Result: exit 1; `1 failed, 5 deselected`.
- Sole failure: the exact-offer one-item plan reaches `_matches` with operator `min_length`, which raises `ValueError: Unsupported check operator: min_length` at `backend/app/evaluation/score_batch.py:43`.
- The test uses synthetic files under pytest `tmp_path`; no server or provider was started. Pytest owns temporary-directory cleanup.

# `score_batch` all-run human labels/last-run scope RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_reports_all_run_labels_and_scopes_quality_to_last_guide_run`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `8ec17f49d8a6115624286e2512523f914197bf3132ed726f35065d3bfed656f4`.
- Scorer `backend/app/evaluation/score_batch.py` SHA-256: `b3ba570d3154c0365c2f5dc69d686f630c1261b562b15c998bdaf1b63810d414`.
- Result: exit 1; `1 failed, 11 deselected` in 0.43s.
- First failure: the legacy `human_quality` alias is `pass`, but the report lacks required `human_quality_scope='last_guide_run'`; per-capture human run labels are also expected by the test. No output was produced with the required scope contract.
- Synthetic batch files were under pytest `tmp_path`; no server or provider was started.

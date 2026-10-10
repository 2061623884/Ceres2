# Public development manifest integrity GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_public_dev_case_set_has_forty_regression_cases_and_current_fact_pointers`
- Worktree: `codex/ceres2-local-followup-20261008`, HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d` (uncommitted evaluation slice).
- Test source SHA-256: `35ee0254b85f8dda4dc71a1621bd943b0a49bd8cab3402dbe636a4f2dc5a667a`.
- Manifest `evals/ceres2-local-followup-dev.json` SHA-256: `818c3426e0266eabd997d31d4464e9ea22a4fee87df69dcc774674155f7383c5`.
- Scorer `backend/app/evaluation/score_batch.py` SHA-256: `879a23361b4a893be594e0df390642cb86e14926026760a3a9600690353e32da`.
- Result: exit 0; `1 passed, 5 deselected` in 0.23s.
- The test validates 40 regression cases and their current fact pointers against the checked-in Ceres2 demo sources. It does not run model/API sampling or establish answer quality.

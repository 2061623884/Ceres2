# Public development manifest integrity v2 attempt

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_public_dev_case_set_has_forty_regression_cases_and_current_fact_pointers`
- Result: exit 1; 1 failed, 13 deselected (0.30s).
- Test source SHA-256: `cbdca37bc5b129f9c0c86c4e7075a128d82f6baf3b9ec59a0e520546c03679a8`.
- Public case manifest version: `ceres2-local-followup-dev-2026-10-08-v2`; SHA-256 `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d`.
- First failure: pointer `backend/app/prompts/experience.json#expression.keke` is tested as a literal substring of the source file. The JSON contains nested `expression` and `keke` keys, so the dotted path exists structurally but the literal string does not. No other check failed before this assertion.
- Raw pytest output: [public-dev-manifest-integrity-v2-fail.log](public-dev-manifest-integrity-v2-fail.log), SHA-256 `40e7f9231efa406c885fba368b005eb9304c3ff839eb000b7c9520d041914d51`.
- This is retained as a failed integrity attempt, not a GREEN result. No source, manifest, test, service, or provider was modified or called by the tester.

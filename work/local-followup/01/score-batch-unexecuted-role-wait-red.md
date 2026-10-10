# score_batch unexecuted and role-wait outcomes RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_keeps_unexecuted_rows_unknown_and_scores_actual_role_wait`
- Result: exit 1; 1 failed, 17 deselected (0.58s).
- Test source SHA-256: `8947ae2405f46936400cbf9a3899a7e9e22f600e09a3ecb1b475274d52260e10`.
- `score_batch.py` SHA-256: `3ca87f34238096ec7666bef5483349e385edd791c25ce85e1ca987d5c1dd28d1`.
- First failure: a planned `not_run` case is scored as `business_verdict=fail`; expected both `not_run` and `preparation_failed` rows to remain `unknown`. The test also asserts the separately completed role-choice case counts as a role wait while preserving Keke as the active role.
- Raw pytest output: [score-batch-unexecuted-role-wait-red.log](score-batch-unexecuted-role-wait-red.log), SHA-256 `88d637d795b9df6d6c71ac51a4a53fbe999b9234f540b2b9ccce412ca82c77f0`.
- Synthetic CLI input only; no service, live provider, or model call.

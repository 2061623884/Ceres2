# score_batch unexecuted and role-wait outcomes GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_keeps_unexecuted_rows_unknown_and_scores_actual_role_wait`
- Result: exit 0; 1 passed, 17 deselected (0.39s).
- Test source SHA-256: `8947ae2405f46936400cbf9a3899a7e9e22f600e09a3ecb1b475274d52260e10`.
- Implementation SHA-256 (`backend/app/evaluation/score_batch.py`): `464c7130ed8e8f13287b88b41e8ca8572d344b6381e79445061e76bc2c973e9a`.
- Unexecuted, preparation-failed, and runner-failed cases remain in the planned denominator with unknown business verdicts; the actual role-choice outcome counts as a role wait without changing the active Keke role.
- Raw pytest output: [score-batch-unexecuted-role-wait-green.log](score-batch-unexecuted-role-wait-green.log), SHA-256 `dd6483b0f82ac3420175e13b0cdb1883fab6fd064e155b74a2f81c2a251e967c`.

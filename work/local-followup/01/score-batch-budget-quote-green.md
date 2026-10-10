# score_batch budget quote boundary GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_treats_unconfirmable_budget_quote_as_pending_not_critical`
- Result: exit 0; 1 passed, 16 deselected (0.51s).
- Test source SHA-256: `acea91b790f431f7bf41b5b0c10f29c22560890c3242f319c6196c94a52c2ba8`.
- Implementation SHA-256 (`backend/app/evaluation/score_batch.py`): `3ca87f34238096ec7666bef5483349e385edd791c25ce85e1ca987d5c1dd28d1`.
- A non-confirmable quote that exceeds the user's budget now remains a pending/unknown business outcome rather than a critical failure.
- Raw pytest output: [score-batch-budget-quote-green.log](score-batch-budget-quote-green.log), SHA-256 `23d0832844693c20100e56c42665fe844cf25d1f05e6c1a0e291b9af85c03443`.

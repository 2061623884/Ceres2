# score_batch budget quote boundary GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_treats_unconfirmable_budget_quote_as_pending_not_critical`
- Result: exit 0; 1 passed, 16 deselected (0.40s).
- Test source SHA-256: `f09e0b0476d7f3724ebed34ab89f256907764648fbb71daef9477545ca58f84f`.
- Implementation SHA-256 (`backend/app/evaluation/score_batch.py`): `3ca87f34238096ec7666bef5483349e385edd791c25ce85e1ca987d5c1dd28d1`.
- A non-confirmable quote above the user's budget remains pending/unknown rather than a business failure.
- Raw pytest output: [score-batch-budget-quote-green-final.log](score-batch-budget-quote-green-final.log), SHA-256 `c62531d6c60d7a41423c4f9c368a337eb8ae6f0a0e90d40527929008efb52af2`.

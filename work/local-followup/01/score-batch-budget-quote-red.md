# score_batch budget quote boundary RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_treats_unconfirmable_budget_quote_as_pending_not_critical`
- Result: exit 1; 1 failed, 16 deselected (0.61s).
- Test source SHA-256: `c7cb223e0071a5a9a507bffcb744a759b4df13653e7f9b2515cfdb6780218624`.
- Implementation SHA-256 (`backend/app/evaluation/score_batch.py`): `359271f20bc6cacf4000db8ff93eb50bc214529178b5f3fbb5256705ba733ef7`.
- First failure: the quote scenario has a valid pending `waiting_confirmation` state and explicit non-confirmable quote, but the scorer returns `business_verdict=fail` instead of `unknown`. The 1500-fen quote is over the captured 1000-fen budget and must not be treated as a confirmed business failure.
- Raw pytest output: [score-batch-budget-quote-red.log](score-batch-budget-quote-red.log), SHA-256 `9d935309c4f8d65031ec432e8b88026a320b659cd4dadfab4a77e54338a5a617`.
- Synthetic temporary inputs only; no service, live provider, or model call.

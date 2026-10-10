# evaluation report aggregation CLI GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_evaluation_report_cli_keeps_denominators_multirun_timing_and_usage_unknown`
- Result: exit 0; 1 passed, 16 deselected (0.40s).
- Test source SHA-256: `f09e0b0476d7f3724ebed34ab89f256907764648fbb71daef9477545ca58f84f`.
- `report_batch.py` SHA-256: `3775cbf968dc574ebdcd171a123bf381af75c4dfeff10a42e08a722c917c702f`; `score_batch.py` SHA-256: `3ca87f34238096ec7666bef5483349e385edd791c25ce85e1ca987d5c1dd28d1`.
- The report preserves planned/attempted/not-run denominators, every capture label with last-run quality scope, per-step arrival timing percentiles, and unknown usage/cost when records are incomplete. The test fixture now binds the score to the source batch digest.
- Raw pytest output: [evaluation-report-multirun-timing-green-final.log](evaluation-report-multirun-timing-green-final.log), SHA-256 `c62531d6c60d7a41423c4f9c368a337eb8ae6f0a0e90d40527929008efb52af2`.

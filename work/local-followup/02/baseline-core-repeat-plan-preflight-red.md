# run_baseline unsupported-step preflight RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k test_baseline_cli_plans_core_repeats_and_resumes_without_repeating_attempts`
- Result: exit 1; 1 failed, 6 deselected (1.38s).
- Test source SHA-256: `0d0b7d9f3ccc4323fc0bc60a0616a3b57d443f8dfba83564b184c1a1b09e4dff`.
- Runner SHA-256 (`backend/app/evaluation/run_baseline.py`): `d079ee2dbc511a1c7ec02e9ef00c2e35e70667445c6b7ac2877d31a947aa52e7`.
- Failure: unsupported declared step is reported by name, but `before` and `catalog_facts` are non-null. The owner’s updated expectation requires a preflight rejection before any baseline state/catalog capture.
- Raw pytest output: [baseline-core-repeat-plan-preflight-red.log](baseline-core-repeat-plan-preflight-red.log), SHA-256 `d5ec6bc2e7b07879ccd7b7ba18681ef13d4620d19b652e0f00538d84050bb7e6`.
- The loopback fixture is shut down and joined by the test’s `finally` block. No live service/provider was used.

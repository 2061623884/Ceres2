# run_baseline unsupported-step preflight GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k test_baseline_cli_plans_core_repeats_and_resumes_without_repeating_attempts`
- Result: exit 0; 1 passed, 6 deselected (1.15s).
- Test source SHA-256: `0d0b7d9f3ccc4323fc0bc60a0616a3b57d443f8dfba83564b184c1a1b09e4dff`.
- Runner SHA-256 (`backend/app/evaluation/run_baseline.py`): `cdda0026e00531cff82cfb1fdd0559d067d1184610055d207fadf46cf7e52b29`.
- Unsupported `steps` operations are rejected before any API state or catalog capture; core repeat/resume accounting remains correct.
- Raw pytest output: [baseline-core-repeat-plan-preflight-green.log](baseline-core-repeat-plan-preflight-green.log), SHA-256 `20d2bf318312e57ce2be20cf8b778c71a893fb4aed2a0424d4897703139aa739`.
- Loopback fixture cleanup completed in `finally`; no live service/provider was used.

# run_baseline current module regression

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py`
- Result: exit 1; 1 failed, 6 passed (5.82s).
- Test source SHA-256: `03be48243fdc8b74891d777d381dcd881736ccfbc40978e3e98ad452fa4c7dc9`.
- Runner SHA-256 (`backend/app/evaluation/run_baseline.py`): `d079ee2dbc511a1c7ec02e9ef00c2e35e70667445c6b7ac2877d31a947aa52e7`.
- Failure: `test_baseline_cli_plans_core_repeats_and_resumes_without_repeating_attempts`. For a deliberately malformed `steps` row, the test expected the recorded reason to identify `steps`, but it instead recorded `"'op'"` from a `KeyError`.
- Raw pytest output: [baseline-runner-file-current.log](baseline-runner-file-current.log), SHA-256 `61ad6788f6524fa24503284e7e614775f867a6dbeb6b3e8d3dd8685eb2ac4ddf`.
- The six other tests, including public session-history filtering, passed. Their loopback fixtures were test-owned and cleaned up in `finally`; no live provider/service was used.

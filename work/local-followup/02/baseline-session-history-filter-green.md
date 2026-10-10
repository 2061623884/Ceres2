# run_baseline per-capture session history GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k test_baseline_cli_filters_public_session_history_to_each_capture_request`
- Result: exit 0; 1 passed, 6 deselected (0.92s).
- Test source SHA-256: `03be48243fdc8b74891d777d381dcd881736ccfbc40978e3e98ad452fa4c7dc9`.
- Runner SHA-256 (`backend/app/evaluation/run_baseline.py`): `d079ee2dbc511a1c7ec02e9ef00c2e35e70667445c6b7ac2877d31a947aa52e7`.
- The initial and follow-up captures now each contain only user messages for their own request ID, while preserving their public session sequence values.
- Raw pytest output: [baseline-session-history-filter-green.log](baseline-session-history-filter-green.log), SHA-256 `8c546a253fd514e0769dde79e9ad1153016d91168fbf58eaeb3f810d8fb3e509`.
- The test-owned loopback HTTP fixture shut down and joined in `finally`; no live provider or service was used.

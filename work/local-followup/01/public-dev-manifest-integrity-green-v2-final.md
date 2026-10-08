# Public development manifest integrity v2 GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_public_dev_case_set_has_forty_regression_cases_and_current_fact_pointers`
- Result: exit 0; 1 passed, 13 deselected (0.35s).
- Test source SHA-256: `60fd73771c5f913ed654af0c8b0e4ebf8c71b16a385d8e3451800d021fece387`.
- Manifest `ceres2-local-followup-dev-2026-10-08-v2` SHA-256: `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d`.
- The validator now resolves dotted anchors against nested JSON objects; the current fact pointers all passed.
- Raw pytest output: [public-dev-manifest-integrity-green-v2-final.log](public-dev-manifest-integrity-green-v2-final.log), SHA-256 `0095cd8111945a80e39d07ba972844dc9da8d293d3815f51bc0118ef59f4e642`.

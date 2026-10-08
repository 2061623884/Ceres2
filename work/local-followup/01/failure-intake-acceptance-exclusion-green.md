# failure_intake acceptance exclusion GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_failure_intake_cli_excludes_non_regression_acceptance_cases`
- Result: exit 0; 1 passed, 14 deselected (0.38s).
- Test source SHA-256: `32edb22380469cce94ba54d09a6bcefee38bae26f0bd0073c4b067f994801ed0`.
- Implementation SHA-256 (`backend/app/evaluation/failure_intake.py`): `f0b8bb7d769ddc870c8bcebcb50812df4a632b4fd9ab064711d98923e8d734d5`.
- The CLI now excludes failed captures from a non-regression acceptance case when generating regression intake.
- Raw pytest output: [failure-intake-acceptance-exclusion-green.log](failure-intake-acceptance-exclusion-green.log), SHA-256 `d5e9c180de04ea3cab730beba89fa4da24dbbd6d01c42981da7f1ac9e7154540`.

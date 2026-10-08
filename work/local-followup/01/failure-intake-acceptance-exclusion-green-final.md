# failure_intake acceptance split boundary GREEN (final source)

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_failure_intake_cli_excludes_non_regression_acceptance_cases`
- Result: exit 0; 1 passed, 16 deselected (0.39s).
- Test source SHA-256: `f09e0b0476d7f3724ebed34ab89f256907764648fbb71daef9477545ca58f84f`.
- Implementation SHA-256 (`backend/app/evaluation/failure_intake.py`): `ebe4029805a504a75ec04e9534910c8f55598ea2b7b717ac444bf373ebec8de6`.
- The final source checks the case split before parsing run labels, and excludes acceptance cases from regression failure intake.
- Raw pytest output: [failure-intake-acceptance-exclusion-green-final.log](failure-intake-acceptance-exclusion-green-final.log), SHA-256 `a5e81d62383e9739df44f6406b46314b58b29dfc9806ba75984158e72f231503`.

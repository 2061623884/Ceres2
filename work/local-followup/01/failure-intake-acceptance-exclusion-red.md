# failure_intake acceptance exclusion RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_failure_intake_cli_excludes_non_regression_acceptance_cases`
- Result: exit 1; 1 failed, 14 deselected (0.58s).
- Test source SHA-256: `32edb22380469cce94ba54d09a6bcefee38bae26f0bd0073c4b067f994801ed0`.
- `failure_intake.py` SHA-256: `8ce8d50b034a0d2192bf2dafd02b16fbc42613385422afcd9ca768139d5ce679`.
- First failure: the CLI returned success but emitted an `acceptance`-split failed case into the regression failure set; expected `cases: []`. This confirms failure intake currently lacks the split boundary.
- Raw pytest output: [failure-intake-acceptance-exclusion-red.log](failure-intake-acceptance-exclusion-red.log), SHA-256 `4ae10d8847c8d06ab72e03bfc81491c1b8608e816e343ebde765659933073399`.
- Synthetic `tmp_path` files only; no service, live provider, or model call.

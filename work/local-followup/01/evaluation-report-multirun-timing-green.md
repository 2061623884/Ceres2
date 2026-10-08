# evaluation report aggregation CLI GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_evaluation_report_cli_keeps_denominators_multirun_timing_and_usage_unknown`
- Result: exit 0; 1 passed, 14 deselected (0.39s).
- Test source SHA-256: `32edb22380469cce94ba54d09a6bcefee38bae26f0bd0073c4b067f994801ed0`.
- Implementation SHA-256 (`backend/app/evaluation/report_batch.py`): `9c361d9e436cef8ec880fa07019be1dcc760243ac1ee4b7eae64b7f0d2ac0675`.
- The case verifies planned/attempted/not-run denominators, final-run quality with all run labels, per-step client timing percentiles, and unknown usage/cost when provider records are incomplete or absent. It ignores duplicate row-level timing and untrusted runtime-event token claims.
- Raw pytest output: [evaluation-report-multirun-timing-green.log](evaluation-report-multirun-timing-green.log), SHA-256 `a578996d11deceaae72627fac75f325fac289baee996b8f9d8674397806dc93d`.
- Synthetic CLI inputs only; no service, live provider, or model call.

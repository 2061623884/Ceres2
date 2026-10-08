# evaluation report aggregation CLI RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_evaluation_report_cli_keeps_denominators_multirun_timing_and_usage_unknown`
- Result: exit 1; 1 failed, 13 deselected (0.42s).
- Test source SHA-256: `cbdca37bc5b129f9c0c86c4e7075a128d82f6baf3b9ec59a0e520546c03679a8`.
- First failure: the CLI subprocess cannot import `app.evaluation.report_batch` (`No module named app.evaluation.report_batch`). The test reached the intended missing-module assertion; no configuration guard or live provider failure occurred.
- The case covers planned/attempted/not-run denominators, every guide-run label and last-run quality scope, per-step client arrival timing percentiles, and usage/cost remaining unknown when provider records are incomplete or absent.
- Raw pytest output: [evaluation-report-multirun-timing-red.log](evaluation-report-multirun-timing-red.log), SHA-256 `e9f6f642362833aee0e4369270d3b60059ca78774470c5703181a562c7a8d383`.
- Temporary loopback/service fixtures were not used. No service, model, or live provider was called.

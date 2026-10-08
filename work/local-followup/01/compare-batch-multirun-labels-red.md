# compare_runs multi-run label scope RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_compare_batch_cli_exposes_all_run_labels_and_last_run_quality_scope`
- Result recorded from the tester execution: exit 1; 1 failed, 12 deselected.
- Test source SHA-256: `8ec17f49d8a6115624286e2512523f914197bf3132ed726f35065d3bfed656f4`.
- Compare implementation SHA-256 at the RED attempt: `1e2d1ecabc3d064610d6fafd6427b41752f5d88b9716cbf68719ad40675a0cf4`.
- First failure: `KeyError: 'quality_scope'` after the legacy quality verdict assertion. The output had no declared last-guide-run scope or all-run labels for the fail/null/pass captures.
- The raw console output was not retained for this attempt. This report records the observed failure and explicitly does not claim a raw log artifact.
- The corresponding implementation GREEN is preserved at [compare-batch-multirun-labels-green.md](compare-batch-multirun-labels-green.md).

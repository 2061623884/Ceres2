# compare_runs batch-v1 CLI RED

- Command: `(cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k compare)`
- Pytest result: exit 1; 1 selected test failed, 0 passed.
- Test: `test_compare_batch_cli_pairs_cases_and_keeps_unreviewed_quality_unknown`.
- Frozen batch-v1 test source SHA-256: `6bfaf1fd49d4a802076bf37329066d2cf368791484506ae50a68db1c6dd9f6de`.
- Root cause: the CLI subprocess exits 1 because Python cannot import `app.evaluation.compare_runs` (`No module named app.evaluation.compare_runs`). The test reached its assertion; no configuration guard or live provider failure occurred.
- Raw pytest output is retained in the ignored sibling `compare-batch-red.log` (SHA-256 `32a84dff02138be3b36e10c7092c27e96997f15392df223ed211a59198eb5f9c`).
- This batch-v1 RED is current; the earlier per-session RED is retained separately as pre-contract-revision evidence. No source, lock, configuration, or test file was changed by Tester. No build, API, server, model, or other pytest command was run.

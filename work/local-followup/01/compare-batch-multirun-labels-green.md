# compare_runs multi-run label scope GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_compare_batch_cli_exposes_all_run_labels_and_last_run_quality_scope`
- Result: exit 0; 1 passed, 12 deselected (0.40s).
- Test source SHA-256: `8ec17f49d8a6115624286e2512523f914197bf3132ed726f35065d3bfed656f4`.
- Implementation SHA-256 (`backend/app/evaluation/compare_runs.py`): `1313a91318d644ee92e8e0a55e193df383e2b7a217a24344bf52ad789d68c430`.
- The case verifies the last guide run remains the quality alias and all three captures' owner/run labels and verdicts are present for fail, null, and pass outcomes.
- Raw pytest output: [compare-batch-multirun-labels-green.log](compare-batch-multirun-labels-green.log), SHA-256 `89da4bcddc27b7ad1795cd1beb5776273eef094cdad94a6bad5c4978f68cf973`.
- This was a synthetic CLI test using isolated temporary inputs; no service, live provider, or model call was made.

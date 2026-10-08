# score_batch multi-run label scope GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_reports_all_run_labels_and_scopes_quality_to_last_guide_run`
- Result: exit 0; 1 passed, 12 deselected (0.39s).
- Test source SHA-256: `8ec17f49d8a6115624286e2512523f914197bf3132ed726f35065d3bfed656f4`.
- Implementation SHA-256 (`backend/app/evaluation/score_batch.py`): `359271f20bc6cacf4000db8ff93eb50bc214529178b5f3fbb5256705ba733ef7`.
- The case verifies that the last guide run remains the quality alias with `human_quality_scope=last_guide_run`, and that labels for all three captures are retained, including fail, null, and pass outcomes.
- Raw pytest output: [score-batch-multirun-labels-green.log](score-batch-multirun-labels-green.log), SHA-256 `e1c2ee61cf2c0745a90a6532c11e37159e12cebaa6d41d4260eb8d5c208e38e0`.
- This was a synthetic CLI test using its isolated temporary inputs; no service, live provider, or model call was made.

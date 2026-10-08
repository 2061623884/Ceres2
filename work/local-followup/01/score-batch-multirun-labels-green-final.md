# score_batch multi-run label scope GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_score_batch_reports_all_run_labels_and_scopes_quality_to_last_guide_run`
- Result: exit 0; 1 passed, 13 deselected (0.38s).
- Test source SHA-256: `60fd73771c5f913ed654af0c8b0e4ebf8c71b16a385d8e3451800d021fece387`.
- Implementation SHA-256 (`backend/app/evaluation/score_batch.py`): `359271f20bc6cacf4000db8ff93eb50bc214529178b5f3fbb5256705ba733ef7`.
- The case verifies the last guide run is the quality alias with `human_quality_scope=last_guide_run`, and labels for all captures include fail, null, and pass.
- Raw pytest output: [score-batch-multirun-labels-green-final.log](score-batch-multirun-labels-green-final.log), SHA-256 `1bb7cfb720a406ebe8c74af936fce1f59c84b9ab1dee0e6282814ff2c84886e8`.

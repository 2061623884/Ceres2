# report_batch batch identity validation RED

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_evaluation_report_rejects_score_from_different_batch_bytes`
- Result: exit 1; 1 failed, 16 deselected (0.62s).
- Test source SHA-256: `c7cb223e0071a5a9a507bffcb744a759b4df13653e7f9b2515cfdb6780218624`.
- `report_batch.py` SHA-256: `9c361d9e436cef8ec880fa07019be1dcc760243ac1ee4b7eae64b7f0d2ac0675`; `score_batch.py` SHA-256: `359271f20bc6cacf4000db8ff93eb50bc214529178b5f3fbb5256705ba733ef7`.
- First failure: score was produced from the original batch, then the candidate batch's `first_final_ms` was changed from 200 to 201. `report_batch` accepted the score/batch mismatch and returned 0; the test expects rejection.
- Raw pytest output: [evaluation-report-batch-hash-mismatch-red.log](evaluation-report-batch-hash-mismatch-red.log), SHA-256 `96ea4bd04e82cfa3905193597dc0623fdaa535851243c7877b520a43a6c7e2f5`.
- Synthetic temporary inputs only; no service, live provider, or model call.

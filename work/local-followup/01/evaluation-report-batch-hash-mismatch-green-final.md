# report_batch batch identity validation GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_evaluation_report_rejects_score_from_different_batch_bytes`
- Result: exit 0; 1 passed, 16 deselected (0.67s).
- Test source SHA-256: `f09e0b0476d7f3724ebed34ab89f256907764648fbb71daef9477545ca58f84f`.
- `report_batch.py` SHA-256: `3775cbf968dc574ebdcd171a123bf381af75c4dfeff10a42e08a722c917c702f`.
- A score generated from different batch bytes is rejected with a clear mismatch error.
- Raw pytest output: [evaluation-report-batch-hash-mismatch-green-final.log](evaluation-report-batch-hash-mismatch-green-final.log), SHA-256 `516e1f54a10e9871be4e46eaa7a762ee8cbab4856e566adc01289686b6a78f49`.

# report_batch batch identity validation GREEN attempt 1

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k test_evaluation_report_rejects_score_from_different_batch_bytes`
- Result: exit 1; 1 failed, 16 deselected (0.64s).
- Test source SHA-256: `acea91b790f431f7bf41b5b0c10f29c22560890c3242f319c6196c94a52c2ba8`.
- `report_batch.py` SHA-256: `3775cbf968dc574ebdcd171a123bf381af75c4dfeff10a42e08a722c917c702f`; `score_batch.py` SHA-256: `3ca87f34238096ec7666bef5483349e385edd791c25ce85e1ca987d5c1dd28d1`.
- The behavior under test now works: report generation rejects a score whose `batch_sha256` does not match the supplied batch. The assertion failed only because it expected lowercase `score batch_sha256...` while stderr contains `ValueError: Score batch_sha256...` with uppercase `S`.
- Raw pytest output: [evaluation-report-batch-hash-mismatch-green.log](evaluation-report-batch-hash-mismatch-green.log), SHA-256 `067e7dcfa456e29996317e0e889b2d432f0a78bd6e00150c6287301f447e9983`.
- This attempt is not counted as GREEN; awaiting the owner decision on normalizing the assertion/message.

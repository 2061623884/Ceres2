# Amount validation delta GREEN

The isolated amount-closure CLI test passed after the follow-up fix.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest tests/test_local_followup_evaluation.py::test_score_batch_cli_checks_plan_and_confirmed_cart_amounts -q
```

Result: exit 0, **1 passed in 0.42s**. The test covers selected-total mismatches with missing Offer evidence and with quantity/unit details absent, missing amount evidence as unknown, a receipt/body item-count mismatch, and independent cart Offer-price, line-total, and total mismatch findings. Raw output: [`amount-delta-green.log`](amount-delta-green.log).

| Item | SHA-256 |
|---|---|
| `git rev-parse HEAD` before and after | `4e021e46e8c16671ae1366ec09c11f39bad01bd6` |
| `backend/app/evaluation/score_batch.py` | `cb255c4f6cdbe211dbad04d4425be77e14383da2f9080da44b9db50f068efb07` |
| `backend/tests/test_local_followup_evaluation.py` | `4f218062ff96fcd87c01da59d61bd83b2a9c9dd3aadeda5a20fdbffb6208dbe7` |

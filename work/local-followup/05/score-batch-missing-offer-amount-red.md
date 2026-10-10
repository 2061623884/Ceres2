# `score_batch` amount mismatch without Offer evidence RED

This is the isolated public CLI RED requested after the prior combined run. No other pytest test ran in this invocation.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest tests/test_local_followup_evaluation.py::test_score_batch_cli_checks_plan_and_confirmed_cart_amounts -q
```

Result: exit 1, one failed test in 0.62s. The earlier plan total, confirmed-cart money, and missing-amount checks in this same test passed. The new no-catalog row remains `business_verdict='fail'`, but it does not contain the required critical `selected_total_mismatch` evidence for known line sum 600 versus selected total 601. The test therefore fails at its final new assertion:

```text
tests/test_local_followup_evaluation.py:1434
assert any(selected_total_mismatch, severity='critical', expected=600, actual=601)
```

Raw output: [`score-batch-missing-offer-amount-red.log`](score-batch-missing-offer-amount-red.log).

| Item | SHA-256 |
|---|---|
| `git rev-parse HEAD` before and after | `e855d691d0a446c9e5385196134b55f2ec609320` |
| `backend/app/evaluation/score_batch.py` | `d23c444d099bdacd309bc673c37b2c4579f2759ad9e48eb45b03caa9bccf64bd` |
| `backend/tests/test_local_followup_evaluation.py` | `feb81d04da98101ea355e9a4b129a241d86dba91f70484fed1df1f940e77ccf3` |

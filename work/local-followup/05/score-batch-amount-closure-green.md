# `score_batch` plan/cart amount closure GREEN

The single test requested after the corresponding RED passed.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py::test_score_batch_cli_checks_plan_and_confirmed_cart_amounts
```

Result: exit 0, **1 passed in 0.42s**. The test verifies that plan selected totals match line sums, a successful confirmation is checked against current Offer unit prices and cart line/total amounts, and missing row/total amounts remain unknown rather than being coerced to zero. Raw output: [`score-batch-amount-closure-green.log`](score-batch-amount-closure-green.log).

| Item | SHA-256 |
|---|---|
| `git rev-parse HEAD` before and after | `e855d691d0a446c9e5385196134b55f2ec609320` |
| `backend/app/evaluation/score_batch.py` | `1fb9ac117f7dce624b7ff5d5c3c99226ab24763507424f9e186dff9be071bcc7` |
| `backend/tests/test_local_followup_evaluation.py` | `2c65a9b91eb9b71167818c232f028465620d4dbf4ce7dab93fe85d146363b066` |

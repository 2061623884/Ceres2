# Amount verification delta RED

This is the isolated test requested by the review-fix owner after adding two further amount cases. Prior RED/GREEN evidence remains unchanged.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest tests/test_local_followup_evaluation.py::test_score_batch_cli_checks_plan_and_confirmed_cart_amounts -q
```

Result: exit 1, one failed test in 0.62s. The no-catalog total mismatch and initial selected-total assertions passed. The next assertion covers a successful confirmation receipt whose `items_added` reports quantity 1 while the confirmation request selected quantity 2, alongside an incorrect cart unit price, line total, and cart total. The scorer reported `confirmation_receipt_mismatch`, but omitted the three required independent cart-money critical findings:

```text
tests/test_local_followup_evaluation.py:1442
expected: confirmation_receipt_mismatch, cart_catalog_price_mismatch,
          cart_line_total_mismatch, cart_total_mismatch
actual:   confirmation_receipt_mismatch
```

The later partial-line assertion was not reached and is not treated as verified in this attempt. Raw output: [`amount-delta-red.log`](amount-delta-red.log).

| Item | Before | After |
|---|---|---|
| `git rev-parse HEAD` | `4e021e46e8c16671ae1366ec09c11f39bad01bd6` | `4e021e46e8c16671ae1366ec09c11f39bad01bd6` |
| `backend/app/evaluation/score_batch.py` SHA-256 | `20e27571e8f65b08560275a3bc066302c14eb0a7dc76f038dbb203ab474d8ca7` | `20e27571e8f65b08560275a3bc066302c14eb0a7dc76f038dbb203ab474d8ca7` |
| `backend/tests/test_local_followup_evaluation.py` SHA-256 | `a70142d99a63c7ee74886495702b13814fcfec120ec5919eb1011d2ac4bcaaa5` | `a70142d99a63c7ee74886495702b13814fcfec120ec5919eb1011d2ac4bcaaa5` |

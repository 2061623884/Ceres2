# Amount delta intermediate verification

This is the requested verification after fixing the partial-line selected-total mismatch. The prior RED reports are preserved.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest tests/test_local_followup_evaluation.py::test_score_batch_cli_checks_plan_and_confirmed_cart_amounts -q
```

Result: exit 1, one failed test in 0.50s. The selected-total mismatch with missing quantity/unit is now detected as critical, and the no-catalog selected-total test also passes. The remaining first failure is the intentionally mismatched successful receipt: `items_added` quantity 1 versus request quantity 2. The scorer reports `confirmation_receipt_mismatch` but still omits independent critical cart price, line-total, and cart-total findings:

```text
tests/test_local_followup_evaluation.py:1450
expected: confirmation_receipt_mismatch, cart_catalog_price_mismatch,
          cart_line_total_mismatch, cart_total_mismatch
actual:   confirmation_receipt_mismatch
```

Raw output: [`amount-delta-partial-total-intermediate.log`](amount-delta-partial-total-intermediate.log).

| Item | SHA-256 |
|---|---|
| `git rev-parse HEAD` before and after | `4e021e46e8c16671ae1366ec09c11f39bad01bd6` |
| `backend/app/evaluation/score_batch.py` | `f578ec6c065fdfd5c12a9ed50089fa81b931fabc679f9437aec8a6205d6e3a70` |
| `backend/tests/test_local_followup_evaluation.py` | `4f218062ff96fcd87c01da59d61bd83b2a9c9dd3aadeda5a20fdbffb6208dbe7` |

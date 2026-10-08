# `score_batch` amount mismatch without Offer evidence GREEN

The single test requested after the corresponding RED passed.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest tests/test_local_followup_evaluation.py::test_score_batch_cli_checks_plan_and_confirmed_cart_amounts -q
```

Result: exit 0, **1 passed in 0.43s**. The full amount closure test now passes with the additional no-catalog scenario: available selected line amounts still produce a critical selected-total mismatch even when Offer evidence is absent, while missing amount evidence remains unknown. Raw output: [`score-batch-missing-offer-amount-green.log`](score-batch-missing-offer-amount-green.log).

| Item | SHA-256 |
|---|---|
| `git rev-parse HEAD` before and after | `e855d691d0a446c9e5385196134b55f2ec609320` |
| `backend/app/evaluation/score_batch.py` | `20e27571e8f65b08560275a3bc066302c14eb0a7dc76f038dbb203ab474d8ca7` |
| `backend/tests/test_local_followup_evaluation.py` | `feb81d04da98101ea355e9a4b129a241d86dba91f70484fed1df1f940e77ccf3` |

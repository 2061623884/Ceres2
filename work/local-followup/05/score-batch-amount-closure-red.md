# `score_batch` plan/cart amount closure RED

This is the isolated public CLI RED requested by the review-fix owner. No other pytest test ran in this invocation.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py::test_score_batch_cli_checks_plan_and_confirmed_cart_amounts
```

Result: exit 1, one failed test in 0.61s. The CLI returns successfully, but the first scenario has a self-consistent line amount of 600 fen and `selected_total_fen=601`; the scorer incorrectly returns `business_verdict='pass'` where the test requires `fail`. Later confirmation-cart assertions were not reached in this RED attempt and are not treated as verified.

```text
tests/test_local_followup_evaluation.py:1397
assert 'pass' == 'fail'
```

Raw output: [`score-batch-amount-closure-red.log`](score-batch-amount-closure-red.log).

| Item | Before | After |
|---|---|---|
| `git rev-parse HEAD` | `e855d691d0a446c9e5385196134b55f2ec609320` | `e855d691d0a446c9e5385196134b55f2ec609320` |
| `backend/app/evaluation/score_batch.py` SHA-256 | `d63b2974f7ecaf5b9cc9fbac17123180e522d87a66910ed02231cabd177a11c` | `d63b2974f7ecaf5b9cc9fbac17123180e522d87a66910ed02231cabd177a11c` |
| `backend/tests/test_local_followup_evaluation.py` SHA-256 | `2c65a9b91eb9b71167818c232f028465620d4dbf4ce7dab93fe85d146363b066` | `2c65a9b91eb9b71167818c232f028465620d4dbf4ce7dab93fe85d146363b066` |

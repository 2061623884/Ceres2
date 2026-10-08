# `score_batch` non-comparable evidence GREEN, revised input

The owner revised the synthetic invalid-value path to use `plan.note` so it does not conflict with the now-explicit total-amount contract. The prior GREEN report is retained; this result verifies the revised test input against the same implementation.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py::test_score_batch_cli_keeps_noncomparable_checks_unknown_and_continues
```

Result: exit 0, **1 passed in 0.68s**. The expected plugin-autoload warning remains. Raw output: [`score-batch-noncomparable-green-v2.log`](score-batch-noncomparable-green-v2.log).

| Item | SHA-256 |
|---|---|
| `git rev-parse HEAD` before and after | `e855d691d0a446c9e5385196134b55f2ec609320` |
| `backend/app/evaluation/score_batch.py` | `d63b2974f7ecaf5b9cc9fbac17123180e522d87a66910ed02231cabd177a11c` |
| `backend/tests/test_local_followup_evaluation.py` | `d9a7cd9b19497433fff42519f752275fd7c2acc932b9859632f9750f7928efe5` |

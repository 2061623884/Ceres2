# `score_batch` non-comparable evidence GREEN

The single test requested after the corresponding RED passed.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py::test_score_batch_cli_keeps_noncomparable_checks_unknown_and_continues
```

Result: exit 0, **1 passed in 0.59s**. The expected pytest warning appears because plugin autoload is disabled. The test verifies an incomparable numeric comparison is retained as an evidence gap while subsequent checks and a later valid case are still scored, and that an unknown operator remains a configuration error. Raw output: [`score-batch-noncomparable-green.log`](score-batch-noncomparable-green.log).

| Item | SHA-256 |
|---|---|
| `git rev-parse HEAD` before and after | `e855d691d0a446c9e5385196134b55f2ec609320` |
| `backend/app/evaluation/score_batch.py` | `d63b2974f7ecaf5b9cc9fbac17123180e522d87a66910ed02231cabd177a11c` |
| `backend/tests/test_local_followup_evaluation.py` | `04e9e2f1b5fafd50d635a4cfccce74bfd3f397ecd0ce3979b1e9d3164754579a` |

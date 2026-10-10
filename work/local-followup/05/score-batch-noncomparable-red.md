# `score_batch` non-comparable evidence RED

This is the isolated public CLI RED requested by the review-fix owner. No other pytest test ran in this invocation.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py::test_score_batch_cli_keeps_noncomparable_checks_unknown_and_continues
```

Result: exit 1, one failed test in 0.60s. The first check compares `after.guide.plan.selected_total_fen='bad-string'` with integer minimum `100`; the scorer aborts instead of keeping that check non-comparable/unknown and continuing later checks and rows:

```text
backend/app/evaluation/score_batch.py:40, _matches
TypeError: '>=' not supported between instances of 'str' and 'int'
```

Raw output: [`score-batch-noncomparable-red.log`](score-batch-noncomparable-red.log).

| Item | Before | After |
|---|---|---|
| `git rev-parse HEAD` | `e855d691d0a446c9e5385196134b55f2ec609320` | `e855d691d0a446c9e5385196134b55f2ec609320` |
| `backend/app/evaluation/score_batch.py` SHA-256 | `464c7130ed8e8f13287b88b41e8ca8572d344b6381e79445061e76bc2c973e9a` | `464c7130ed8e8f13287b88b41e8ca8572d344b6381e79445061e76bc2c973e9a` |
| `backend/tests/test_local_followup_evaluation.py` SHA-256 | `04e9e2f1b5fafd50d635a4cfccce74bfd3f397ecd0ce3979b1e9d3164754579a` | `04e9e2f1b5fafd50d635a4cfccce74bfd3f397ecd0ce3979b1e9d3164754579a` |

# `report_batch` status/deadline/unannotated RED

This is the isolated public CLI RED requested by the review-fix owner. No other pytest test ran in this invocation.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py::test_report_cli_separates_run_status_critical_deadline_and_unannotated_usefulness
```

Result: exit 1, one failed test in 0.60s. The batch contains `protected` and other run statuses, a stopped/failed deadline boundary, an explicitly unannotated case, and legacy single-turn timing. The current reporter crashes before producing a report while indexing `timing[field]` for a `None` timing value:

```text
backend/app/evaluation/report_batch.py:255, aggregate_report
TypeError: 'NoneType' object is not subscriptable
```

Raw output: [`report-cli-status-red.log`](report-cli-status-red.log).

| Item | Before | After |
|---|---|---|
| `git rev-parse HEAD` | `e855d691d0a446c9e5385196134b55f2ec609320` | `e855d691d0a446c9e5385196134b55f2ec609320` |
| `backend/app/evaluation/report_batch.py` SHA-256 | `3775cbf968dc574ebdcd171a123bf381af75c4dfeff10a42e08a722c917c702f` | `3775cbf968dc574ebdcd171a123bf381af75c4dfeff10a42e08a722c917c702f` |
| `backend/tests/test_local_followup_evaluation.py` SHA-256 | `5496407b44bdd0e493ae23e75a12ae2fc0647d0b7b3066ccb4807b261cdfe4d1` | `5496407b44bdd0e493ae23e75a12ae2fc0647d0b7b3066ccb4807b261cdfe4d1` |

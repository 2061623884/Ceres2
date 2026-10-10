# `report_batch` status/deadline/unannotated GREEN

The single test requested after the corresponding RED passed.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py::test_report_cli_separates_run_status_critical_deadline_and_unannotated_usefulness
```

Result: exit 0, **1 passed in 0.52s**. The same expected pytest warning appears because plugin autoload is disabled. Raw output: [`report-cli-status-green.log`](report-cli-status-green.log).

| Item | SHA-256 |
|---|---|
| `git rev-parse HEAD` before and after | `e855d691d0a446c9e5385196134b55f2ec609320` |
| `backend/app/evaluation/report_batch.py` | `13964592964aae8d10f532da73fab5a9038c2bf563039c09587e387fb74a8b61` |
| `backend/tests/test_local_followup_evaluation.py` | `4768f8d7ec4a0ecead9a875fc61a657b8f5d59a72aeffe8fe6b21a5869955df2` |

# Amount mismatch with partial line details RED

This is the isolated second RED requested by the review-fix owner after reordering the existing amount CLI test. The first RED in [`amount-delta-red.md`](amount-delta-red.md) is preserved.

Command from `backend/`:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest tests/test_local_followup_evaluation.py::test_score_batch_cli_checks_plan_and_confirmed_cart_amounts -q
```

Result: exit 1, one failed test in 0.64s. The partial-line case has `line_total_fen=600` and `selected_total_fen=601`, while quantity and unit price are absent. The scorer returned `business_verdict='unknown'` rather than emitting the checkable selected-total mismatch as a failure:

```text
tests/test_local_followup_evaluation.py:1441
assert 'unknown' == 'fail'
```

Raw output: [`amount-delta-partial-total-red.log`](amount-delta-partial-total-red.log).

| Item | Before | After |
|---|---|---|
| `git rev-parse HEAD` | `4e021e46e8c16671ae1366ec09c11f39bad01bd6` | `4e021e46e8c16671ae1366ec09c11f39bad01bd6` |
| `backend/app/evaluation/score_batch.py` SHA-256 | `20e27571e8f65b08560275a3bc066302c14eb0a7dc76f038dbb203ab474d8ca7` | `20e27571e8f65b08560275a3bc066302c14eb0a7dc76f038dbb203ab474d8ca7` |
| `backend/tests/test_local_followup_evaluation.py` SHA-256 | `4f218062ff96fcd87c01da59d61bd83b2a9c9dd3aadeda5a20fdbffb6208dbe7` | `4f218062ff96fcd87c01da59d61bd83b2a9c9dd3aadeda5a20fdbffb6208dbe7` |

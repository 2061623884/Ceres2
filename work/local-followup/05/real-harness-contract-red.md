# Real harness contract RED

This record covers only the new public synthetic harness module. The test created synthetic JSON/environment values and a temporary copy of `graph_audit.py`; it did not read the original `.env`, ignored run output, private acceptance cases, or real batch, and it did not call a model/provider or live HTTP/server.

## Execution

Git HEAD: `fbb44854a412da8d77a7ec30426d240756a9d261`.

Working directory: `backend/`.

Command:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_real_harness.py
```

Exit code: 1. Result: `4 failed, 1 passed, 1 warning in 0.53s`. The warning was pytest's `Unknown config option: asyncio_mode` after plugin autoload was disabled.

SHA-256 values at execution:

- Test `backend/tests/test_local_followup_real_harness.py`: `e68821eab29d685e70f55b690b434e206218a3876a53ebc33b7b457cd35c42a3`
- `work/local-followup/04/real-model-20261008/provider_job.py`: `21a6351a5160fb1426740cc8812099d981341836efd031e8357831f44aeee248`
- `work/local-followup/04/real-model-20261008/graph_audit.py`: `2bdcf70088bdb0d134d0ac7275a0915126d94270c598fb702ee18962274da6e4`

Raw pytest output: `work/local-followup/05/tmp/real-harness-contract-red.log`, SHA-256 `f33946e8814cb6f71f9a843de31a36d1d978f9eb50260d90fc6a9efe65016ebf`. It is in the ignored `work/**/tmp/` path.

## First observed failure in each failing test

1. `test_provider_call_summary_keeps_unobserved_unknown_and_actual_zero_distinct`: `_call_summary(None)` returned `count=0`, `kind_status={}` and `provider_total_tokens_by_model={}`; the contract expects these to remain `None` when calls were not observed. The later checks for unknown usage (`None`/empty usage) and actual zero usage did not execute after this first assertion failure, so their behavior is not established by this run.
2. `test_graph_audit_keeps_unobserved_failure_unknown_instead_of_zero`: a synthetic `graph_status=not_executed` / `KNOWLEDGE_TIMEOUT` record produced `query_wall_ms=0.0`; the first assertion expects `None`. Remaining canonical-fact/scope/ingredient unknown assertions did not execute.
3. `test_graph_audit_does_not_default_missing_success_facts_to_empty`: a synthetic success record without `canonical_facts` exited 0, while the contract expects the audit CLI to reject missing success facts. This confirms missing facts are currently accepted as an empty result.
4. `test_provider_serve_drops_inherited_operator_settings_before_settings_load`: with synthetic host environment values, Settings still observed `operator_token_configured=true`, `shopping_writes_paused=true`, and `kev_configured=true`, where the test requires these inherited operator fields to be cleared. The expected HOME, HTTP_PROXY and isolated synthetic database path matched. The test restores the original process environment in `finally`.

The passing test was `test_graph_audit_keeps_observed_empty_success_as_zero_and_evaluates_it`; its synthetic observed empty success remained distinguishable from unobserved/failure state. These are RED findings only; no source or test file was changed during this run.

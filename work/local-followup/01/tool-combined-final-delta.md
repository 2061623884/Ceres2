# Final amount-delta combined test group

Status: **passed**. This is the current combined verification after the two amount-delta fixes: selected totals are checked using known line amounts even with missing quantity/unit or Offer evidence, and a receipt/body mismatch does not suppress independent cart money checks.

## Command and result

Working directory: `backend/`. The actual `HOME` was inherited unchanged. The command used the worktree Node 22 loopback-guard wrapper, Python loopback guard, task-local `TMPDIR`, and disabled pytest plugin autoload:

```text
PATH=<worktree Node 22 loopback-guard wrapper>:/home/amax/.nvm/versions/node/v22.19.0/bin:/usr/bin:/bin
PYTHONPATH=<worktree loopback-only Python guard>
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
TMPDIR=<worktree task temp directory>
../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py tests/test_local_followup_baseline.py tests/test_local_followup_app.py
```

Exit 0: **29 passed, 1 warning in 15.73s**. The warning is `Unknown config option: asyncio_mode` because plugin autoload was disabled. Raw output: [`tool-combined-final-delta.log`](tool-combined-final-delta.log), SHA-256 `663550ec777cb7978d6af9552c6f8f3ae55814a95a888f69a9c6bd9190438b83`.

## Source provenance

The pre-run manifest covers 213 files under `backend/app`, `backend/tests`, `backend/data/fixtures`, and `runtime/pi/src`, plus the public dev case set and rubric. [`tool-combined-final-delta-source.sha256`](tool-combined-final-delta-source.sha256) has SHA-256 `8d3724cba223fb46bc46eb198aaf3a378c2096e1e930b4648fda6f5ee1b6aa1a`; post-run verification confirmed it was unchanged.

| Source | SHA-256 |
|---|---|
| `backend/app/evaluation/report_batch.py` | `59415a08949e4cbab7b86c4f6b28d4fc907f90c95a5126268019934bb7f175e5` |
| `backend/app/evaluation/score_batch.py` | `cb255c4f6cdbe211dbad04d4425be77e14383da2f9080da44b9db50f068efb07` |
| `backend/app/evaluation/batch_runs.py` | `4d1bba5c7d7c3b497c2914c6177a88bc121ca0f7d914572846c1210f49c22172` |
| `backend/app/evaluation/compare_runs.py` | `0e954a1ce35890a834a225215a03da82cd14ee16ab07f6c2606d8d3cbaf1ad25` |
| `backend/app/evaluation/failure_intake.py` | `116edc72bb54f0d76b31dbefa47838e43fc80f1ee048640988360393dbc49727` |
| `backend/tests/test_local_followup_evaluation.py` | `4f218062ff96fcd87c01da59d61bd83b2a9c9dd3aadeda5a20fdbffb6208dbe7` |
| `backend/tests/test_local_followup_baseline.py` | `0d0b7d9f3ccc4323fc0bc60a0616a3b57d443f8dfba83564b184c1a1b09e4dff` |
| `backend/tests/test_local_followup_app.py` | `cc5b310f81252772aaf19396b007043e6ad942ad97932ae545c019af68b5ccd8` |
| `evals/ceres2-local-followup-rubric.md` | `86294a2d79289e75ec49181142283d6d66b716698bea51e4f10d70c65722e1b8` |

Checkout `HEAD` is `4e021e46e8c16671ae1366ec09c11f39bad01bd6`. A read-only diff against base `170fac0bc75fcc855897b073337ba218abeb5b7d`, excluding `backend/app/evaluation/**`, found no non-evaluation product changes under `backend/app`, `runtime/pi`, `frontend`, or `backend/data/fixtures`. Evaluation and test changes remain separately scoped. No real provider, external model, product `.env`, or prior runtime data was used.

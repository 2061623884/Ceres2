# Public baseline CLI → controlled FastAPI/Pi smoke

Status: **passed, one controlled public case**. This is a local integration smoke against a real FastAPI TCP listener and the real `run_baseline` CLI, with a deterministic loopback Pi-compatible model fixture. It is not a real-provider or production-service test.

## Command and result

From `backend/`, the test ran with an empty inherited environment, the worktree's independent `.venv`, Node 22.19.0 and its loopback-only Node guard, plus the Python loopback socket guard:

```text
env -i PATH=<worktree loopback Node wrapper>:<Node 22.19.0>:/usr/bin:/bin HOME=<worktree temp> TMPDIR=<worktree temp> PYTHONPATH=<loopback-only guard> PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_app.py
```

Result: exit 0, **1 passed in 3.50s**, with one pytest warning because plugin autoload was disabled and the repository's `asyncio_mode` option therefore had no plugin consumer. Raw output: [`app-controlled-http-smoke.log`](app-controlled-http-smoke.log), SHA-256 `71385216e71a37cba86916db09073b5b9cc675e904a43153dfeb8f891218343d`.

## What this exercised

The public batch CLI launched as a subprocess and called a fixture-backed FastAPI app over an ephemeral `127.0.0.1` TCP port. The app used a fresh temporary SQLite database, `seed_catalog`, dependency overrides for that database, and Uvicorn with lifespan disabled. One public case, “帮我选可乐包装,” made exactly one HTTP request to the deterministic controlled model (`controlled-pi`) and ended in `waiting_clarification` with the packaging question. The captured row retained `request_id=public-cola-packaging:trial:1`, a newly allocated owner/session, and runtime version metadata. Public bootstrap and session reads matched the captured owner/session; the receipt was readable and the cart remained empty.

The controlled model request was observed to contain the user's current query. No real provider, external API, paid call, Graph build, or product `.env` was used. The fixture supplies only its own loopback model endpoint and temporary database configuration.

## Cleanup and provenance

The test's `finally` path requests Uvicorn shutdown, joins its owned thread, and closes the listener. The shared `pi_client` fixture then stops any owned in-flight receipt, closes the TestClient, clears FastAPI dependency overrides, shuts down and closes its loopback model server, disposes its temporary engine, and clears cached settings. `tmp_path` owns the test database and case/output files.

| Source | SHA-256 |
|---|---|
| `backend/tests/test_local_followup_app.py` | `cc5b310f81252772aaf19396b007043e6ad942ad97932ae545c019af68b5ccd8` |
| `backend/tests/test_runtime_pi_product_query.py` (controlled model fixture) | `39eeaf5e13df83be7385d5fc4700a490dd68c814e44598ec9bbab4345186adf1` |
| `backend/app/evaluation/run_baseline.py` | `cdda0026e00531cff82cfb1fdd0559d067d1184610055d207fadf46cf7e52b29` |
| worktree Node 22 guarded wrapper | `f05a442273aa056822a31b3ac6cd63265b25bd40e10a38b4126ed1442faac1c2` |
| loopback-only Python guard | `3487ab8ef2e5d61e827efe58250673ff057621c1634be4a32525ac930afcb29b` |

The raw test log is the only captured execution output; generated database and case files were confined to pytest temporary storage.

# Review-fix final combined test group

Status: **passed**. This run validates the frozen evaluation tools together with the public baseline runner and controlled FastAPI/Pi integration smoke after the review fixes. It does not rerun the separate 18-minute product suite or Node/frontend builds.

## Command and result

Working directory: `backend/`. The actual process `HOME` was inherited unchanged; only worktree `TMPDIR`, Node 22 guard path, Python loopback guard, and pytest plugin-autoload setting were supplied:

```text
PATH=<worktree Node 22 loopback-guard wrapper>:/home/amax/.nvm/versions/node/v22.19.0/bin:/usr/bin:/bin
PYTHONPATH=<worktree loopback-only Python guard>
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
TMPDIR=<worktree task temp directory>
../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py tests/test_local_followup_baseline.py tests/test_local_followup_app.py
```

Exit 0: **29 passed, 1 warning in 16.27s**. The warning is `Unknown config option: asyncio_mode`, because pytest plugin autoload was disabled. Raw output: [`tool-combined-reviewfix-final.log`](../01/tool-combined-reviewfix-final.log), SHA-256 `ff78b06bfe5cfd8b1285f05aa8a24bcfed498a3409df0d9d62d6b77d30b39138`.

## Source provenance and scope

The pre-run manifest covers 213 files under `backend/app`, `backend/tests`, `backend/data/fixtures`, and `runtime/pi/src`, plus the public dev case set and rubric. [`tool-combined-reviewfix-source.sha256`](../01/tool-combined-reviewfix-source.sha256) has SHA-256 `982074bc3816b38f05ed897fde1c46a133ff530aed7844571327665f3ac08d86`; a post-run recomputation matched it exactly.

| Source | SHA-256 |
|---|---|
| `backend/app/evaluation/report_batch.py` | `59415a08949e4cbab7b86c4f6b28d4fc907f90c95a5126268019934bb7f175e5` |
| `backend/app/evaluation/score_batch.py` | `d23c444d099bdacd309bc673c37b2c4579f2759ad9e48eb45b03caa9bccf64bd` |
| `backend/app/evaluation/batch_runs.py` | `4d1bba5c7d7c3b497c2914c6177a88bc121ca0f7d914572846c1210f49c22172` |
| `backend/app/evaluation/compare_runs.py` | `0e954a1ce35890a834a225215a03da82cd14ee16ab07f6c2606d8d3cbaf1ad25` |
| `backend/app/evaluation/failure_intake.py` | `116edc72bb54f0d76b31dbefa47838e43fc80f1ee048640988360393dbc49727` |
| `backend/tests/test_local_followup_evaluation.py` | `2c65a9b91eb9b71167818c232f028465620d4dbf4ce7dab93fe85d146363b066` |
| `backend/tests/test_local_followup_baseline.py` | `0d0b7d9f3ccc4323fc0bc60a0616a3b57d443f8dfba83564b184c1a1b09e4dff` |
| `backend/tests/test_local_followup_app.py` | `cc5b310f81252772aaf19396b007043e6ad942ad97932ae545c019af68b5ccd8` |
| `evals/ceres2-local-followup-rubric.md` | `86294a2d79289e75ec49181142283d6d66b716698bea51e4f10d70c65722e1b8` |

The checkout is at `e855d691d0a446c9e5385196134b55f2ec609320`. A targeted read-only comparison against `170fac0bc75fcc855897b073337ba218abeb5b7d`, excluding `backend/app/evaluation/**` and excluding the added evaluation test files from the product scope, found no changes in non-evaluation product code under `backend/app`, `runtime/pi`, `frontend`, or `backend/data/fixtures`. Relative to 170, the added paths are the evaluation tools and three new test modules. No real provider, external model, product `.env`, or prior runtime data was used.

# Review-fix final combined test group, current source

Status: **passed**. This run follows the additional no-Offer selected-total RED/GREEN and validates the complete current evaluation workflow modules with the public baseline runner and controlled FastAPI/Pi smoke. It does not rerun the separate product full suite or Node/frontend builds.

## Command and result

Working directory: `backend/`. Actual `HOME` was inherited unchanged. The command used the worktree's Node 22 loopback-guard wrapper, Python loopback guard, task-local `TMPDIR`, and disabled pytest plugin autoload:

```text
PATH=<worktree Node 22 loopback-guard wrapper>:/home/amax/.nvm/versions/node/v22.19.0/bin:/usr/bin:/bin
PYTHONPATH=<worktree loopback-only Python guard>
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
TMPDIR=<worktree task temp directory>
../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py tests/test_local_followup_baseline.py tests/test_local_followup_app.py
```

Exit 0: **29 passed, 1 warning in 15.87s**. The warning is `Unknown config option: asyncio_mode` because plugin autoload was disabled. Raw output: [`tool-combined-reviewfix-final.log`](tool-combined-reviewfix-final.log), SHA-256 `1b6b37ee375988cbacd8970b800447fe1d920e9dde72ef56e4a6b6c8f1600ad7`.

## Source provenance and scope

The pre-run manifest covers 213 files under `backend/app`, `backend/tests`, `backend/data/fixtures`, and `runtime/pi/src`, plus the public dev case set and rubric. [`tool-combined-reviewfix-final-source.sha256`](tool-combined-reviewfix-final-source.sha256) has SHA-256 `29bdaf543db8b498dc30adb9deab2da14c8eeaac9bcaf456cc0612f71716ae91`; a post-run recomputation matched it exactly.

| Source | SHA-256 |
|---|---|
| `backend/app/evaluation/report_batch.py` | `59415a08949e4cbab7b86c4f6b28d4fc907f90c95a5126268019934bb7f175e5` |
| `backend/app/evaluation/score_batch.py` | `20e27571e8f65b08560275a3bc066302c14eb0a7dc76f038dbb203ab474d8ca7` |
| `backend/app/evaluation/batch_runs.py` | `4d1bba5c7d7c3b497c2914c6177a88bc121ca0f7d914572846c1210f49c22172` |
| `backend/app/evaluation/compare_runs.py` | `0e954a1ce35890a834a225215a03da82cd14ee16ab07f6c2606d8d3cbaf1ad25` |
| `backend/app/evaluation/failure_intake.py` | `116edc72bb54f0d76b31dbefa47838e43fc80f1ee048640988360393dbc49727` |
| `backend/tests/test_local_followup_evaluation.py` | `feb81d04da98101ea355e9a4b129a241d86dba91f70484fed1df1f940e77ccf3` |
| `backend/tests/test_local_followup_baseline.py` | `0d0b7d9f3ccc4323fc0bc60a0616a3b57d443f8dfba83564b184c1a1b09e4dff` |
| `backend/tests/test_local_followup_app.py` | `cc5b310f81252772aaf19396b007043e6ad942ad97932ae545c019af68b5ccd8` |
| `evals/ceres2-local-followup-rubric.md` | `86294a2d79289e75ec49181142283d6d66b716698bea51e4f10d70c65722e1b8` |

Checkout `HEAD` remains `e855d691d0a446c9e5385196134b55f2ec609320`. A read-only diff against base `170fac0bc75fcc855897b073337ba218abeb5b7d`, excluding `backend/app/evaluation/**`, found no change in non-evaluation product source under `backend/app`, `runtime/pi`, `frontend`, or `backend/data/fixtures`. Added tests and evaluation tools remain in their separate scope. No real provider, external model, product `.env`, or prior runtime data was used.

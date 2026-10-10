# Combined evaluation, baseline-runner, and app smoke

Status: **passed**. This was the requested single-process pytest run across the three current public test modules; no 18-minute product-suite rerun was performed.

## Command and result

Working directory: `backend/`.

```text
PATH=<worktree Node 22 loopback-guard wrapper>:/home/amax/.nvm/versions/node/v22.19.0/bin:/usr/bin:/bin
PYTHONPATH=<worktree loopback-only Python guard>
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
HOME=<worktree temporary directory>
TMPDIR=<worktree temporary directory>
../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py tests/test_local_followup_baseline.py tests/test_local_followup_app.py
```

Exit 0: **26 passed, 1 warning in 15.06s**. The warning is pytest's expected `Unknown config option: asyncio_mode` because plugin autoload was disabled. Raw output: [`tool-combined-final.log`](tool-combined-final.log), SHA-256 `d60352bc3fd517eb141e175955fea6a256052c912a43867ebfc94bde663a4ef9`.

The isolated environment uses the worktree Node 22 wrapper and Python loopback guard. `backend/tests/conftest.py` disables dotenv loading and replaces inherited provider/database settings with controlled values before app imports. Test-owned model and API servers use loopback; the app case uses a temporary SQLite DB. No real `.env`, provider, external model, or old runtime data was used.

## Frozen source and scope

The pre-run SHA manifest covers 213 source/fixture files under `backend/app`, `backend/tests`, `backend/data/fixtures`, `runtime/pi/src`, plus the public dev case set and rubric. Manifest: [`tool-combined-current-source.sha256`](tool-combined-current-source.sha256), SHA-256 `7032e79c8b31ce1d830452f48cf9246bb0e2812c7fb5f02d584a22e3ea8fcaf9`.

Relevant direct hashes:

| Source | SHA-256 |
|---|---|
| `backend/tests/test_local_followup_evaluation.py` | `8947ae2405f46936400cbf9a3899a7e9e22f600e09a3ecb1b475274d52260e10` |
| `backend/tests/test_local_followup_baseline.py` | `0d0b7d9f3ccc4323fc0bc60a0616a3b57d443f8dfba83564b184c1a1b09e4dff` |
| `backend/tests/test_local_followup_app.py` | `cc5b310f81252772aaf19396b007043e6ad942ad97932ae545c019af68b5ccd8` |
| `backend/app/evaluation/run_baseline.py` | `cdda0026e00531cff82cfb1fdd0559d067d1184610055d207fadf46cf7e52b29` |
| `evals/ceres2-local-followup-dev.json` | `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d` |
| `evals/ceres2-local-followup-rubric.md` | `2c115e4fc4131892bbb01f6e3417e5b25f93c697e06aac1209f46eecdf3a829e` |

The checkout remains at `170fac0bc75fcc855897b073337ba218abeb5b7d`. A read-only tracked diff check against 170 for `backend/app` excluding `backend/app/evaluation`, `backend/tests`, `runtime/pi`, `frontend`, and `backend/data/fixtures` returned empty (exit 0). Current additions are confined to evaluation modules and the three new local-followup test files; non-evaluation product source remains unchanged. This result does not replace or rewrite the separate 170 baseline full-suite result (752 passed, 4 failed); those environment-related failures and their targeted follow-up evidence remain documented in [`product-baseline-170-full.md`](product-baseline-170-full.md).

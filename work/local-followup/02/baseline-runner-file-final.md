# run_baseline module regression GREEN

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py`
- Result: exit 0; all 7 tests passed in 5.68s.
- Test source SHA-256: `0d0b7d9f3ccc4323fc0bc60a0616a3b57d443f8dfba83564b184c1a1b09e4dff`.
- Runner SHA-256 (`backend/app/evaluation/run_baseline.py`): `cdda0026e00531cff82cfb1fdd0559d067d1184610055d207fadf46cf7e52b29`.
- This includes multi-capture request filtering, supported follow-up confirmation/idempotent replay, core repeat/resume accounting, and preflight rejection of unsupported operations. Test-owned loopback fixtures cleaned up; no live provider/service was used.
- Raw pytest output: [baseline-runner-file-final.log](baseline-runner-file-final.log), SHA-256 `9314cfe98ec05e765dd4b514999b8e13cbef3cbcd4debc3afc662117d0077caa`.

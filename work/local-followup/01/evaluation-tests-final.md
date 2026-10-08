# Final local-followup evaluation test module

- Command: `cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py`
- Result: exit 0; all 18 tests passed in 3.64s.
- The exact pre-run source manifest is [current-evaluation-source-freeze.sha256](current-evaluation-source-freeze.sha256). The test and implementation hashes remained unchanged through the run.
- Public dev case set: `ceres2-local-followup-dev-2026-10-08-v2`, SHA-256 `032bc3bc0e14c82d46e04b16ccdf0ff1a9f9fee97685a58f2aefa3902fbb674d`.
- Final source hashes: `tests/test_local_followup_evaluation.py` `8947ae2405f46936400cbf9a3899a7e9e22f600e09a3ecb1b475274d52260e10`; `annotate_batch.py` `0e44aecfeceba5ae1c49c6f10bd2bd4e08d327c6ed5e61ac9f5bdf27a9ef46bf`; `batch_runs.py` `1c4de1bdbbe155385bdfe1c8e45d399aca2193cc388b05b8d5c11d6750d45f82`; `compare_runs.py` `1313a91318d644ee92e8e0a55e193df383e2b7a217a24344bf52ad789d68c430`; `failure_intake.py` `ebe4029805a504a75ec04e9534910c8f55598ea2b7b717ac444bf373ebec8de6`; `report_batch.py` `3775cbf968dc574ebdcd171a123bf381af75c4dfeff10a42e08a722c917c702f`; `run_baseline.py` `cdda0026e00531cff82cfb1fdd0559d067d1184610055d207fadf46cf7e52b29`; `score_batch.py` `464c7130ed8e8f13287b88b41e8ca8572d344b6381e79445061e76bc2c973e9a`.
- Raw pytest output: [evaluation-tests-final.log](evaluation-tests-final.log), SHA-256 `6225a018091d4e18bfdd49eaa1767c17d8df79715036706f1f42e98df5201556`.
- Tests use synthetic/temporary data and no live provider, model, database, or service.

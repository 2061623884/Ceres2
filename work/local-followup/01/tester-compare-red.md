# compare_runs CLI RED

- Command: `(cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k compare)`
- Pytest result: exit 1; 1 selected test failed, 0 passed.
- Test: `test_compare_cli_pairs_public_cases_and_keeps_unreviewed_quality_unknown`.
- Frozen test source SHA-256: `664acc435a303254f709fa79d5cbfecc1241172b81e9415a6f17d169ee8b691f`.
- Root cause: the CLI subprocess exits 1 because Python cannot import `app.evaluation.compare_runs` (`No module named app.evaluation.compare_runs`). The test reached its assertion; no configuration guard or live provider failure occurred.
- Raw pytest output is retained in the ignored sibling `compare-red.log` (SHA-256 `3d4aec074cc394eb77671ef3049bbb12705810bc62552bab1944682cb7318408`).
- No source, lock, configuration, or test file was changed. No build, API, server, model, or other pytest command was run.

# compare_runs batch-v1 CLI GREEN

- Command: `(cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_evaluation.py -k compare)`
- Pytest result: exit 0; 1 selected test passed.
- Test source SHA-256: `6bfaf1fd49d4a802076bf37329066d2cf368791484506ae50a68db1c6dd9f6de`.
- Implementation under test, `backend/app/evaluation/compare_runs.py`, SHA-256: `5dae749478c7c40321bd72071177ddc5728c9a05d4f75e90964ba3efd4d8a23d`.
- Git HEAD remained `170fac0bc75fcc855897b073337ba218abeb5b7d`, tree `295499ee22cc30485d38eba82e96330a39d7d573`; the implementation is an untracked working-tree file, not part of that tree.
- Raw pytest output is retained in the ignored sibling `compare-batch-green.log` (SHA-256 `718af798eb1450a812074f301573c1f498edd3575a2450f85ee649d7e03c3c72`).
- No other pytest, build, API, server, or model command was run; Tester changed no source or test files.

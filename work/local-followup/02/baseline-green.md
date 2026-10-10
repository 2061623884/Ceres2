# run_baseline CLI GREEN

- Command: `(cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k baseline_cli_captures_current_public_runs_without_business_confirmation)`
- Pytest result: exit 0; 1 selected test passed.
- Test source SHA-256: `b3601e1c91f2258ff1a74984123297164ff3d7142f4e467ed3c5bedda6783e07`.
- Implementation under test, `backend/app/evaluation/run_baseline.py`, SHA-256: `e86780db61afd63f8a3448b247b0317181adf73fe19cd0e8ade259122dc0138c`.
- Git HEAD/tree remained `170fac0bc75fcc855897b073337ba218abeb5b7d` / `295499ee22cc30485d38eba82e96330a39d7d573`; implementation remains an uncommitted working-tree file.
- Raw pytest output is retained in the ignored sibling `baseline-green.log` (SHA-256 `057a4f811934a7c8e0413d700e4be6b0e9bcd24fc5edea4612ed45c4e19a021e`).
- No other pytest, build, API, server, or model command was run.

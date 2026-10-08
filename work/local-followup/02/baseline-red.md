# run_baseline CLI RED

- Command: `(cd backend && ../.venv/bin/python -m pytest -q tests/test_local_followup_baseline.py -k baseline_cli_captures_current_public_runs_without_business_confirmation)`
- Pytest result: exit 1; 1 selected test failed, 0 passed.
- Test source SHA-256: `b3601e1c91f2258ff1a74984123297164ff3d7142f4e467ed3c5bedda6783e07`.
- Root cause: the CLI subprocess exits 1 because Python cannot import `app.evaluation.run_baseline` (`No module named app.evaluation.run_baseline`); the module is absent in the current working tree. The test reached its expected CLI assertion, not a loopback/server or configuration guard failure.
- The test-owned loopback fixture was shut down in its `finally` block. No provider, product API, application server, or model was called.
- Raw pytest output is retained in the ignored sibling `baseline-red.log` (SHA-256 `9c7cc05da9bc95b18de576fc1a438882bcc2c6583fb65fc13adfe3779c040c57`).
- Git HEAD/tree stayed at `170fac0bc75fcc855897b073337ba218abeb5b7d` / `295499ee22cc30485d38eba82e96330a39d7d573`. No source or test file was changed by Tester.

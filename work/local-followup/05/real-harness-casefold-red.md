# Real harness inherited-setting casefold RED

This record covers only `test_provider_serve_drops_inherited_operator_settings_before_settings_load` with a synthetic host environment. No original `.env`, ignored real output, private acceptance data, or real batch was read; no model, provider, live service, or network call was made.

Git HEAD: `fbb44854a412da8d77a7ec30426d240756a9d261`.

Working directory: `backend/`.

Command:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_real_harness.py::test_provider_serve_drops_inherited_operator_settings_before_settings_load
```

Exit code: 1. Result: `1 failed, 1 warning in 0.30s`; the warning was pytest's `Unknown config option: asyncio_mode` after disabling plugin autoload.

Source hashes at execution:

- `work/local-followup/04/real-model-20261008/harness_config.py`: `fc42454c73359ec1ca82e7936f3d5cf9c26aa3e4df0a132e0b369af74bbba1d8`
- `work/local-followup/04/real-model-20261008/provider_job.py`: `98855489dffdcc75bb3aedbfa45568384642cfaf90730475ccfea62b142d8ccc`
- `backend/tests/test_local_followup_real_harness.py`: `123b494e18903d034e47c6a6ae2fe34d094aeb13e614c968fda43d6f28f73d2c`

The test supplied uppercase and lowercase spellings of the synthetic operator token and Kev settings, plus mixed-case `Shopping_Writes_Paused`. After `provider_job.main()` the test observed all three settings still configured/true, while the expected filtered server settings were false. The expected HOME, HTTP proxy, and isolated synthetic database path matched. The test's `finally` restored the original process environment.

Full raw pytest output is at `work/local-followup/05/tmp/real-harness-casefold-red.log`, SHA-256 `c26501131f1f6e25dfad26fae9b6df32ee444e8ea952e19a969eb6413ccacc36`; it is under the ignored `work/**/tmp/` path.

# Ticket 01 controlled launcher regression

Date: 2026-10-09. This formal-workflow regression is run at the current pinned source; it does not inherit the earlier 5b24 controlled GREEN.

- HEAD: `9e9be1da8ef7dd7ba630a2025e63835612e4795e`.
- Command (cwd `backend`): `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ../.venv/bin/python -m pytest -q tests/test_local_followup_kev_launcher.py`
- Result: exit 0; `1 passed` in 3.41 seconds (4.64 seconds wall time).
- Python: 3.11.15; pytest: 9.1.1.
- Test source [`test_local_followup_kev_launcher.py`](../../../../backend/tests/test_local_followup_kev_launcher.py), SHA-256 `f676bb091aeb6f938ce359438a10199f261274ff89d0f765b70753130dab7fe6`.
- Launcher [`serve_baseline.py`](./serve_baseline.py), SHA-256 `af65cd78c7045da48d186fdedf27e9306b1a41194e71b9e351a7d6a89f7dc3d8`.

The test creates a temporary synthetic source env, fake Kev HTTP server, isolated runtime directory, and sentinel database/checkpoint files. It verifies public HTTP bootstrap/catalog, rejection of an inherited operator token, exactly one fake-Kev route call, synthetic config selection, environment secret sentinels absent from child output, and unchanged sentinel files. The fixture closes the fake server/thread and child process in `finally`. This did not use the approved `.env`, live Kev, DeepSeek, the 8017 service, or any existing DB/checkpoint.

Pytest emitted one non-failing warning: project config key `asyncio_mode` is unknown to the installed pytest (`PytestConfigWarning`); this test passed without loading external plugins.

## Bounded live-service and pin check

After the controlled test, without restarting or stopping anything:

- `GET http://127.0.0.1:8017/health`: HTTP 200, `business_data_mode=demo`, `llm_configured=true`.
- `GET http://127.0.0.1:8009/v1/models`: HTTP 200; `kev-latest` and `jev-latest` cards retained a `batches` object with numeric `count`, `requests`, and `queued` fields. This is metadata readiness only; no inference was sent.
- The 8017 process remains in exec session `78420`. The existing 8009 Kev process was not touched.
- The running 8017 service is the same process previously launched with the approved `deepseek-flash` selection; this regression neither re-read `.env` nor invoked the primary provider.
- Frozen data/index/source SHA-256: policies `7a370431a1a9c2df2b818218f3c54cb01946f93fa027aad44021dd1637f10502`; hybrid index `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`; GraphRAG manifest `3aad90d9d498e614ddd30799275881c5fc53b9f45c1dbba5fc62eb067cdb3787`; `kev_provider.py` `5059a7e61dda6590b57c17532fb96f6907db6b5c40ab213c728964bdba824566`; `navigation_service.py` `0baa40f74f73a72f1f0ccc8eed5003acaba25ca0e71ff501458886a78892c0ce`.
- No `backend/`, `frontend/`, or `runtime/` source diff was present after the check.

One hash-collection command was first issued with worktree-root-relative paths while cwd was `backend`, so those paths were not found. The command was rerun successfully from the worktree root; no source, database, or service state changed.

This controlled regression plus the route/API/policy/browser evidence in [the 01 results report](./KEV-NAVIGATION-POLICY-RESULTS.md) is ready for the root to assess as the ticket 01 technical gate. It is not authorization to start the formal 100-run baseline.

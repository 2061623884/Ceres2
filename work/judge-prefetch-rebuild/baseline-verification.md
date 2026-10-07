# Fresh cloud rebuild baseline

This is new controlled evidence for public Ceres2 main `4bed9c891261e382122d424825b649989ea92c92`, branch `ceres2/judge-prefetch-rebuild-20261007`. No historical pass count is inherited. The dedicated Tester executed every install, build, typecheck and test below on 2026-10-07.

## Environment and dependencies

- Python 3.12.14, Node 24.19.0, npm 11.9.0.
- Created independent `backend/.venv`; installed all 62 packages from `backend/requirements.lock` using the official PyPI registry.
- `runtime/pi` and `frontend` each received their own `npm ci` from the official npm registry and existing package lock. Neither lock nor manifest changed.
- Dependency compatibility: `uv pip check --python backend/.venv/bin/python` passed.
- An initial uv invocation could not create its default cache in the read-only home directory. Retrying with a new cache inside the task's ignored temporary directory succeeded. This was an environment setup issue, not a product failure.
- Dependencies, caches and compiled output are ignored. No existing environment, database, provider credential or live script was used.

## New checks

The raw `evidence/` paths below identify locally retained execution records and logs. They are not included in the planning checkpoint or promised as files in a public checkout; this committed summary records their observed outcomes.

| Check | Result | Raw evidence |
| --- | --- | --- |
| Python installed dependency compatibility | Passed | `evidence/baseline-python-dependencies/` |
| Pi runtime `npm run typecheck && npm run build` | Passed | `evidence/baseline-pi-build/` |
| Preserved frontend `npm run build && ./node_modules/.bin/tsc --noEmit` | Passed | `evidence/baseline-frontend-build/` |
| Controlled configuration isolation and foundation HTTP tests | 5 passed in 4.20 s | `evidence/baseline-http-isolation/` |
| Actual Pi SDK loopback product query and actual Momo/LangGraph SDK HTTP contract | 2 passed in 3.15 s | `evidence/baseline-pi-momo-wire/` |

The two runtime smoke node IDs were `test_runtime_pi_product_query.py::test_product_query_uses_pi_search_then_details_and_persists_grounded_reply` and `test_mercury_wire.py::test_public_query_uses_installed_sdk_http_tool_contract`.

Every check captured source hashes before and after execution and observed no source change during the run. The task-local `run_check.py` captures commands, return codes, elapsed time and exact source hashes for subsequent red/green runs, including newly authored untracked tests.

## Isolation and limits

The runner uses a sanitized child environment, synthetic fixture keys, memory/temporary databases, and loopback provider fixtures. Python and Node execution guards deny dotenv reads and non-loopback socket connections. Existing pytest configuration disables dotenv before application settings instantiate. The isolation regression independently verifies collection-time configuration protection. The actual SDKs execute against deterministic HTTP fixtures; this is not real-provider or language-quality acceptance.

The frontend build emits the existing Vite future-native-config warning about `__dirname` and JSON import attributes; it still builds and passes strict TypeScript. No lint script is configured, so lint is not claimed as passed.

This is limited baseline readiness, not full regression, browser DOM, real browser, live-provider, independent holdout or user acceptance. No product or frontend source was modified by the Tester. Full candidate checks will follow the approved vertical slices.

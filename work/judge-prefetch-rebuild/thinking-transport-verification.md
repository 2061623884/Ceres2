# Official-host transport: controlled verification

Dedicated Tester verification date: 2026-10-07. Frozen source is the six-file change below on base commit `016680a3930b0aa27a29d3cb3276e653cb32d1e0` in branch `ceres2/judge-prefetch-thinking-transport-20261007`. This is a bounded transport-support milestone, not completion of tickets 01–04.

## Scope and outcome

- Official `api.deepseek.com` and uppercase-normalized official hostnames send `thinking: {type: disabled}`.
- Ordinary providers and suffix look-alikes omit both `thinking` and `reasoning_effort`; absence is checked separately from null.
- Checked five actual request paths: Momo, memory extraction, Dream, result-expression generation and its validator. Python tests retain the installed OpenAI SDK and real LangGraph; Node expression tests retain the actual Pi SDK and loopback HTTP/SSE.
- Existing model identities, temperature, response-format/tool/stream behavior, retry/timeout settings, and existing expression 512/256 limits are checked. Fixture-reported usage is preserved; no live-provider usage or cost is claimed.
- `runtime/pi/src/worker.ts` is unchanged. Main Pi worker and main Pi validator integration/verification remain pending with the ticket 01 owner. These results do not approve those paths.

## TDD evidence

| Capture | Observed outcome |
| --- | --- |
| `thinking-red-01` | Momo: 2 expected missing-thinking failures, 2 nonofficial-host passes |
| `thinking-green-01` | 4 Momo cases + 2 provider regressions: 6 passed |
| `thinking-red-02` | Extraction/Dream: 4 expected missing-thinking failures, 4 nonofficial-host passes |
| `thinking-green-02` | Momo/memory cases + provider regression: 14 passed |
| `thinking-red-03` | Expression/validator: 2 expected missing-thinking failures, 2 nonofficial-host passes; SDK completed against loopback before behavioral assertion |
| `thinking-build-green-03` | Pi typecheck and build passed |
| `thinking-green-03` | All 16 dedicated wire cases + 2 provider regressions: 18 passed in 5.13 s |
| `thinking-regression-03` | 12 related expression/diagnostic/memory-model tests passed in 16.42 s |

Final focused command: `backend/.venv/bin/python -m pytest -p pytest_asyncio.plugin -q tests/test_official_deepseek_thinking.py tests/test_mercury_provider.py`, run from backend through the task-local safety/capture runner. Regression modules: `test_next_expression_public.py`, `test_final_review_expression_diagnostics_public.py`, `test_memory_background_models.py`.

The final build, focused test and broader regression records contain identical before/after source maps, and all current source bytes were independently compared with those records before this report. No source changed during any recorded final run.

## Frozen changed-source manifest

| File | SHA-256 |
| --- | --- |
| `backend/app/core/deepseek_request.py` | `c3214d44a832aec1c1df7ca1c456da3cb6ff904c2b839dc94777cdab23dd8191` |
| `backend/app/mercury/provider.py` | `b80df9bfcf4196028e3ea3a1f939afaa882d33b9a9dd354be560a513801ed2f1` |
| `backend/app/services/memory_model.py` | `6a1e059e8c78c52e8dfdcb6e7ce8b7417db8fba48fbc097eb431866044ae90d2` |
| `backend/tests/test_official_deepseek_thinking.py` | `023713219268a5bef0ca0c8c09a96a622f828a9900b26fc0e0e3435713c25f6f` |
| `runtime/pi/src/official-deepseek.ts` | `62613e886f354907be25384f437017a04258e5f7065f285b8ea9bced6937e367` |
| `runtime/pi/src/result-expression.ts` | `bc3c749af20ba99eb90d91ed18569d187c22be52c8cb0a1e007ef9aef49e43b3` |

## Isolation and retained limits

All installs used independent per-worktree environments from the current rebuild's official-registry download caches. Fake keys, temporary databases and deterministic provider-boundary fixtures were used. No real dotenv, credential, external provider request, historical database, archive/reference runtime dependency, model change or new output budget was used.

The expression RED fixture initially supplied its own minimal child environment and origin-checked loopback fetch redirect. Before GREEN it was tightened to preserve the independent runner's Node dotenv/socket guard as well; behavioral assertions were unchanged. This harness correction is retained in the source hash above.

Raw `evidence/<capture>/output.log`, `record.json` and applicable `source.patch` files are retained locally, not included in this small public milestone report. Full regression, main Pi integration, independent Standards/Spec review, real-provider quality/performance, browser compatibility and user acceptance are not claimed by this report. The source freeze remains in effect until the integration owner commits the exact allowlisted files.

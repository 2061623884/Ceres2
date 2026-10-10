# Final core candidate: controlled whole-phase verification

Dedicated Tester, 2026-10-07. **All 558 backend tests passed on one committed final core candidate.** Pi typecheck/build, exact locked dependencies and three guard/isolation regressions also passed. This closes the controlled backend/runtime verification gate for the combined 01–03 changes. Frontend/browser, real-provider and user acceptance remain separate.

## Frozen identity

- Commit: `d6a40886926bf203b53c52db27d2177b1b3dcb80`; tree `2fad3a1c8e74593dc19ee929211be0d35a323938`.
- Dedicated worktree: `04-core-verification`, branch `ceres2/judge-prefetch-04-core-20261007`.
- No uncommitted product/test changes; the source patch is empty. All **248** source-file hashes equal the accepted repaired 03 snapshot and both final Standards/Spec re-review pins.
- Manifest SHA-256: `7c86cf268f5f4d7055626d6db1e3970d23735bd313ed148f638ede0a02c4368f`.
- [Source, harness, build and check audit](04-core-final-source.json) includes exact commands, source and harness maps, each launcher's before/after digest, child guard counts, review pins, and raw output/record hashes. [Five-capture history](04-core-verification-history.json) preserves setup and all final gates.
- The unfinished comparison-runner CLI, tests and docs were excluded from this worktree and harness fingerprint. Their controlled tests and acceptance are separate.

## Final gates

| Capture | Command/scope | Result |
| --- | --- | --- |
| `04-independent-offline-install` | Fresh local Python environment and Pi package directory, official cached locked packages | Exit 0; 62 Python / 87 npm packages |
| `04-final-dependencies` | `uv pip check`, exact installed Python versions against requirements.lock, Pi `npm ls --depth=0` | Exit 0; all 62 versions match; compatible |
| `04-final-pi-build` | `npm run typecheck && npm run build` | Exit 0; 7.137 s |
| `04-final-guard-proof` | Two task-local actual-child/transport guard tests and backend isolation test | **3 passed**, 4.13 s pytest / 5.566 s capture |
| `04-final-backend-full` | In backend: `.venv/bin/python -m pytest -p pytest_asyncio.plugin -q` | **558 passed**, 738.36 s pytest / 756.438 s capture |

The full backend command has no selections or exclusions. It includes all 34 ticket 03 cases, the 44 ticket 02 policy cases and the backend regressions from the 152-case final 03 focused run. Those overlapping counts are not added to 558. The two task-local guard tests are outside backend/tests; the backend isolation test overlaps the full suite.

All five captures have identical source/harness before and after, and the final worktree still matches. No full 03 suite was duplicated. The earlier 151-case pre-accounting checkpoint remains superseded in the 03 history; the repaired focused 152 and this committed full run certify the accounting repair.

## Actual child and build provenance

The full suite recorded **617 Node launches, including 581 actual Pi worker launches**. Every launched PID has a guard-loaded audit event; the full run recorded no unexpected non-loopback or dotenv block. The separate proof deliberately triggered three non-loopback blocks and one dotenv block. It covers the actual Pi worker, child execution without NODE_OPTIONS and a hostname-lookalike predicate without DNS/network. The product child-environment allowlist was not broadened. Earlier guard inheritance limitations remain explicitly preserved in [the correction record](node-guard-correction.md).

The sole Tester built this worktree's Pi output immediately before the guard and full gates; there was no intervening build or runtime source writer. The five generated artifact hashes were first recorded while the full run was active, then found identical after completion. That timing is explicit, not represented as a pre-suite artifact-hash capture. Generated artifact-map digest: `332362af2be455bdd359f4afbee55306daa09993704d6749e97f724ee8718f02`. Runtime imports/builds used the dedicated worktree, never an archive/reference checkout.

## Coverage and limits

The combined public controlled tests cover role suggestions and typed boundaries, original-input preservation, actual Pi wire evidence, judgment fallback, successful/empty/failed policy lookup, scoped unavailable status, exact query reuse and all supplied references, mixed-result provenance, stale owner/request/source rejection, replay, cancellation/deadline handoffs and rollback of actual staged cart/memory SQL. The bounded accounting fixture preserves lookup/reuse/tool/primary-turn totals after the event tail rolls; these observed counters are not provider HTTP or cost estimates.

Only synthetic credentials and local/loopback providers were used, with temporary/in-memory business state and dotenv access blocked. Python 3.12.14 and dependencies were installed independently from verified official rebuild caches, using Python copy mode. No real provider or user credentials, historical application state, frontend modification or browser journey was used. No repository lint script is configured, so lint is not claimed as passed.

This controlled result does not establish real language quality, live token/cost/latency improvements, browser interactions, the user's frontend match, deployment or final user acceptance. The optional human-operated comparison remains separately verified and must preserve unknown metrics as unknown. The frontend handoff must retain these missing layers rather than infer them from backend success.

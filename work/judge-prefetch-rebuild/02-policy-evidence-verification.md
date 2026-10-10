# 02 policy evidence: repaired final controlled verification

Dedicated Tester, 2026-10-07. **Final repaired ticket 02 passed all 524 backend tests, 2 separate harness regressions, Pi typecheck/build and dependency checks on one frozen source/harness version.** The 44 targeted policy cases are included in the backend total. This is not final four-ticket, real-provider, frontend/browser or user acceptance.

## Exact tested candidate

- Test-time HEAD: `79d34be1037a5fd910fd49bdb735afbea99b17b0`; tree `200b6b5c901660625233f3ff351604aee4fae923`.
- Complete product/test patch on that HEAD, including the new safety-test file: SHA-256 `07cf37bacbb692839d46bf4da46af033ef94a028924d49776c6fed776cd4c116`.
- Patch construction is deliberately explicit: the tracked `git diff --binary HEAD -- backend runtime frontend data` is followed by `git diff --no-index --binary -- /dev/null <path>` for each then-untracked source path. Here the appended path is `backend/tests/test_judge_policy_safety_public.py`. The tracked-only diff starts `64daf155`; it is a different artifact, not source drift. The JSON records its full digest and the combined digest above.
- Exact 246-file manifest digest: `9120143c73ce84afad44d338691394ce10c0805f1d6dba197eff871b463f0e47`.
- [Final source and check equality](02-policy-evidence-final-source.json) records every source hash, all harness hashes, the digest algorithm, commands, return codes, elapsed times, guard audit summaries and raw-record/output hashes.
- All five final captures below have identical source and harness hashes before/after execution. Each task-local Node launcher also remained unchanged. The current source matches them and the independent Spec re-review's complete 246-file pin. Standards and Spec changed-line re-reviews identify the same repaired runtime/safety-test files.
- After the tests, the integrator committed the final product/test source as `0aaffb39549db2704c6c0c414e3819277023e7a6` (tree `0a0cc2d221ab9b0ef24288d2cf8004c1fd549e6e`) and merged canonical integration as `7ea06a343f95043cc5c1948ef74fc139e0de2280` (tree `186645c9d8e37fe629f06d7104432af0789af2ba`). The Tester independently verified all 246 source files and final harness files in both committed trees and worktrees against the tested hashes. This is source-equivalence verification, not another test run. Publication mapping remains the integrator's responsibility; this report does not itself claim publication.

## Final gates

Each label identifies locally retained `evidence/<label>/{record.json,output.log,source.patch}`. Public checkout evidence is the curated report, manifest and history; bulk raw logs, temporary databases, dependencies and caches remain excluded.

| Label | Scope / command | Result |
| --- | --- | --- |
| `02-policy-evidence-green-11` | Both public policy-prefetch/safety modules | **44 passed**, 43.41 s pytest / 45.954 s capture |
| `02-final-dependencies-repaired` | `uv pip check`; installed Python versions compared to `requirements.lock`; Pi `npm ls --depth=0` | Exit 0; **62** locked Python versions match and are compatible; direct Pi packages match installed declarations |
| `02-final-pi-build-repaired` | `npm run typecheck && npm run build` in `runtime/pi` | Exit 0; 8.14 s |
| `02-final-guard-proof` | Direct Python strict-loopback predicate check without a socket; separate task-local Node guard tests | **2 passed**, 1.99 s pytest / 3.231 s capture |
| `02-final-backend-full` | In `backend`: `.venv/bin/python -m pytest -p pytest_asyncio.plugin -q` | **524 passed**, 701.71 s pytest / 718.574 s capture; no selections or exclusions |

The full backend includes the 44 new policy cases and all 193 backend cases that would have been in a repeated post-repair focused run. That redundant focused run was not executed. The two Tester-only guard tests live outside `backend/tests` and are separate from 524. No pass totals are added together as if overlapping runs were distinct tests.

## What the public controlled cases establish

- Each new Keke text receives the named policy judgment, including existing deterministic confirmation/ambiguity shortcuts; normal text still uses the same Pi, while those shortcuts add no Pi model call. Typed actions, Momo and replay retain their zero-additional-judgment behavior. Admission, owner, displayed-plan and replay safeguards remain exercised.
- A yes decision uses the complete original query and no invented category. Real request-owned evidence/ref, source/version, outcome and coverage reach the actual Pi SDK HTTP input as separate lower-trust user data, with the complete original text retained and no fabricated model tool result. The four policy contents/IDs/version remain unchanged.
- No/uncertain skip prefetch; timeout/error preserve genuine safe diagnostics and ordinary policy-tool availability. Lookup errors remain no-ref failures rather than empty facts. Successful, empty and failed attempts remain distinct; exact-scope recovery resolves only the matching failure. Persistent unavailable scope can be projected by the host alongside other work. No lookup is cached or skipped by ticket 02.
- Completed and waiting outcomes retain their ordinary results, policy facts and explicit Momo boundary. Validated multi-message general explanations retain individual units/provenance; policy/boundary facts do not become general-history units. Shopping constraints and mixed dish/history/memory cases retain their own validated facts.
- Empty results display source/version and unknown status. Partial evidence preserves unaddressed coverage, and model-written approval/refund claims cannot replace host facts. Scoped/owner/request/forged references and lower-trust source tool-escalation cases are rejected.
- Cancellation and deadline checks cover judgment, prefetch, blocking progress/freshness reads, ordinary tools, model continuation and publication. Controlled clock advances occur at real SQL boundaries; separate existing tests exercise the real 30-second provider deadline and real 31-second blocked admission. These are correctness checks, not performance measurements.
- After actual cart/memory INSERTs and staged history writes, a late final deadline rolls back the outer transaction. Public cart/orders/plan/state/history/memory readback remains unchanged, with no success deltas. No inner business commit authority was added.
- The final four concurrent new-goal/abandon fixtures block an actual lookup, change the task through public commands, then release it. The repaired runtime returns stale state before a subsequent catalog read or third Pi HTTP call, preserving history/cart and the user's new state.

## Retained failures and superseded checkpoints

[Execution history](02-policy-evidence-verification-history.json) contains all **45** captures with exact commands, source/harness pins, exit codes and log/record hashes. Raw failures remain retained.

- The first official-registry install failed at DNS resolution before application execution. An offline package-manager install from this rebuild's verified official caches succeeded into new local directories; the failed attempt was not hidden.
- The first policy GREEN attempt failed because the fixture assumed SDK user content was a string. Verbose actual-wire capture showed the evidence and original as text-part arrays. The fixture was corrected to inspect the actual transport shape; product behavior was not changed to satisfy that assumption.
- RED/GREEN slices separately reproduced and repaired judgment fallback, lookup recovery, waiting composition, general-unit provenance, empty/partial facts, post-blocking deadline checks, actual transaction rollback, deterministic fresh-text preparation and persistent scoped failure display.
- The pre-review candidate had 40 targeted passes and a **191-pass focused capture**. That process completed normally with exit 0 before the freshness P2 was acted on; it was not interrupted. It is explicitly superseded and cannot certify the repaired candidate. The old full backend had not started.
- The final freshness RED reproduced four failures: late catalog reads after prefetch and a third model HTTP request after ordinary lookup, for both new-goal and abandon. Two post-operation `assert_current` calls, followed by existing stop/deadline checks, repaired the specific handoffs. The fresh 44-case GREEN and final full suite above apply to that repair.
- Initial Node guard probe failures and the historical inheritance overclaim are retained in the separate [guard correction](node-guard-correction.md) and [guard proof history](node-guard-verification.json), not silently relabeled.

## Dependencies and isolation

This worktree received its own Python 3.12.14 virtual environment and Pi Node package directory: 62 Python packages and 87 npm packages installed offline from the current rebuild's official PyPI/npm caches. Python used copy mode. No archive/reference environment, old application database or editable application installation was borrowed. The final dependency checks reverified the locked Python versions and direct Pi packages.

All final captures used sanitized environments, synthetic credentials and temporary/in-memory business state. Python's audit guard and the corrected PATH-based Node launcher were active. The separate guard proof blocks a synthetic non-loopback destination in the actual public Pi worker, a lookalike hostname through a no-network sentinel, and a dotenv read when NODE_OPTIONS is omitted. The ordinary full suite logged **577 Node launches, including 541 Pi worker launches**; every launched PID has a guard-loaded audit entry, and there were no unexpected non-loopback/dotenv guard blocks in that suite. Source/harness/launcher before-after equality is recorded.

The product's explicit child-environment allowlist was not broadened. The Tester changed only test tooling/evidence, not product/backend tests/frontend source; implementation and public fixtures remained with the designated owner. Only the dedicated Tester executed verification commands.

## Remaining limits

- Ticket 03 query reuse/multi-reference work and the final same-version whole-phase gate remain separate. These results do not release overall four-ticket acceptance.
- No new frontend writes, typed DOM run, real-browser journey or user acceptance. The backend public typed/action/SSE behavior is covered; local frontend integration remains open.
- No real-provider sampling, real language-quality result, paired old/new benchmark, latency/token/cost improvement or live holdout. Unknown usage/cost is not zero. Controlled lookup/model counts are not live performance claims.
- No configured repository lint script; lint is not claimed as passed. Publication and deployment are not inferred from local verification.

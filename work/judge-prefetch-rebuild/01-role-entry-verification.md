# 01 role entry: frozen controlled verification

Dedicated Tester, 2026-10-07. **All final controlled gates passed on one source version: 480 backend tests, the overlapping 149-test focused subset, Pi typecheck/build, and dependency checks.** This is ticket 01 plus the bounded thinking transport verification, not acceptance of all four tickets or of the real frontend/provider experience.

## Exact candidate

- Test-time HEAD: `ec625a27db5418f0851a5da946c384531534309c` (the durable WIP commit).
- Test-time HEAD tree: `b9a6d62a8c51e3299a76c35359dc6132d8931587`.
- Final tracked product/test patch on that HEAD: SHA-256 `500f395d80a9bdf6af9201a4f10d63ce254320cdb5cea8c773bf1ffbcf81b3f0`.
- Exact 244-file source manifest digest: `05e4e9ca1d0cabdd7169ad3d56a83003f8edc3ea4daa330f9a30738c8c01e09f`.
- [Final source manifest and check equality](01-role-entry-final-source.json) contains every file hash, the digest algorithm, commands, result codes, elapsed times, and raw-record/output hashes. All four final checks had identical before/after source manifests, matching the frozen candidate and the post-run worktree. No source changed during any capture.
- After verification, the integrator committed the six-file repair as `9f2eff1265c373736cc5f8683c8ccaa680959c30` (tree `205ed5cd8ba42da198360a1d4f8e8dbe875c1f17`) and merged canonical integration as `46f3fcf47d544e0c0ecead0abc13cb23d63a38b8` (tree `f670841b8c4a821874bda1c603bd57f64edf4f54`). The Tester independently verified that all 244 committed and worktree source hashes in both locations equal the tested manifest. The different whole-tree hashes include their distinct documentation/history context. This is an exact source-equivalence check, not another test execution; publication mapping remains the integrator's separate responsibility.

## Final gates

Each label below names locally retained `evidence/<label>/{record.json,output.log,source.patch}`. Raw evidence is not promised as part of a public checkout; the linked curated manifest/history retain the necessary result and provenance summaries.

| Label | Command / scope | Result |
| --- | --- | --- |
| `01-review-final-focused` | Backend pytest with explicit asyncio plugin, 16 selected modules covering role/legacy/public contracts, navigation/context/returns, Kev wire, snack/drink/comparison/confirmation regressions, and thinking transport | **149 passed**, 135.26 s pytest; 140.192 s capture |
| `01-review-final-dependencies` | `uv pip check`; importlib metadata comparison to `backend/requirements.lock`; Pi `npm ls --depth=0` | Exit 0; all **62** Python locked package versions match and are compatible; direct Pi dependencies match declared installed versions |
| `01-review-final-pi-build` | In `runtime/pi`: `npm run typecheck && npm run build` | Exit 0; 7.351 s |
| `01-review-final-backend-full` | In `backend`: `.venv/bin/python -m pytest -p pytest_asyncio.plugin -q` | **480 passed**, 652.46 s pytest; 668.007 s capture; no selection or exclusions |

The focused count overlaps the full suite and must not be added to it. The full run includes isolation, actual Pi and LangGraph SDK loopback flows, transaction/confirmation/owner/version safeguards, memory/history, cancellation/recovery, and existing real-time timeout/SQL-stall cases. These controlled fixtures do not measure real-model quality or production performance.

## RED → GREEN history and retained failures

[Curated execution history](01-role-entry-verification-history.json) lists all 33 surviving captures, including every failure, exact command, source-manifest digest and record/output hash. Earlier successes apply only to their captured versions; final acceptance evidence comes from the four same-source gates above.

- Initial role work proceeded through `01-role-entry-red-01` to `red-08`, with corresponding incremental GREEN captures. The first `green-01` attempt still failed (1 failure); `green-01b` passed. Those records remain retained.
- `01-role-entry-red-09` reproduced the missing public typed navigation response (1 failure). The final public OpenAPI fixture now passes and also checks SwitchRequest required fields, Boolean acceptance, optional/nullable route ID, role enum and extra-field rejection.
- Earlier `01-focused-regression` was **141 passed / 1 failed**. The failure was a stale expected condition map that omitted the user's already-selected authoritative `product_type: potato_chips`. The fixture was corrected without loosening production behavior; both final focused and full runs pass it.
- `01-review-diagnostics-red-01`: **2 failures** for absent correlated, sanitized diagnostics on distinct HTTP/schema causes. `01-review-diagnostics-green-01`: **6 passed**, including unchanged public fallback/replay. Diagnostic payloads preserve cause fingerprints/frames without raw provider bodies, credentials or URLs.
- `01-review-composition-red-01`: **2 failures** for missing host after-sales boundary alongside completed shopping/policy and waiting/clarification results. `01-review-composition-green-01`: **4 passed**, including exclusive boundary and intact first context. Public SSE retains the existing results/references and appends a fixed boundary plus explicit pure-navigation Momo action; fixture-supplied false claims do not become authority.
- `01-review-boundary-type-red-01`: **3 failures** because string, integer and object markers were silently accepted. `01-review-boundary-type-green-01`: **5 passed**, including the two valid mixed-result paths. Invalid non-Boolean markers now fail with `PI_ANSWER_INVALID` before publication.
- The previously completed transport integration had 46 passing selected cases, but it is historical evidence. The final focused/full gates re-execute the current transport paths and role behavior on the repaired frozen candidate.

## Isolation and execution boundaries

The Tester first verified that no prior pytest, capture, build or install process remained active. The surviving `backend/.venv` and `runtime/pi/node_modules` are actual directories local to this worktree, not links into a reference/archive tree. No reinstallation was needed. Python is 3.12.14; direct Pi dependencies are pi-agent-core/pi-ai 1.0.3, typebox 1.3.27, TypeScript 5.9.3 and @types/node 22.19.0.

All captures used the committed `run_check.py` and guards: a sanitized child environment, synthetic keys, temporary/in-memory databases and checkpoints, disabled pytest plugin autoload, blocked dotenv reads, and Python/Node connections restricted to loopback. No real provider credentials, existing business databases or real-provider calls were used. The harness hashes and per-run source hashes remain in raw records. Only the dedicated Tester executed verification commands; the Tester made no product/test/frontend changes.

## Not verified / not claimed

- No new frontend writes, typed DOM execution, real-browser journeys or user acceptance. The backend's public typed HTTP/action/SSE contract is covered; the frontend implementation and same-version acceptance remain the local handoff.
- No live-provider sampling, real language quality, latency/token/cost improvement, paired historical performance comparison or independent live holdout. Unknown usage/cost is not reported as zero.
- No repository lint script is configured; lint is not claimed as passed.
- Tickets 02–04 and their final integrated whole-phase gates remain separate. Independent Standards/Spec review results and publication mapping are maintained by the integrator, not inferred from passing tests.

## Later isolation wording correction

The [Node guard correction](node-guard-correction.md), discovered during ticket 02 on 2026-10-07, qualifies the earlier blanket Node-enforcement statement above: Pi's explicit child environment omitted NODE_OPTIONS, so the old Node guard was not inherited by that worker. Synthetic credentials/endpoints, Python isolation, test outcomes and source equality remain distinct verified facts. Earlier raw records are preserved; they are not relabeled as stronger-harness runs. All subsequent/final whole-phase verification uses the corrected task-local Node launcher and its direct real-worker enforcement regression.

## Integration carry-forward to ticket 02

The independent Spec re-review closes the ticket 01 role-boundary composition finding. The pre-existing five-kind policy attachment gate can still omit policy evidence for waiting/general and other unsupported primary outcomes. Ticket 02 must cover complete policy-plus-primary-result composition, including waiting + policy + role boundary. This is a known baseline gap assigned to 02, not a new 01 regression or a claim that 01 solved all mixed-policy rendering.

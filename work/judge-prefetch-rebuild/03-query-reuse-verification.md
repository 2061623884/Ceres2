# 03 query reuse: repaired final controlled verification

Dedicated Tester, 2026-10-07. **152 focused backend cases passed on the final repaired snapshot**, including all **34** ticket 03 cases. Locked dependencies, Pi typecheck/build and **3** separate guard/isolation checks passed on the same source and harness. The final whole-phase backend suite is a separate required gate in the dedicated 04 core worktree; no redundant full 03 run was performed.

## Exact tested candidate

- Test-time HEAD: `2cdc88f9400ccf5fe8a86cb55892601fa8bf4065`, tree `12bf09d9865fe2320b1113d215997aaab240fdd0`.
- Exact 248-file source manifest: `7c86cf268f5f4d7055626d6db1e3970d23735bd313ed148f638ede0a02c4368f`.
- Complete source patch SHA-256: `56be7d0c39f6211f924f328215d793bf5bf3031ae682c0cccfe794cd3173e641`.
- Patch construction: tracked `git diff --binary HEAD -- backend runtime frontend data`, then the binary no-index diff from `/dev/null` for the then-untracked `backend/tests/test_judge_policy_reuse_safety_public.py`. The tracked-only diff is `341f56d67eba47f201182f12a485c5ad24335712d6a6113acdd04c73b46fab32`; these are different artifacts, not source drift.
- [Final source and equality evidence](03-query-reuse-final-source.json) records every source/harness hash, all final commands, elapsed times, guard/launcher audit, review pins, and raw record/output hashes.
- All five final captures below have identical source/harness hashes before and after. Both core changed-line review pins have the identical complete source map. No verification process remained active when the Tester released the commit freeze.

## Final scoped gates

| Capture label | Scope | Result |
| --- | --- | --- |
| `03-query-reuse-green-05` | Both public query-reuse modules | **34 passed**, 35.16 s pytest / 36.947 s capture |
| `03-final-dependencies-repaired` | Python dependency compatibility and exact lock versions; Pi `npm ls --depth=0` | **62** locked Python versions match; exit 0 |
| `03-final-pi-build-repaired` | Pi `npm run typecheck && npm run build` | Exit 0, 7.429 s |
| `03-final-guard-proof-repaired` | Two task-local Node guard regressions plus backend controlled-isolation regression | **3 passed**, 2.47 s pytest / 3.565 s capture |
| `03-final-focused-repaired` | Query reuse, prefetch, safety, role entry, legacy navigation, shared policy, compound projection, purchase, confirmations, atomic memory and official thinking transport | **152 passed**, 120.02 s pytest / 124.923 s capture |

The 34 are included in 152. Two guard tests live outside the backend suite; the third isolation test will also be covered by the final full backend run. Overlapping results are not added into a fictitious unique-test total. Exact module paths and commands are retained in the JSON evidence.

## Established behavior

- Exact trusted request/session/owner/task scope, original query, category and current authoritative source version allow reuse of complete real successful or empty policy evidence. Failed acquisition is not reused, and a later genuine success/empty can recover. New queries, categories, source versions and request/owner scopes remain separate actual lookups.
- Earlier applicable references remain available after a later subquery. Every supplied legacy single reference and new list reference is checked, including mixtures, malformed lists, wrong-scope/forged references and acquired references whose authoritative source version changed.
- Multiple real query scopes retain source/version/query boundaries and host-rendered facts. Mixed waiting, purchase and role-boundary projection, exact-body replay, terminal replay and business write protections remain exercised through public APIs and actual Pi SDK HTTP traffic.
- Stop, deadline and task-anchor checks still run around blocked reads and reuse handoffs before later dispatch/publication. Controlled tests assert actual lookup, tool and model activity, not merely intended calls.
- Bounded request accounting survives a rolled 256-event tail. The legal existing-budget fixture issues three sequential batches of 16 identical policy calls after the initial guide call: one actual lookup, 48 reuses, 49 tool starts and five primary Pi turns. The fixed-size `runtime_summary` keeps observed totals, policy judgment summary and a truncation flag; durable readback agrees and no cart write appears. The original 1536 token declaration and 30-second budget remain unchanged. These counters do not claim unobserved provider HTTP counts, usage or cost.

## Retained RED/GREEN history

[All 26 captures](03-query-reuse-verification-history.json) preserve commands, exit codes, source/harness pins and raw-log hashes. Raw evidence stays local under `evidence/<label>/`; curated artifacts are suitable for the canonical repository.

- RED 01 reproduced three actual reads for prefetch plus two identical same-batch tool calls; GREEN established one read and complete evidence reuse.
- RED 02 reproduced the last-reference-only rejection; GREEN retained the earlier applicable reference. RED 03 exposed accepting an expired source-version reference; GREEN rejected it.
- RED 04 reproduced both rejected multi-reference output and dropped delivery evidence when legacy and list forms coexist; GREEN passed all 49 related reuse/prefetch/safety cases.
- The initial 33-case acceptance and **151-pass focused capture** completed normally before the accounting review fix. They are superseded, not evidence for the repaired candidate.
- The first tail-accounting RED hit a fixture-only `max_tokens` assumption. The corrected fixture checks the actual SDK field `max_completion_tokens=1536`; RED 05b then reproduced the missing summary after the tail rolled. The repaired 34-case GREEN and 152-case focused result above certify that fix. Neither failure was discarded.

## Dependencies, isolation and limits

This worktree received its own Python 3.12.14 environment and Pi package directory from this rebuild's verified official PyPI/npm caches: 62 Python and 87 npm packages, Python copy mode. No archive/reference environment or editable application linkage was borrowed. No repository lint script is configured, so lint is not claimed.

All test captures use synthetic keys, temporary/in-memory state and guarded loopback fixtures. The corrected task-local Node launcher reaches the actual Pi child despite the product's restrictive environment allowlist. The final focused run recorded **125 Node launches, including 117 Pi workers**; every launched PID has a guard-loaded audit record and the run had no unexpected guard block. The separate guard proof deliberately demonstrates non-loopback and dotenv blocking, including a hostname-lookalike probe without DNS/network. Harness and each per-run launcher hashes are pinned before/after. The historical guard inheritance overclaim remains explicitly corrected in the existing guard report; it was not silently rewritten.

The optional comparison-runner drafts are outside this 03 source/harness. There was no real-provider sampling, frontend modification, browser/DOM acceptance, live benchmark, language-quality verdict, or measured latency/token/cost improvement. Unknown metrics remain unknown. Final whole-phase verification, publication mapping and the frontend handoff remain separate acceptance steps.

## Post-verification integration map

The final product/test commit is `35a30fab775764cfcbc01ee84599fb450b6411bd` (tree `65d84693b2245d51fa753140742805798067fed2`); canonical merge is `d6a40886926bf203b53c52db27d2177b1b3dcb80` (tree `2fad3a1c8e74593dc19ee929211be0d35a323938`). The Tester independently verified every one of the 248 source hashes and all final harness hashes in both committed trees and worktrees. This establishes source equivalence, not an additional test run or remote publication. The dedicated 04 core worktree is frozen at that canonical merge for the single whole-phase gate.

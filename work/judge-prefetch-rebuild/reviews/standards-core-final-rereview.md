# Core Standards re-review: bounded accounting repair

Result: **No new documented-standard violation, actionable smell, or scope growth identified.** The prior core review remains applicable; this supplements its event-tail caveat.

## Candidate

HEAD `2cdc88f9400ccf5fe8a86cb55892601fa8bf4065` plus current source changes. All 248 files match `03-query-reuse-green-05/frozen-candidate.json`: manifest `7c86cf268f5f4d7055626d6db1e3970d23735bd313ed148f638ede0a02c4368f`; saved source-patch SHA-256 `56be7d0c39f6211f924f328215d793bf5bf3031ae682c0cccfe794cd3173e641`. Adjacent `standards-core-final-rereview-pin.json` preserves exact hashes and comparison with the previous review.

Only two product files and two reuse fixtures changed. Removing only accounting additions restores both previous product-file hashes; cache/reference checks and freshness/publication behavior are unchanged.

## Checks

- `pi_product_runtime.py:62–90` records fixed policy acquisition/outcome/tool-origin/reuse counters, observed SDK tool starts and primary Pi turns, one policy judgment, and a truncation flag before trimming the existing 256-event diagnostic tail. This closes the normal-result accounting gap without unbounded logging, a telemetry framework, new configuration, retries, or budgets. It has actual callers and implements ticket-03 observability, consistent with AGENTS:15,20–24.
- Every policy/SDK event append now uses the same recorder. Reuse does not increase acquisition counts; failed actual lookups do. SDK starts/turns are not represented as provider HTTP requests, tokens, cost, or successful tool outcomes.
- `pi_product_turn_service.py:267` includes the summary in the existing result/receipt publication transaction and replay path. The change adds no business authority, database schema, or independent commit, preserving ADR 0001.
- `test_judge_policy_reuse_public.py:198–210,253–297` checks outcomes and real public rollover/readback; the safety fixture checks stopped/deadline accounting. These use approved public/provider/query seams under REBUILD-DECISIONS:100–104. The independent Tester record reports 34 passed with matching before/after source maps; this reviewer executed no tests.

## Limits

Hard-error paths can omit the summary; unavailable counts remain unknown. The detailed event tail can still truncate, explicitly marked. No complete HTTP/usage/performance evidence is implied. Integrated documentation, separate harness/manual runner, frontend/browser/provider/user acceptance remain separate gates. No product/test edits, builds, installs, or provider calls performed.

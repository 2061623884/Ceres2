# Core Spec re-review: accounting repair

Original P2 closed. No new scoped finding. Read-only review, 2026-10-07.

Ticket `tasks/ceres2-judge-prefetch-03-query-reuse.md:36` requires “观测分别呈现实际检索、复用、补查、工具调用、Pi 轮数”. The repair now keeps those observations independently of the bounded diagnostic tail:

- `backend/app/services/pi_product_runtime.py:62–90` maintains fixed counters for actual policy lookups and outcomes, tool-origin policy lookups, reuses, observed SDK tool starts and primary Pi turns. It preserves one complete policy-judgment record and marks tail truncation. Accounting occurs before trimming; no unbounded trace store is introduced.
- All actual lookup/reuse/judgment sites and SDK lifecycle frames call this recorder (`:211–264,370`). Failed lookups count as failed acquisitions; reuse does not increment acquisition totals. Cancellation and budget behavior remain unchanged.
- `backend/app/services/pi_product_turn_service.py:267,283–291` adds `runtime_summary` to the standard result, persisted receipt and final event. The original progress callback only stores phase updates, not an independent full accounting stream.

The public fixture at `backend/tests/test_judge_policy_reuse_public.py:253–297` drives the real SDK through three sequential batches, retaining unchanged output/round caps. After the 256-event tail evicts the judgment, it observes one actual lookup, 48 reuses, 49 tool starts and five primary turns, then verifies persisted readback. Existing error/empty/recovery fixtures now check summary outcomes; interruption fixtures check no additional reuse. The dedicated Tester's record reports **34 passed** with no source drift. I did not execute it.

The names correctly describe observations: primary SDK turns are not HTTP attempts or validator calls, and tool starts are not successful executions. The repair invents no provider usage/cost. Hard-error responses do not expose this normal-result summary, so their missing counts must remain unavailable, never inferred as zero. Tool-origin lookup is an exact origin count; it should not be relabeled as exclusively supplemental retrieval when prefetch was skipped.

## Exact candidate

HEAD `2cdc88f9400ccf5fe8a86cb55892601fa8bf4065`; tracked diff SHA-256 `341f56d67eba47f201182f12a485c5ad24335712d6a6113acdd04c73b46fab32`. All 248 source hashes match frozen manifest `7c86cf268f5f4d7055626d6db1e3970d23735bd313ed148f638ede0a02c4368f`; source patch `56be7d0c39f6211f924f328215d793bf5bf3031ae682c0cccfe794cd3173e641` also matches. Adjacent `spec-core-final-rereview-source-pin.json` retains the exact source map and changes from the original review.

Only runtime, its result projection and two reuse-test files changed. This closes the source-level core Spec gate, not final integrated documentation, whole-phase verification, comparison-runner review, live/performance or local frontend/user acceptance.

# TASK09 explicit memory and role boundary

## Implemented contract

- `ShoppingMemory` in canonical SQL is the only authority for user/feedback/project/reference. Fresh table plus additive migration marker `0009_explicit_role_memory`; no archive database or automatic extraction code is used.
- Chat tools share `MemoryCommand`. The host binds owner, origin role, run source ID and current user source text. Writes require an exact source quote; model-supplied owner/source authority fields are forbidden. Reference URLs must occur in the user's source text when supplied.
- A turn may list to identify a unique existing record, then stage at most one write. Correction/deletion recheck owner, current validity and expected revision in the final transaction. Delete is a revisioned tombstone, excluded from every live list/recall; no physical history purge is claimed.
- Pi applies the staged command under its existing session/task/run-stop fences in the same commit as public messages and run receipt. Mercury applies it under its canonical case/run/selection/responsibility fences in the same commit as public chat. Neither memory service owns a commit.
- Explicit management list returns every valid owned record, optionally by category. It is not the model's default memory context. Default recall is limited by role, current need, five records and 2,000 serialized-record characters. Shopping is Keke-only, aftersales Momo-only, communication style can be relevant to both. Relevant terms use English word/CJK-bigram matching; this is deliberately conservative lexical recall, not a claimed semantic search service.
- Within the authorized domain, the effective winner per key is chosen before relevance or size admission: explicit beats automatic, then most recently updated. An excluded explicit value never causes an automatic predecessor to be used. Explicit tombstones also participate in key winner selection as deletion fences, without entering live lists or model prose; a newly explicitly saved replacement can supersede that fence. Current task conditions suppress same-key background; business facts and authorization always remain in canonical services, never free-text memory.
- A prior successful explicit list can contribute at most 2,000 characters of ordered opaque ID/revision positions, plus total/truncation/provenance metadata. This supports an ordinal follow-up without restoring deleted or expired prose as remembered background. Missing/truncated/ambiguous references require clarification; writes still revalidate the record.
- Mercury permits memory management before order selection. Business tools still require the selected canonical order; no model confirmation/apply capability was added. Normal next-turn history is read from canonical published case messages rather than a checkpoint that might contain an unpublished staged success. Management prose is retained for the user's history but omitted from future provider context.

## Ownership

TASK09 owns memory model/schema/service and tests; TASK04 edits Pi worker/runtime/turn hooks as unique owner. Foundation owns model aggregation and migration registration. TASK14 transferred memory-only editing of Mercury graph/tools/store/router after its root technical release. Existing frontend remains unchanged: deterministic memory messages use the retained chat/SSE paths. No settings UI, external memory engine or TASK10 extraction/Dream was added.

## Fresh evidence

All commands were run by the dedicated Tester, never by the implementer. Raw evidence is under `work/ceres2-runtime-upgrade/09/test-runs/`:

- `red-explicit-memory`: actual Pi SDK unknown memory tool fails public save/list.
- `red-mercury-memory`: actual LangGraph no-order memory request incorrectly waits for order.
- `green-memory-public-01`: initial five public/migration checks pass.
- `green-role-memory-01`: two P15 regression failures exposed inappropriate coupling to the order read port; fixed by using canonical CaseStore sessions, without changing the failure fixture.
- `green-role-memory-02`: 55/55 affected checks pass; exploratory moving-source run.
- `green-memory-atomic`: all twelve then-current memory checks pass, including stop-before-commit, expiry during a delayed model response, source precedence, role sharing and installed OpenAI SDK wire behavior.
- `red-memory-lookup-update`: two actual-runtime natural correction failures before allowing lookup followed by one mutation.
- `red-memory-review-boundaries`: three independent review regressions fail before precedence-before-filter and prior-list identity fixes.

Independent read-only Standards and Spec review both report no remaining actionable findings after the lookup, precedence, ordinal-reference and nullable-source fixes (root confirmed closure on 2026-10-05 17:39 UTC). `green-reviewed-memory` records 74/74 passing affected checks; the identical-source pair `final-memory-01` / `final-memory-02` then passed 74/74 in 56.27s / 56.20s. `final-memory-source-comparison.json` verifies all four scoped snapshots with fingerprint `6c57b5ff6e2fd300f397c2431952fc1f5dbb5b98f32c69dd8a67a8d619b94ad4`; unrelated TASK04 DOM-only work is excluded. A subsequent public `committed` read/write marker correction passed its new check twice and all 20 then-current memory tests. `mutation-flag-successor-evidence.json` records the exact existing-source delta (only `pi_product_turn_service.py`) plus the new test, without mislabeling it as part of the earlier pair. A later deletion-fence RED (`red-deleted-predecessor-fence`) demonstrated that an explicit tombstone must suppress an older automatic predecessor of the same key; after TASK04 released its consumed-source freeze, its narrow fix passed the focused check twice and all 21 current memory checks in 42.16s. `deletion-fence-successor-evidence.json` captures the exact two existing-file differences from the original 74-case pair (`memory_service.py` and the earlier `pi_product_turn_service.py` flag correction), plus the two new regression files. The final narrow Spec re-review reported no actionable issue. No current-source claim is substituted for the original pair fingerprint. Controlled HTTP providers and synthetic data prove public contracts only. No live qwen3.8-27b quality/latency, real browser, or user acceptance is claimed. Real credentials remain absent; actual model verification stays at TASK16.

Current owned/consumed hashes: `release-source-manifest.json`. TASK10 authority/source-freshness handoff: `HANDOFF-P10.md`. Root owns technical release and local commits.

Root released the controlled technical scope on 2026-10-05 17:53 UTC. Ticket status remains 待验收 because live/provider/browser/user gates remain at TASK16. No further implementation changes are pending; root may transfer the memory authority to TASK10.

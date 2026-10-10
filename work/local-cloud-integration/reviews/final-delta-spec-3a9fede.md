# Final product delta: independent Spec review

Baseline: `81b02f956298361cf9044ee289c0821a8275fab8`.
Target: `3a9fedeae8f01053dba2abc2d6bc36daef125133`, clean T09-product-fixes worktree.
Commands: git diff 81b02f9...3a9fede and matching git log; outputs saved alongside.

No new actionable Spec finding. Static review confirms the bounded-tail correction and behavior-neutral filter rename.

The spec requires “完整 runtime_summary 独立于裁剪后的详细事件尾部”. pi_product_runtime.py:137–141 now trims events in place. The final result's existing runtime_events reference therefore remains the actual latest 256-event tail when final projection emits retrieval observations. Summary counters still update before trimming and remain independent; no events, counts or provenance are fabricated. This also resolves the stale-alias behavior missed by the preceding whole-branch review.

The public regression saturates the diagnostic tail before result construction, then exercises a final projection retrieval through the real KnowledgeService observation boundary with controlled worker output. Assertions cover the terminal SSE payload, persisted receipt and owner-scoped JSONL export: 256 retained events, final retrieval_end/source identity, truncation marker and complete retrieval count. Its synthetic markers are explicitly test-only. Execution remains sole-Tester evidence; this reviewer did not execute it.

The rename to product_filter_mismatch changes only the function identifier and all three production callers: comparison, product-question exploration and purchase validation. The predicate body, canonical category/attribute checks, Offer checks and purchase authority are unchanged. No remaining old identifier exists in product backend/runtime/frontend at this pin.

This delta extends the static whole-branch report at 81b02f9; it does not substitute for final same-pin execution. Browser, live-provider/graph quality and user acceptance remain blocked or unpassed as previously reported.

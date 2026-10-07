# Final product Standards delta closure

Fixed baseline: 81b02f956298361cf9044ee289c0821a8275fab8.
Fixed repair: 3a9fedeae8f01053dba2abc2d6bc36daef125133.
Worktree: T09-product-fixes, clean at inspection. Exact commands: git diff 81b02f9...3a9fede and git log 81b02f9..3a9fede --format='%H %s'; full diff and three-commit list retained beside report. This supplements, rather than replaces, the full 37c98400...81b02f9 Standards review. Applicable repository standards and smell baseline remain unchanged.

## Findings (under 400 words)

The final-projection tail-alias P2 is closed on source inspection. pi_product_runtime.py:139–141 now deletes the old prefix in place, preserving the same list object already held by the final result. The initial append and aggregate updates retain their prior behavior. Searches of backend product code found no other runtime event-list rebind after its constructor initialization; pre-Pi events are extended into that list before result publication. Late projection retrieval_start/end therefore reach the persisted result while the tail remains bounded at 256.

The public regression saturates the tail at agent_end, before the result captures its reference, then makes a final projection call through the actual KnowledgeService.search observation boundary. It checks the terminal SSE result, persisted receipt and owner-scoped export for the 256 bound and final retrieval_end, and retains the aggregate retrieval count assertion. Test setup explicitly controls retrieval content and adds diagnostic padding; it does not claim natural-language or live retrieval acceptance. Root/Tester report RED at 9df0abb with the actual 257-entry result; GREEN is pending at review time.

The nonblocking naming P3 is also closed: product_filter_mismatch replaces drink_filter_mismatch at the shared definition and the three existing consumers in comparison, product questions and purchase confirmation. Predicate logic is unchanged. Git source search found no stale old-name references in backend, runtime or frontend. No compatibility alias or unused abstraction was added.

Hard documented violations: none. New judgment/smell findings: none. All product Standards findings from the whole-branch review are closed at this repair pin, contingent on separate terminal Tester evidence and canonical source-equivalence binding. Helper cleanup was closed independently at 8e6be36 and is not reaccepted by this product-only delta. No tests, builds, installations, services, APIs or code edits performed by this reviewer; only external review artifacts written. Browser and real-provider acceptance remain separate.

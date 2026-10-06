# TASK08 Spec corrections recorded at 18:26 UTC

Closed at 18:33 UTC: all targeted REDs became GREEN, corrected 19-case behavior pair passed, independent reviews closed, and root released the controlled technical scope. The following preserves the original correction assignment; RELEASE.json records final applicability.

The first frozen implementation passed two independent 16-case public/migration runs and DOM/type/build checks. That baseline predates the following Spec findings and is not the final TASK08 release. TASK05 keeps its shared-source freeze through its final paired regression. Root transfers shared ownership to TASK06 for these corrections before its new feature edits. TASK08 does not edit shared App/turn/runtime files concurrently.

## Actual App completion order

Spec found App's catch unconditionally erased every displayed card. An older A failure can therefore erase newer B cards even though Python's expected-ref compare-and-clear preserves B. The success path also unconditionally erased all cards before appending an unrelated A reply, causing the same outcome.

Public UI reproducer: `work/clean-rebuild/08-comparison/ui_comparison_order.mjs error` and `... success`. Both hold A's stream, complete B with a current comparison, then release A. B's rendered card and posted displayed_candidate_refs must survive. Tester alone runs the scripts.

Minimal integration:
- Capture `shownCandidates` before entering send's try block, preserving its existing before-admission timing.
- Catch must remove only refs in that captured set from displayedCandidateRefs and message.productCards; never erase newer minted refs. Continue removing A's empty placeholder and presenting its error.
- For successful terminal responses, first fetch the latest authoritative session. Build its current product-card ref set. Preserve already-rendered message cards in that set, and attach only returned turn.product_cards in that same set. Then apply the authoritative snapshot. Unrelated A's empty card array cannot erase B; an actual current empty comparison still clears stale cards. Do not promote unseen background snapshot refs without rendering them.

## Actual App reconnect

Spec found reconnectGuideRun's terminal TurnResponse discarded by `.then(async () => ...)`; the later snapshot only prunes old cards and never renders the newly completed comparison. Reopening a running comparison therefore loses its cards until another reopen.

Reproducer: `ui_comparison_order.mjs reconnect`. Open a running comparison, deliver only a terminal response containing messages/cards, then assert those cards render and their refs are posted on the next user message.

Consume `.then(async turn => ...)`, merge its completed messages/cards using the same authoritative ref gate as ordinary send, remove the reconnect placeholder, and then apply the snapshot. A small shared terminal-message projection helper with these two actual callers is appropriate; no new general UI framework is required.

## Protected comparison close

Deadline and tool-budget closure return a normal protected terminal, not the exception branch that retires previous comparison evidence. Prior displayed candidates currently survive restoration after an unsuccessful new comparison.

Public actual-Pi reproducer: `backend/tests/test_comparison_safety.py::test_protected_comparison_close_retires_old_snapshot`, parameterized tool_budget/deadline. The deadline case intentionally uses the real 15-second runtime bound.

Inside the existing fenced final host transaction, when status is deadline or tool_budget, call `ComparisonService(db, owner).clear(session_id, comparison_snapshot_refs)`. Its exact-ref CAS is already implemented and preserves newer concurrent displays. Do not publish uncompleted partial products as new comparison cards. No new schema or runtime option is needed.

## Verification

After actual REDs, Tester reruns each targeted UI/public case GREEN, then the full comparison suite twice at the corrected source, affected purchase/guide regressions and frontend checks. Root's independent reviewers recheck the corrected axes. Live qwen3.8-27b, real browser and user acceptance remain separate.

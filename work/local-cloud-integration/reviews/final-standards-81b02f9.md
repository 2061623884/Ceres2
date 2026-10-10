# Final whole-branch Standards review

## Fixed scope

Baseline: `37c98400e7152b89e4a58f02fff3bceaa73b0eac`.
Candidate: `81b02f956298361cf9044ee289c0821a8275fab8`.
Exact commands: `git diff 37c98400e7152b89e4a58f02fff3bceaa73b0eac...81b02f956298361cf9044ee289c0821a8275fab8` and `git log 37c98400e7152b89e4a58f02fff3bceaa73b0eac..81b02f956298361cf9044ee289c0821a8275fab8 --format='%H %s'`.
Nonempty 227-path diff; full diff and commit list saved beside this report. Canonical advanced to documentation-only 4e728c7 during inspection; static diff from frozen candidate across backend/app, runtime/pi/src, frontend/src, data/fixtures and packaged browser-support was empty. Findings remain pinned to 81b02f9, not the moving branch.

Standards: root/frontend AGENTS, recovery entrypoint AGENTS, CERES2-WORKSPACE, domain/issue-tracker instructions, GLOSSARY, ADRs 0001/0002, current nine-ticket TASK and integration spec. Historical scope restrictions were interpreted according to the explicit integration supersession. All twelve code-review smell heuristics considered; repo overrides apply, tooling-enforced style checks excluded. Stage reports were context, not inherited full-branch clearance.

## Standards findings (under 400 words)

Hard documented-standard violations: none established.

1. P2 correctness/design judgment, newly found integrated observation alias: `backend/app/services/pi_product_turn_service.py:356,369–374` stores `runtime.events` in the result before final question projection can perform observed retrieval. `pi_product_runtime.py:136–139` appends then rebinds the list when trimming. If the tail is already 256 entries, projection's retrieval_start grows the list held by the result to 257 and redirects subsequent events to a new list. The persisted/exported result consequently exceeds the tail bound and omits retrieval_end, although aggregate counters remain correct. Refresh the result's event reference after projection, or trim in place. Tester should combine a saturated tail with final projection retrieval and assert receipt/export have at most 256 entries including the final retrieval_end. Existing tests cover saturation and final projection separately.

2. P2 correctness/design judgment, existing helper lifecycle issue remains in this frozen candidate: `work/local-cloud-integration/browser-support/launch_browser_fixture.py:29–34` waits only for the group leader after TERM. A leader that exits while a descendant ignores TERM bypasses KILL; lines 133–135 still report fixture_stopped=true. Check the exact owned group independently, escalate within bounds, and report failure if absence is unproven. Helper-owner repair is outside this pin and requires separate review/evidence.

3. P3 possible Mysterious Name, nonblocking: `backend/app/services/product_constraints.py:45–64`, drink_filter_mismatch, now governs category/brand/pack/type/packaging across all product categories and final confirmation. Rename to product_filter_mismatch with its real callers when centrally convenient. The existing docstring mitigates this; no new correctness issue is claimed.

The prior initial-context observer P2 is closed by the process-wide observation lifetime. No additional independent finding established in integrated policy/retrieval, canonical shopping, native completion, audited interim/SSE, UI navigation, GraphRAG, aftersales/ticket evidence, migrations or export seams. Final testing, browser acceptance and Spec remain independent gates.

Summary: zero hard violations; three judgment findings (two P2, one nonblocking P3). No tests, builds, installations, services, APIs or product edits were performed.

## Detailed inspection notes

### Policy / knowledge / deadlines

Inspected corpus, hybrid, BGE, knowledge service/worker/CLI, policy snapshot acquisition, all modified catalog/comparison/question/dish service seams, Guide admission/projection and Mercury deadline forwarding. Build and read use shared implementation/config/fixture identities; no runtime fallback to lexical production recall was introduced. Full approved/category ID space precedes downstream candidate filtering, and current SQL product/Offer projections use populate_existing. Request-owned deadline/cancellation travels through lock acquisition, nonblocking writes/reads and worker ownership. Graph CLI supervision is distinct from Guide budget. Policy successes and empties are reusable only within matching scope/version; failures remain unknown and can be retried in the existing request. No additional unused configurable seam identified.

### Pi / interim / provenance

Inspected the complete changed Pi worker and runtime hunks, provider-observation transport, claim prompts, process publication and runtime summary/export logic. Native finish stays in the same sequential Agent; tool authorization and Python reference validation remain authoritative. Interim text is independently audited before a separately fenced history/event transaction, without committing business runtime staging. Final publication retains deadline/cancellation fences and transaction rollback. Provider call identities and usage distinguish observation from estimates; tail and aggregate contracts are deliberately separate. The new P2 is their final-publication alias interaction, not loss of aggregate totals. ContextVar reset covers pre-runtime errors and normal exit. Export-time fingerprints do not claim loaded-code equivalence; old timestamps remain nullable.

### Graph

Inspected graph export/build/search/project_selection, providers, graph context/manifests, runtime graph lookup/fact rendering and relevant public/official-library/BGE tests. Official query invocation, model selection, host Global expansion and canonical facts are separate. Current recipe records own displayed amounts; graph references alone do not create procurement. Source/model/implementation/artifact validation precedes provider work; local BGE is fixed-revision/local-only. Per-operation context avoids cross-query counters, unknown interrupted calls remain unknown, and errors are not successful empty retrieval. No unsupported inheritance or generic framework introduced.

### Business / photos / migrations

Inspected order progression CAS, proposal facts/confirmation, upload validation, exact ticket application links, user/operator photo reads and additive migrations/model registration. Confirmation remains Python-owned, tied to owner/order/selection/generation and one transaction including receipt and human-ticket responsibility. Photo bytes are bounded and decoded, ticket reads join explicitly linked applications rather than all case evidence. Existing legacy applications receive null links, not invented associations. No old state/index import appeared in changed production paths.

### Frontend

Inspected modified React screens, typed client contracts, native finish navigation, stream event handling, contact-order restoration, retained order progression race guard, product detail, photo upload/display and object URL cleanup. New calls have existing UI consumers. Role actions remain explicit, old navigation receipts are not replayed by plain buttons, interrupted streams preserve approved interim IDs, and selected-order generation fences avoid late response replacing a newer order. Tail alias issue is server-side. Added styling follows existing Tailwind classes; no new styling framework/configuration.

### Tests / fixtures / docs / evidence

Read changed shared doubles, migration/photo/public HTTP/Graph/Pi/provenance regressions, supplemental UI/HTTP harnesses and existing-test contract updates; inventoried the full added test scope. Tests clearly label controlled source/model boundaries and do not turn DOM/HTTP into browser success. Static fixtures carry source/digest and explicit synthetic labels; mutable Offers are not copied from a runtime database. Independently reviewed helper isolation, unique browser origin, Host-gated cookie bootstrap, CSP, fresh HOME/database/checkpoint, allowlisted environment and source hash evidence; cleanup P2 remains open in the packaged pin. Reviewed dependency declarations, ignore scope, recovery/current task/README/handoff and historical evidence organization. Pending final verification and blocked browser entries are not treated as success; frozen historical reports/manifests are provenance records, not current acceptance. Final documentation should be updated by Merger after actual gates, without altering frozen product source during testing.

## Next verification request

For finding 1, use the existing public stream final-projection fixture and the existing controlled tail padding approach in one regression. Saturate before result construction, exercise real KnowledgeService.search on final projection, inspect public terminal receipt and explicit-owner JSONL export. Verify last retained event is the final retrieval_end, length <=256, events_truncated true and aggregates still match boundary calls. Reviewer has not run or claimed RED/GREEN.

For finding 2, helper owner's separately frozen fix must replace these exact packaged sources only after terminal Tester evidence and delta review. No acceptance of an unmerged helper candidate is implied by this report.

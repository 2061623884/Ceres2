# TASK14 implementation handoff (2026-10-05 17:19 UTC)

Status: root accepted the controlled technical release at 2026-10-05 17:19 UTC after final paired verification and closed Standards/Spec reviews. Formal task remains pending acceptance. No commit. Real qwen3.8-27b, browser/layout and user acceptance remain TASK16 gates.

## Public contract and flow

- POST `/api/v1/mercury/sessions/{id}/proposals` accepts kind refund/return, nullable item_id, nonempty reason and current selection_version. It runs actual LangGraph eligibility → immutable proposal → persistent confirmation interrupt. No application is created.
- The model receives only `prepare_aftersales_proposal`, alongside existing read tools. It cannot confirm or execute an application. Query graph stops after the concrete proposal summary. Button/API confirmation is the only current approval channel; ambiguous chat replies cannot write.
- POST `.../confirm` requires immutable proposal_id, idempotency_key and confirmed:true. It resumes the actual interrupt, then deterministic apply → receipt. Canonical receipt replay precedes all checkpoint reads; missing checkpoint can reconstruct a wait but cannot bypass the canonical transaction.
- GET `.../aftersales` restores current proposal and all case receipts. Existing refund/return progress readers now read canonical receipts; eligibility readers include existing applications.
- Frontend has a concrete order/item/quantity/amount/reason/policy preview, separate explicit confirmation, persistent receipt and refresh recovery. Editing draft terms hides the old confirmation; changed saved proposals and selections are server-fenced. Old order responses cannot update the current panel.

## Canonical authority and transaction

The sole SimulatedOrder/MercuryCase tables remain authoritative. Three additive tables hold immutable proposals, applications and receipts. The proposal includes the displayed scope and hash of original order facts, not a second order authority. Proposal revisions are per case. Creating a new revision invalidates the previous approval target.

A write fence on the canonical owner/case row precedes all submit reads. In the same SQLAlchemy transaction the service checks receipt identity/body, case owner, agent responsibility and generation, active run, selected order/version, current proposal revision, fresh eligibility and exact factual hash. It then creates the unique application and unique receipt before one commit. A committed receipt replays even if the later response or checkpoint fails. Failed precommit leaves neither application nor receipt. Original order snapshots and status are not rewritten; application requested means submitted for simulated handling, not approved/refunded.

Current rules: unshipped entire-order refund, or one delivered returnable entire line within seven days inclusive. No partial quantities or multiline custom policy. Reason changes require a new immutable proposal. No arbitrary fifteen-minute expiry; return window and canonical facts are checked again at submit. Human generation changes invalidate the proposal even after a later release.

## Migration and rollback

Foundation owner registers the three tables and marker `0014_confirmed_aftersales`. Order columns remain unchanged. Canonical cases receive the minimal aftersales_intent_version counter, default zero, to fence delayed proposals against newer accepted intent. The proposal lifecycle invalidated column is added idempotently for databases created during this ticket before the review fix; preview content is not rewritten. Repeated initialization is idempotent. Test fixtures create empty databases or synthetic pre-upgrade SQLite only. Before accepting any new writes, the pre-upgrade backup can restore the old schema. After a new application/receipt has committed, never restore that older backup: stop the application and all writers, retain the upgraded file, and inspect it with SQLite URI mode=ro. This is a maintenance hold, not an operational flag in the running application. The dedicated maintenance test confirms newly committed application/receipt/order facts remain readable and a write is rejected. Never drop live application/receipt tables or restore an unconfirmed legacy write path.

## Source/provenance

Current P02/P12/P13 handoffs and policy/order readers are the primary dependencies. Read-only selective reference: archived user's `Mercury/mercury/services.py` sections `_refund_check`, `_return_check`, create_refund/create_return. Preserved existing unshipped/whole-order, delivered/seven-day/whole-line and no-duplicate business meaning. Did not copy the archived independent connection/commit, demo identities or free-write model tool. Wang/NanGe are architecture references only; no source copied and no license assumed. No runtime import, symlink, dependency or old state from archive/reference.

## Evidence so far

Dedicated Tester only; exact evidence directory: [work/ceres2-runtime-upgrade/14/test-runs](../../ceres2-runtime-upgrade/14/test-runs/). Names below are relative to that directory.
- `red-aftersales`: six fresh HTTP cases fail absent route before endpoint implementation.
- `green-aftersales-01`: 12 passed including foundation/migrations.
- `green-aftersales-02`: 47 passed with P02/P12/P13/P15; frontend typecheck/build green. Concurrent TASK03 edits mean broad source snapshot was not a final freeze.
- `green-aftersales-03`: 15 TASK14 public/migration cases passed.
- `dom-aftersales-01`: actual component/client controlled DOM passes preview/no initial submit/exact key/receipt restore/changed terms/late result fence.

Fixed public fixture time: 2026-10-05T12:00:00Z. Model adapter in one test is a controlled tool response, while LangGraph and SqliteSaver are actual installed libraries. No live provider, real browser or inherited historical pass is claimed. Source manifest differentiates owned implementation from consumed shared files; final frozen pair and review records must supersede provisional evidence before technical release.

## Review corrections in progress

Standards found that a slow model could return after a human ticket was opened and closed, then save a proposal using the new generation. Public RED reproduced the visible stale proposal. The minimal fix carries the original host run ID and responsibility generation into both eligibility and proposal transactions; both require exact live run ownership and generation. Direct HTTP proposals use a separate idle-case path. Tester recheck and reviewer closure pending.

## Accepted replacement versus malformed request

A concrete review regression showed that an unshipped refund preview could survive a well-formed replacement request for an ineligible delivered-line return. The old preview was hidden locally but could reappear on refresh and still be confirmed. The dedicated red case reproduced this.

The real graph now first accepts a well-formed replacement intent under owner, selection and live model run/generation checks. This transaction invalidates only the earlier pending proposal's lifecycle flag; its immutable payload is preserved. The eligibility node then either proceeds to a new preview or explains the denial and that the old pending preview is invalid. This acceptance/invalidation remains committed on a later eligibility denial by design. Malformed shape, blank reason and missing/unsupported scope arguments fail before acceptance and leave the current preview alone. New application and receipt creation still occur exclusively in their one confirmed business transaction.

The earlier 55-case paired run predates this review fix and is retained only as historical scoped evidence; it is not the final source acceptance.

## Concurrent replacement correction

Standards then identified an earlier valid request paused before proposal persistence while a newer accepted request failed eligibility. Invalidating only existing previews did not fence that earlier in-flight request. Public synchronized RED reproduced it after the previous 57-case paired point; those runs remain evidence for their earlier source only.

Acceptance now increments a canonical case aftersales_intent_version in the same transaction that invalidates any prior pending preview. The graph carries this exact accepted token; both eligibility and proposal persistence check it under the case write fence. A newer accepted intent therefore fences an earlier delayed proposal even when the newer request is denied. This counter is not a second case authority or a background workflow. The shared migration adds only that case column and preserves existing selection, responsibility and history. Application/receipt atomicity remains unchanged.

## Final released scope and verification

Final exact-source pair: `final-aftersales-05` and `final-aftersales-06`, **59/59 twice** (23.45s and 22.89s), including all **23 TASK14 public/migration cases** and affected P02/P12/P13/P15 regressions. [Scoped source comparison](../../ceres2-runtime-upgrade/14/test-runs/final-intent-fence-source-comparison.json) confirms all four before/after snapshots match: `4e2fb91c6881958f1632256a9970f44338b7b845ff90ba787c2d79ffa4335e1d`. Unrelated TASK04 guide/runtime/test edits during run two are explicitly excluded, not misrepresented as globally identical source.

The matching `intent-final-dom-01` / `intent-final-dom-02` pair passes real component/client controlled DOM; `intent-final-typecheck` and `intent-final-build` are green. Freshly recompiled P02 late selection/SSE and P13 contact/remount DOM regressions also passed on the latest panel source: `intent-mercury-races` and `intent-contact-races`. This is not a real browser/layout claim.

Root confirmed both independent Standards and Spec re-reviews closed on the final accepted-intent counter source. Review findings and fixes: original run/human generation preservation; maintenance read-only retention of committed facts; sequential accepted replacement invalidation; concurrent accepted-intent token fence. Earlier 55/57 runs are historical, not the release point. Counter migration's attempted red capture happened after its edit and was green; only the actual public concurrent red is claimed for that change.

[Final release manifest](release-source-manifest.json) preserves the reviewed implementation hashes separately from consumed shared files. No implementation commits made. Live qwen3.8-27b, actual browser and user acceptance remain unverified TASK16 gates.

## Next owner: Mercury memory integration

Root has released TASK14; graph/tools/store memory integration hooks can now pass to TASK09 under explicit ownership. Preserve model proposal-only capability, actual confirmation interrupt, canonical run/responsibility/selection/intent fences and the single application+receipt transaction. The current query graph blocks at require_order before provider work; a future memory-only no-order route must not weaken order requirements for aftersales actions. CaseStore.publish_result already offers the same-transaction owner/run/selection/responsibility publication fence; any memory commit belongs inside that transaction, without its own commit. No TASK09 changes are included in this evidence.

TASK09 confirmed unique ownership transfer for memory-only graph.py/tools.py/store.py/router.py edits at 17:20 UTC. TASK14 will not modify those files further; later changed hashes require their own regression evidence.

# TASK13 exact-order contact integration

Root accepted TASK13 scoped technical release on 2026-10-05 16:37 UTC; Standards and Spec reviews are closed. Formal status remains pending acceptance. No commits made by this owner. This document does not imply real-browser, live-model or user acceptance.

## Authority and entry

Canonical SimulatedOrder/MercuryCase remain in the single business DB. No schema or migration was necessary. No historical unknown owner/time was imported. Mercury list/read projections expose canonical store_id (nullable) and version, leaving historical unknown store unknown.

The persisted order's contact button calls App with the exact order_id. App keeps an atomic one-shot {orderId, sequence}. Mercury restores the trusted owner case and explicitly calls selection CAS even for the same selected ID, fencing a prior delayed selection. Successful consumption acknowledges its sequence and App clears only that intent. Manual selections survive full page unmount/remount. No automatic chat message, model request, checkout confirmation or free-form write occurs from contact.

All Mercury client API requests share saleGuide.ensureIdentity, waiting for an in-flight trusted bootstrap. Browser-local case ID is only a restore reference; all public endpoints still validate canonical owner.

## TASK15 seam

Store.publish_result checks owner, run ID, selection version, responsibility and generation; only a successful guarded update invokes record_query_outcome(db, case_id, state) before the same commit. P15 owns its human module, structured graph/tool signals and service behavior. MercuryChat mounts the actual HumanCasePanel and refreshes it on successful completion/selection. These changes do not create another case authority.

## Fresh evidence

- HTTP metadata red → green; initial P02/P12/P13 regression 24/24.
- Shared backend pair after P15 integration: 35/35 twice, scoped fingerprint eae1f7182413b312ef05a794c8b5d576b28d84adcdbf7803811de84c25aa822f, recorded in ../../ceres2-runtime-upgrade/13/test-runs/final-shared-source-comparison.json.
- Controlled StrictMode component DOM final pair covers exact contact, repeated same contact, close/resume, stale in-flight selection fencing, and full unmount/remount after manual selection.
- Bootstrap race red → green, final independent pair; previous late-selection and late-SSE/error regression green.
- Integrated parent wiring typecheck/build green.

Evidence is controlled public HTTP/SSE + DOM, not live qwen or a real browser. P15 may still change its independently owned code; each run's source snapshot determines applicability. Review-source manifest separates TASK13 files from consumed shared files.

## TASK14 downstream

Use the sole app.mercury.models.SimulatedOrder and MercuryCase, not a second order/case store. Owner comes from trusted cookie; a contact button or thread ID is never authority. Order selection increments selection_version and responsibility_generation and remains blocked during an active query or human hold. Read_case exposes the canonical selected order and generation; query checkpoint is execution state only.

P14 must bind its proposals/confirmation to canonical case/order versions and revalidate owner, selection, responsibility generation, eligibility and confirmation in the same business write transaction. P13 adds no refund/return write tool or proposal authority. The independent Mercury entry and exact order selection are now wired; receipt readers/confirmed business writes belong to P14.

P15's later ticket-reply identity finding is outside the accepted P13 read-only order/case integration scope. Consumed human-module hashes in the test evidence are historical applicability records, not claims that later P15 changes passed these runs.

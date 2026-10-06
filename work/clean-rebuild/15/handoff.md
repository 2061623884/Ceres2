# TASK15 active implementation contract

Owner: implement_clean_human_tickets. Scope: minimal asynchronous human support only.

Canonical case authority remains app.mercury.models.MercuryCase in the shared SQLAlchemy business database. New HumanTicket and HumanHandoffState are supporting tables; neither duplicates ownership/selection/responsibility authority. Taking/releasing human responsibility increments canonical responsibility_generation in the same transaction as ticket state changes. P14 must check canonical responsibility='agent' and exact generation together with its authorization/operation claim in its write transaction. Closing/resolving never restores old authorization.

Public explicit human request uses the owner-scoped panel/API. Structured query signals are host-owned: policy_indeterminate from authoritative POLICY_UNKNOWN or a completed policy lookup without a match; service_failure from actual business read-service exceptions. Missing details, invalid model arguments, ordinary ineligibility and model prose never independently create a ticket. Two consecutive published service failures persist across restart before automatic handoff. Existing open/waiting-user ticket is reused for the same case.

Shared integration: P13 owns store.py and mounts HumanCasePanel; record_query_outcome(db, case_id, state) runs only after successful fenced publication and before the same commit. Foundation owns Settings/main/model registration/migration marker; P03 owns App operator route. Provider outages alone do not auto-escalate; user can explicitly request help. Provider keys must never be accepted as operator credentials; operator configuration is empty/disabled by default, and synthetic test credentials stay isolated.

Frontend HumanCasePanel.tsx, HumanOperatorPage.tsx, lib/humanCases.ts are retained clean-rebuild frontend scaffolds originating in prior implementation. They are selectively adopted without claiming old test success. Backend human implementation and test fixtures are fresh. No archive runtime imports, old business data or credentials.

Tests/acceptance: pending fresh Tester RED, green and independent repetition. Real provider, browser layout and user acceptance remain separate gates. No business refund/return write implementation in this ticket.

## Migration and safe fallback

The 0015 migration adds only human_tickets and human_handoff_states via registered metadata and records one idempotent migration marker. It does not import or rewrite old business records. Ticket order_id records the selected order at creation; resolved historical tickets keep that association even if a later agent session selects another order. Failure streaks are scoped to the canonical selection_version.

Do not roll back by dropping ticket tables or clearing MercuryCase human holds/generations. Before the first ticket exists, an application rollback can leave the unused additive tables in place. Once a ticket is open, retain this operator path or roll forward to a corrected version; an older application must preserve the canonical human hold and refuse agent writes. An unavailable operator is not permission to silently release a hold. No destructive downgrade or live-data repair command is included.

## Final controlled evidence (2026-10-05 16:39 UTC)

Fresh public RED covered missing implementation and business-service handoff. Review/self-review RED additionally covered malformed policy query/category incorrectly escalating, real service TimeoutError being mistaken for host budget expiration, in-flight UI responses clearing newer drafts, and stale version-one user replies landing on a replacement version-one ticket. All were corrected minimally and reverified.

Dedicated Tester final-human-05 and final-human-06 each passed 36/36 with P02/P13/P12 regressions. Exact scoped source fingerprint 1565ea10bc47ffdff768f8051cc85f5892089b0389287910269a24b4d8efcd31 matches all four before/after snapshots. Evidence: work/ceres2-runtime-upgrade/15/test-runs/final-ticket-fence-source-comparison.json. No implementation test commands were run by the owner.

Fresh ticket-fence-dom-01/02 passed user/operator lifecycle, exact ticket identity on reply and preserved newer drafts; actual App operator route controlled DOM, typecheck and build passed. Controlled DOM is not a real browser/layout claim. Source dependencies and retained-front-end provenance are recorded in release-source-manifest.json.

User message bodies now require exact ticket_id and version. Owner/case are canonical, and stale replacement-ticket identity returns 409 without mutation. Operator actions already identify ticket in the URL. Human messages never grant business authorization; release increments responsibility_generation again.

P14 transaction integration remains a later combined test gate: P15 demonstrates canonical responsibility increments and stale in-flight query-publication rejection but does not create an imitation financial write to claim P14 safety. The future real P14 write must consume the same generation in its transaction. Actual model/provider quality, real browser/layout and user acceptance are not established by controlled Python/DOM tests. Root confirmed scoped technical acceptance at 2026-10-05 16:41 UTC: both review axes have zero remaining findings. Root owns local commits. TASK15 will not modify the shared Mercury graph again without coordination with the incoming TASK14 owner.

Operator route: /operator/human-cases. HUMAN_OPERATOR_TOKEN defaults to blank, disabling all operator reads/writes; users configure their separate credential out of band if they choose to exercise it manually. Do not use a model API key. No permanent credentials were generated or saved by this task.

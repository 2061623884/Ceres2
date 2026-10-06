# TASK06 controlled evidence to date

- First append public RED: real Pi rejected unsupported operation; `06/red-multidish-append`.
- Minimal append GREEN plus all TASK05 public regressions: 10/10, `06/green-multidish-append`; compatible demand is aggregated before sale-package rounding.
- Group update/remove public RED after actual shared row purchase: schema 422, `06/red-group-revision-ledger`.
- Minimal targeted group updates/removal plus single-dish regression: 11/11, `06/green-group-revisions`; purchased SKU ledger survives and stale confirmation fails.
- Actual retained App group controls RED: missing per-group controls, `06/red-multidish-ui`.
- Actual retained App group controls GREEN, single-dish DOM regression and typecheck GREEN: `06/group-ui-green`, `06/single-dish-ui-regression`, `06/group-ui-typecheck`.
- Immutable group purchase reference public and UI RED verified: `06/red-group-purchase-evidence`, `06/red-group-ledger-ui`. Next minimal fix derives group evidence from durable confirmation receipts, never mutable condition fields.

Paths above are relative to `work/ceres2-runtime-upgrade/`. Tester owns execution and raw evidence. These are controlled/offline results using actual Pi and DOM transport simulation. Final paired runs/reviews remain pending. No live qwen3.8-27b, real browser or user acceptance is claimed.

Latest candidate (18:55 UTC):
- Immutable source receipt projection + TASK05 regression: 12/12, `06/green-group-purchase-evidence`; shared-source App ledger DOM GREEN, `06/group-ledger-ui-green`.
- Distinct recipe and full source demands + TASK05: 13/13, `06/green-distinct-shared-demand`. Refined missing-recipe RED ends in an actual waiting reply and asserts missing group directly (`06/red-distinct-dish-shared-demand-02`), rather than a fixture exception.
- Reserved group/selection condition field boundary + lifecycle/dish coverage: 24/24, `06/green-group-authority-boundary`.
- Additional current-behavior edge coverage: 6/6, `06/multidish-edge-regression`.
- Removed last-target stale-update RED then GREEN plus current multidish/dish regressions: 21/21, `06/green-retained-group-boundaries`.
- Shared budget reconstruction and isolated synthetic old JSON/receipt compatibility: 2/2, `06/multidish-compatibility-regression`.
- Final candidate source is captured in `review-source-manifest.json`. Independent review and final paired regression remain pending.

Independent review correction (19:02 UTC):
- Standards had no initial actionable finding. Spec found one P2: unrelated row checkbox changes rewrote unchanged shared-row per-group selection and could attribute purchases to an excluded target.
- Two public REDs: `06/red-mixed-contribution-selection`. Minimal fix reuses the actual contribution calculator for deliberately changed rows only; unchanged contribution flags remain untouched. Package recomputation occurs before budget/supply facts; separate explicit package quantities are retained.
- Corrected public/own/dish regression: 25/25, `06/green-mixed-contribution-selection`.
- Root reports both independent axes closed on the corrected application. Two regression-only checks additionally cover explicit package quantity and recomputed budget; these were added immediately before final freeze, without application changes.
- Final frozen source is `FINAL-CANDIDATE.json`; paired final verification and UI/build results remain pending.

Saved final validation outputs (read after environment restart, 19:10 UTC; no reruns by implementer):
- `06/final-multidish-01`: 134/134, 192.47s.
- `06/final-multidish-02`: 134/134, 192.08s.
- Actual retained App group and immutable-ledger DOM flows pass twice each: `final-group-ui-01/02`, `final-ledger-ui-01/02`.
- Existing single-dish and comparison App DOM regressions pass; final frontend typecheck/build outputs are retained.
- The final two regression-only selection tests remain byte-identical to `FINAL-CANDIDATE.json` (`6d5f23ead17e39cc6b7b98f90f4acdf8f77c29745e8c16d8716f361c4c39c25f`).
- Tester is reconciling saved execution metadata and source snapshots after restart; root retains the release decision. Live provider/browser/user gates remain separate.

19:11 UTC root release: Tester verified both 134/134 runs exit 0, four identical 304-file snapshots and current-source match, fingerprint `f3f92bbbecb18f4bff18d92a2cb2175056241bf53698f9b5792a177b9ab8f62d`. DOM pairs, single/comparison regressions and typecheck/build are all exit 0 at that snapshot. Both review axes are closed. Controlled technical scope is passed; overall/user/live/browser gates remain awaiting acceptance. Root transfers shared ownership to TASK07. No application edits or commits by this owner after release.

# Final independent controlled verification

Tested immutable candidate: `0c752a2b252d797297b4b073883571884ff6855a`, worktree `next-final-fixture`.

- Entire backend: **426 passed**, 645.95 seconds (runner 662.357 seconds), exit 0. Includes all real-time timeout and SQL-stall cases; no selection/exclusions. Evidence: `runs/fixture-final-backend-full/{record.json,output.log}`.
- Runtime typecheck/build and frontend production build/strict TypeScript: exit 0. Evidence: `checks/fixture-final-builds/{record.json,output.log}`.
- **37 controlled DOM/client scenarios passed**: 33 historical/next scenarios plus two result-introduction and two final-review scenarios. 49 base commands include compilation steps and are not 49 behavioral tests. Evidence: `checks/fixture-final-dom-all/{record.json,output.log}`.
- Isolated real OS-process kill/restart probe: **1 passed**, 5.66 seconds. Completed checkout receipt and exactly one order survive; interrupted Pi run recovers without provider replay; a fresh explicit turn works. Evidence: `runs/fixture-final-process-restart/{record.json,output.log}`.

All four captures report unchanged source. Backend captures fingerprint 242 files including four freshly generated runtime JavaScript artifacts. Build/UI captures fingerprint 280 relevant source/harness files. Source equality to docs-only integration `a41d9ea53c1684051d81de4471277f0ca4a4c8e1` is recorded in `final-controlled-equality.json`: 238 backend-source files and 280 build/UI-source files match exactly. Integration generated artifacts are excluded from that equality and require normal rebuild; the tested worktree artifacts were freshly built.

## Environment and scope

Python 3.12.14, Node 24.19.0, npm 11.9.0; dependencies originate from this project's locked fresh installation. Controlled runner uses synthetic settings, temporary home/DB/checkpoints, disables dotenv before application imports, denies dotenv reads, and restricts Python network access to loopback. Provider SDK and Kev boundaries use controlled local fixtures. No real credentials or old project environment were read or reused.

No repository lint script is configured. Existing nonblocking Vite native-config warnings and the controlled shopping-return harness React render-time state warning remain visible in logs.

## Historical evidence retained

- Original baseline: 296 pass / 1 inherited deadline-fixture failure.
- Three-slice baseline: 339 pass / 6 inherited explicit-role-navigation fixture failures.
- Seven-slice baseline: 378 pass / 1 inherited direct-stdio start-frame fixture failure.
- Superseded `e267fc9`: 403 pass; later independent review found uncovered constraint/quantity/compound/diagnostic issues.
- Superseded corrected `d2166e3`: 424 pass / 1 inherited exclusion fixture failure. Its fake provider indexed a correctly empty constrained search. Approved test-only correction preserves both early-filter behavior and the later authoritative exclusion guard; focused 48 tests passed before this final sweep.

These records remain unchanged; none is relabeled as a successful final run.

## Open acceptance gates

Controlled technical verification passes. Actual browser/layout/navigation acceptance, real configured model/Kev behavior, live memory/Dream behavior, private holdout, independent frozen V3 comparison, and user acceptance remain unrun or unknown. Scripted prompt comparisons do not establish naturalness, token or latency improvements. The OS restart probe proves only its documented bounded scenario. Independent Standards/Spec reviews are separate reports owned by the parent/integrator.

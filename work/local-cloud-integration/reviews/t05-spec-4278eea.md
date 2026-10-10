# T05 supplemental Spec review

Frozen target: 4278eea; prior reviewed target: 656cfef. Diff: git diff 656cfef...4278eea; matching commits/diff saved alongside. No production files changed. Read-only source review; no tests executed.

No actionable Spec finding in the test-only delta. The DOM harness uses retained React components and actual client modules with controlled responses; product explicit add, unavailable/error states, duplicate pending clicks, quality quantity/photo/confirmation, exact displayed ticket evidence, and sequential order transitions are exercised. The HTTP script invokes real public endpoints in the separately controlled synthetic fixture, including PUT for Mercury order selection, checkout/confirmation idempotency, rejected progression skips/stale versions, immutable snapshots, rejected quantity overcount, and ticket-scoped photo bytes.

Scope and evidence claims are honest: controlled DOM is not native browser acceptance; real public HTTP is not live-provider or retrieval-quality validation. These additions do not close all T05/T09 acceptance boxes. Chromium IPC EPERM and official CUA loopback refusal remain external browser blockers; final same-pin integration and user acceptance remain open.

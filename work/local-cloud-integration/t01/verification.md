# T01 controlled policy integration verification

Candidate: `6ba93b2b66a004fdfae1d7106d5f29a0512ddfd6`, including verified T07 core. Baseline: `37c98400e7152b89e4a58f02fff3bceaa73b0eac`; incoming: `6734c7fe79e670df2dae12b065dcc49c0b10a307`.

Final affected regression: **165 passed**, exit 0, 245.01 seconds pytest time (250.986 seconds capture). Runtime typecheck and build passed; separate actual-child guard proof: **2 passed**. Final captures have no source or harness drift. These counts are separate and not additive with earlier runs.

Exact commands, source sets, compiled output and harness hashes are in verification-history.json and source-manifests.json. The final captures additionally enumerate calibration/eval inputs and reusable DOM/build test scripts; earlier captures retain their narrower source scope plus exact full Git HEAD. No raw provider logs or private runtime data are published.

## RED/GREEN and review history

- Fixture/index mismatch and incorrect embedding revision were independently RED before snapshot validation.
- Worker queue timeout/cancellation, explicit stale/unavailable errors, partial-line timeout/recovery, active-request isolation and pipe backpressure were exercised. Real production CLI rejection of wrong index/corpus identity occurs before model imports.
- Missing index initially leaked SQLite OperationalError; changed to explicit unavailable with retained cause. Controlled missing numpy through actual production CLI returns unavailable, not empty; normal interpreter preserves the safety guard.
- Public Pi prefetch initially failed against removed legacy constants; actual snapshot identity/deadline wiring restored public behavior.
- Repeated policy lookups exposed a real context-budget regression: request message sizes grew to 138550 characters and the SDK reduced the last actual output cap from 1536 to 1. Host retains raw retrieval diagnostics; model evidence now carries complete policy facts and snapshot identity without duplicated retrieval payload. All 16 prefetch/reuse cases passed afterward at the unchanged 1536 cap.
- Initial whole-ticket candidate 3edc663 passed 135 affected checks but review found two remaining gaps. Six stale implementation/calibration/pooling/instruction/RRF/floor variants were then RED; shared complete-manifest validation passed 22 core tests. Same-scope success/empty after unknown-source failure remained falsely failed; public RED 2 failed/1 passed, then 5 recovery cases passed.
- The original Guide ingress actually allowed 30 seconds. The parent explicitly approved 30→15 seconds during this integration, preserving independent preflight and all model/token configurations. Both public ingresses and direct remaining-budget checks were RED, while independent preflight passed. After the change, 8 budget cases passed, including actual slow provider/validator and spent-admission cases, replay/reconnect and typed/no-judge behavior. This is an intentional approved budget change, not historical baseline equality.

Counts overlap and refer to distinct source candidates. Do not sum them or inherit historical results.

## Safety, dependencies and limitations

Fresh synthetic DB/checkpoints, fake credentials and loopback provider only. Actual Node PATH launcher forces the guard into spawned SDK workers even when NODE_OPTIONS is filtered; proof includes blocked non-loopback attempts. Python audit hook blocks dotenv reads and non-loopback sockets/DNS. Raw logs remain outside repository.

Python 3.12.14/Node 24.19.0 differs from incoming historical Python 3.11/Node 22.19.0. Runtime installed independently from its own lock, including successful offline reinstall from this task's fresh package cache. Business environment includes verified T07 Pillow 12.3.0 pin. Full incoming knowledge lock resolves under dry-run using documented official CPU Torch index; no full knowledge installation, BGE weights, GraphRAG build, actual model provider, user browser or human acceptance is claimed.

Tests use an explicit model-recall double at the retrieval-worker boundary for policy HTTP cases; production has no lexical fallback. Real worker JSONL tests separately verify subprocess/provenance/failure/deadline behavior. This is controlled integration correctness, not real BGE relevance or language-quality evidence. Final nine-ticket same-candidate regression and independent final reviews remain separate.


## Frozen canonical postmerge check

Tester captures at canonical `ccf272b752f096ce0d80f7d0a4f29b19c05b0a77` in a detached verification worktree: `t01-postmerge-minimum` 18 passed / 11.30s, `t01-postmerge-runtime-build` exit 0, and `t01-postmerge-portable-guard` 2 passed / 3.87s. All report no source or harness drift. Raw records remain in the workspace test-evidence/runs directory. These are focused postmerge checks, not a final aggregate or real-provider validation.

# Core Spec review: frozen 01–03 candidate

One P2 finding; no scoped business-behavior or scope-creep finding. Read-only source review, 2026-10-07.

## P2: Required accounting disappears when the lifecycle buffer rolls over

Ticket `tasks/ceres2-judge-prefetch-03-query-reuse.md:36` requires “观测分别呈现实际检索、复用、补查、工具调用、Pi 轮数”; spec `docs/plans/ceres2-judge-prefetch-spec.md:58,79` also requires retained judgment/evidence records and separate actual counts.

`backend/app/services/pi_product_runtime.py:185–213,236–238` places the new reuse, retrieval and policy-judgment records in `self.events`. Every SDK event then applies `self.events[-256:]` (`:344–346`). `pi_product_turn_service.py:266–267` publishes this tail plus tool rounds, without independent retrieval/reuse/tool/model totals or a truncation marker.

This is reachable within the unchanged budget: one guide_request followed by three sequential batches of 20 identical policy calls produces over 300 records and evicts the original judgment, actual prefetch and early reuse/model events. The worker limits tool rounds, not batch size (`runtime/pi/src/worker.ts:184–202`). Installed SDK 1.0.3 emits four lifecycle records per tool (`runtime/pi/node_modules/@earendil-works/pi-agent-core/dist/agent-loop.js:374–399,640–665`), plus the host reuse record. Thus public accounting can report zero actual retrievals despite a successful prefetch. The rolling buffer predates this work, but putting newly required authoritative accounting only inside it leaves the new requirement incomplete.

Preserve independent authoritative totals/required records while retaining bounded diagnostic detail. Add a public multi-batch fixture asserting actual retrieval, reuse, tool calls and model turns after rollover. This is source analysis, not an executed reproduction.

## Other reviewed requirements

Exact request/query/category/source-version reuse, uncached failures, full material recovery, all supplied singular/plural references, earlier valid references, source invalidation, error/empty/partial projections, mixed shopping/policy provenance, freshness/stop/deadline fences, role-only entry, Momo zero judges/button-only return and unchanged official-DeepSeek transport scope otherwise match the approved specification. Earlier 01/02 findings remain closed.

## Pin and release boundary

Baseline `4bed9c891261e382122d424825b649989ea92c92`; actual HEAD `2cdc88f9400ccf5fe8a86cb55892601fa8bf4065` plus tracked diff SHA-256 `a470a1a6cbb75406298f287bbcebc304173235c1a688f4073bc6e3a684a0ed48` and untracked safety test. Adjacent `spec-core-final-source-pin.json` records all 248 source hashes, unchanged at completion and matching the dedicated Tester's 33-pass acceptance record. No tests/builds/installations/provider calls executed here.

Whole-phase verification, manual comparison runner, final integration documentation, live/performance evidence and local frontend/browser/user acceptance remain separate open gates. This is not four-ticket acceptance.

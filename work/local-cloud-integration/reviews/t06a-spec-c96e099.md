# T06-A independent Spec review

Baseline `333e0bd81ebad05e6c062437c013feffa06d20c1`; fixed candidate `c96e0994d05e083d30725254b6107e1ea18a2939`. HEAD was already `826d71e3d5e4de4fd258942a2123781a20f29780`; candidate inspected through git show, then the owner's separately identified two-file delta reviewed. Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T06-graph`. Saved commands/output: `git diff 333e0bd...c96e099`, `git log --format=fuller 333e0bd..c96e099`, plus `git diff c96e099...826d71e` and corresponding commit list, using the full pins above.

## Finding

P2 — Explicit standalone graph CLI is not bounded by its advertised deadline. T06 requires “受剩余预算约束”; A phase specifically exposes the public CLI/service boundary. `backend/app/knowledge/cli.py::main` calls asyncio.run(search/build) directly and promises a 15-second default. `providers.py::LocalBge.embedding_async` runs synchronous encoder()/encode() in asyncio.to_thread. `graph.py::search/build` wait_for cancels the await, but cannot stop that running thread; asyncio.run then waits for default-executor shutdown before the CLI can print its timeout result. Model loading/encoding can therefore prolong a 15-second CLI call substantially. The installed Python 3.12 runners.py confirms shutdown_default_executor with THREAD_JOIN_TIMEOUT=300. Synchronous graph preparation also lacks an external interruptible bound.

Use an externally terminable process boundary for standalone graph commands and preserve the original deadline. This is a CLI termination defect, not demonstrated late Guide publication: KnowledgeService already kills its worker on caller expiry/cancellation. This finding remains at 826d71e.

## Covered boundaries

Explicit Local/Global call the official API; ordinary hybrid and deterministic dish lookup remain graph-free. Source/model/implementation/artifact provenance is checked before graph model setup. Host canonical records and model-selected IDs are separate, global expansion is labeled, references must belong to retrieved scope, and optional records never enter purchase requirements. Edges explicitly disclaim allergy, nutrition, substitution and household-stock authority. Missing/stale indexes and dependency/provider failures yield explicit failure, not empty success. Current dish facts are reread against fixture hashes; Offer authority remains in existing catalog lookup.

826d71e improves concurrent observation snapshots and distinguishes local-tokenizer usage from provider usage, recording response model; no new Spec issue found in that delta. Missing usage/cost remain unknown.

No tests/install/API execution. Prior 32 controlled tests are not current-pin acceptance; official dependencies/library tests remain Tester gates. Pi registration/refs are authorized B-stage work after T04, not an A-stage omission. Final combined verification remains required.

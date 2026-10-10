# T08-B independent Spec review

Fixed HEAD: `eebb326d14c2a6f8b91279c3da8ff82aa883f0e1`; baseline: `a835bd411f96285f15d67a75dd0c0abfdb1d1640`. Owner-confirmed clean worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T08-runtime`. Commands: `git diff a835bd411f96285f15d67a75dd0c0abfdb1d1640...eebb326d14c2a6f8b91279c3da8ff82aa883f0e1` and matching `git log --format=fuller`; outputs saved alongside.

## Findings

1. P2 — Initial context retrieval is missing from “complete” run counts. T08 requires “retrieval…独立计数”; the spec says “完整 runtime_summary 独立于裁剪后的详细事件尾部”. `backend/app/services/pi_product_turn_service.py::process:121` calls ProductQuestionService.projection before begin_retrieval_observation at line 187. An active question with a query invokes projection→explore→CatalogService.search_products→KnowledgeService.search, but no observer exists yet. A successful run then exports counters that exclude this real initial retrieval, without a retrieval completeness warning. Start the run observation before context construction (and preserve cleanup/early-failure evidence), or otherwise include those actual calls without reconstructing from the tail. Add a public run with an existing query-bearing active question and compare observed worker calls against the persisted/exported count.

2. P2 — Export drops known Local/Global identity. Spec: “官方 Local/Global 与模型选择结果分别记录”. `backend/app/evaluation/export_runs.py::DIAGNOSTIC_FIELDS:10–22` omits method. Both persisted graph_queries and graph_query_start/end contain that field, but summary()/diagnostic() remove it from JSONL. Counts/IDs survive while the actual search method is lost. Preserve the safe method enum and cover Local/Global export with truncated event tails.

## Other inspected boundaries

Actual fetch starts have run-scoped IDs, distinct from SDK turns and audits; duplicate end/start observations are deduplicated independently of bounded records/tails. Literal usage zero survives, absent/partial fields remain null, and cost stays unknown. Graph/provider/retrieval scopes are separate. Runtime disk/admission and worker/build/Prompt hashes are explicitly scoped, loaded-code equivalence remains unknown, and exporter hashes remain export-time evidence. Navigation linkage uses the exact authorized session/request, never the latest unrelated route. ContextVar reset, early-failure/replay admission provenance, explicit owner/manual labels and bounded non-raw diagnostics are present.

No tests, installs, API/model calls or real-data reads. Current final-pin tests remain Tester-owned; prior 24 passes are not this pin's acceptance. No unrelated scope expansion identified.

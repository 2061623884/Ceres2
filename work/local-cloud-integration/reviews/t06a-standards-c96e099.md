# T06-A backend: independent Standards review

## Fixed scope

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T06-graph`.
- Baseline: `333e0bd81ebad05e6c062437c013feffa06d20c1`.
- Reviewed frozen candidate: `c96e0994d05e083d30725254b6107e1ea18a2939`.
- Exact diff: `git diff 333e0bd81ebad05e6c062437c013feffa06d20c1...c96e0994d05e083d30725254b6107e1ea18a2939`.
- Commits: `git log 333e0bd81ebad05e6c062437c013feffa06d20c1..c96e0994d05e083d30725254b6107e1ea18a2939 --format='%H %s'`.
- Exact diff and six full commit SHAs are saved alongside this report. Candidate source was read with `git show c96e099:<path>` because clean worktree HEAD had advanced to `826d71e3d5e4de4fd258942a2123781a20f29780`.
- Standards: AGENTS, domain/issue tracker, GLOSSARY and ADRs 0001/0002; T06 staged TASK and integration spec. Twelve prescribed smell heuristics considered, repository overrides respected, tooling-enforced rules excluded.
- Read-only official interface reference: installed `test-evidence/knowledge-venv/lib/python3.12/site-packages/graphrag` (metadata version 3.2.0), `graphrag_llm/completion/completion.py`, `graphrag_llm/embedding/embedding.py`. No imports or execution were performed.

## Findings (under 400 words)

Hard documented violations:

1. P2, lost causal diagnostics: `backend/app/knowledge/graph.py:287–292` catches missing-index, stale-index and deadline exceptions and returns only generic error codes. The original reason/exception chain is neither logged nor retained, unlike the generic exception handler immediately below. AGENTS requires error conversion to preserve the original cause. Preserve these diagnostics privately, such as the worker stderr traceback, while retaining sanitized public codes. This matters for distinguishing changed source/model/artifacts and nested provider timeout causes.

2. P2, unsupported optional interface: `KnowledgeService.graph(... expected_graph_revision=None)`, worker forwarding, and public `graph.search(... expected_graph_revision=None)` expose a revision override with no current CLI/Dish caller supplying a value. The owner independently confirmed this absence. AGENTS forbids optional parameters without an existing caller. Remove this unused public plumbing; retain internal `validate_graph(... expected_revision)` because the post-query same-build check genuinely calls it.

Judgment/smell findings: no additional independent finding. The second hard violation also resembles Speculative Generality but is not double-counted.

Otherwise, source/model/implementation and artifact identities are checked before querying and again before returning; build rejects source drift. Host projection distinguishes model-selected entities from canonical community expansion. DishService reloads current canonical recipe records, and ordinary deterministic recipe lookup remains graph-free. Graph requests retain one caller deadline through queueing, pipes and provider timeout; parent cancellation kills the owned worker. Observations are query-scoped and bounded to 64 rows; unavailable provider usage remains unknown on parent-side interruption.

Official build/local/global API calls and provider abstract-method shapes align with the installed 3.2.0 source on static inspection. Controlled transport/no-weight tests explicitly distinguish library integration from real BGE or provider execution. Actual library adaptation and dependency validation remain Tester obligations; this review does not certify them.

No tests, installations, builds, services, real API calls or product edits were performed. Outcome: two open documented Standards findings for T06-A. Pi wiring, full T06 acceptance and final integrated review are outside this phase.

## Follow-on 826d71e static delta

Exact delta: `git diff c96e0994d05e083d30725254b6107e1ea18a2939...826d71e3d5e4de4fd258942a2123781a20f29780`; full diff/commit list saved separately as `t06a-standards-826d71e.*`.

This two-file delta adds locking around observation count/appends, snapshots row dictionaries, distinguishes local-tokenizer usage from provider usage, and records actual response-model identity. Those changes have existing concurrent embedding/provider callers and attribution requirements, and introduce no new Standards finding. They do not fix either hard finding above. No Tester result is inherited or asserted for this delta.

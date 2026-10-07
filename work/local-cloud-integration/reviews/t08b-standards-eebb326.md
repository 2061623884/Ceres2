# T08-B runtime observations: independent Standards review

## Fixed scope

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T08-runtime`, clean at inspection.
- Baseline: `a835bd411f96285f15d67a75dd0c0abfdb1d1640`.
- Frozen HEAD: `eebb326d14c2a6f8b91279c3da8ff82aa883f0e1`.
- Exact diff: `git diff a835bd411f96285f15d67a75dd0c0abfdb1d1640...eebb326d14c2a6f8b91279c3da8ff82aa883f0e1`.
- Commits: `git log a835bd411f96285f15d67a75dd0c0abfdb1d1640..eebb326d14c2a6f8b91279c3da8ff82aa883f0e1 --format='%H %s'`. Six full SHAs and diff saved alongside this report.
- Owner confirmed allocated extensions to guide_run_service, knowledge_service and the exact API launch_run fallback; no frontend/schema/migration/conftest changes. Runtime and evaluation helpers have actual callers.
- Standards: AGENTS, domain/issue-tracker instructions, GLOSSARY, ADRs 0001/0002, staged T08 TASK/integration spec. Twelve smell heuristics considered, repository overrides and tooling exclusions respected.

## Findings (under 400 words)

Hard documented violations: none established.

Judgment finding P2, retrieval observation lifetime starts too late: `pi_product_turn_service.py:121` refreshes current question context before the new ContextVar observer is installed around line 187. With an active product question and query condition, `ProductQuestionService.projection` calls `explore`, which reaches the real `KnowledgeService.search` boundary. Those accepted-run searches see no observer and are omitted from the otherwise complete persisted retrieval counters/source records. A successful run therefore undercounts actual retrieval work, independently of event-tail truncation. Extend the run's observation lifetime to cover this existing pre-runtime path and retain finally cleanup and early-failure evidence; add a public active-question regression that compares actual boundary calls to the exported summary. This is a correctness/design judgment rather than a hard style-rule violation. The owner independently confirmed there is no scope exclusion and this is a real undercount.

No additional independent smell finding established. Fetch observation allocates a call ID at each actual request and forwards original streaming chunks without awaiting the usage tail; cancellation/errors propagate to the existing SDK. Literal zero usage remains observed, absent fields remain null, aggregate partial usage is labeled incomplete, and record/tail truncation does not reset totals. Malformed observation JSON is left untouched for the SDK's existing parser rather than replacing provider bytes.

ContextVar tokens are restored in finally for the installed scope and isolate concurrent thread/run observers. Actual KnowledgeService calls, not tool counts, drive retrieval events; the finding concerns the missing earlier lifetime only. Disk-at-admission and worker-disk-at-start fingerprints are explicitly distinguished from loaded-code equivalence, which remains unknown. Prompt hashes describe supplied prompt inputs. Exact entry-request linkage, early failure/restart retention and replay avoid borrowing later route/version evidence.

Safe numeric/diagnostic projections avoid raw response bodies, keys and reasoning. The observed-call ledger tracks actual transport and stage without changing model/token limits or provider timing controls.

Outcome: one open P2 judgment finding. No tests, builds, services, installations, APIs or product edits were performed. Earlier 0955 test evidence is not inherited as final eebb326 acceptance; the affected run is pending. Final whole-branch review remains separate.

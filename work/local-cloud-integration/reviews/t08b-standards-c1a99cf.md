# T08-B Standards closure review

Frozen delta: eebb326d14c2a6f8b91279c3da8ff82aa883f0e1...c1a99cf27f54647bce32b9d07c4511bdd7a65941; T08-runtime worktree. Full diff and commit list retained alongside this report. Applicable standards: root AGENTS, domain/issue-tracker instructions, GLOSSARY, ADRs 0001/0002 and T08 task; all twelve code-review smell heuristics considered, with repository overrides and tooling exclusions.

## Result

The prior P2 observation-lifetime finding is closed at this pin. PiProductTurnService.process installs the ContextVar before entering _process, so the existing initial ProductQuestionService.projection search is observed. The summary/tail are transferred to the runtime once constructed; final projection remains inside the same observation lifetime. Finally restores the prior token. An initial projection failure persists observed retrieval data without inventing unobserved provider counts. The shared retrieval accumulator has two real callers and removes duplicated aggregation rather than introducing speculative abstraction. Export now permits the existing graph method field.

The new public stream regression compares actual KnowledgeService boundary calls against persisted totals, including initial/final projection and pre-Pi error. It injects the projection search rather than constructing the active-question state; this is controlled boundary coverage, not evidence of a separate natural-language active-question journey. Existing public SDK event assertions now distinguish observation envelopes from SDK lifecycle events and still check order, tool count, request count and no key disclosure.

Hard documented violations: none established. Judgment/smell findings: none open in this delta. No tests/builds/server/installation commands or product edits performed. This is source review only, not Tester acceptance or final baseline-to-product review.

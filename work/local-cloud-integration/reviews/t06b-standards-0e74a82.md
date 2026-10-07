# T06-B explicit graph runtime: independent Standards review

## Fixed scope

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T06-runtime`, clean at inspection.
- Baseline: `8186897ee58d7bf0702b17cfe86509c32c27ccfa`.
- Frozen reviewed HEAD: `0e74a8210371bc00960a2c06b5046ea94b18689f`.
- Exact diff: `git diff 8186897ee58d7bf0702b17cfe86509c32c27ccfa...0e74a8210371bc00960a2c06b5046ea94b18689f`.
- Commits: `git log 8186897ee58d7bf0702b17cfe86509c32c27ccfa..0e74a8210371bc00960a2c06b5046ea94b18689f --format='%H %s'`.
- Three commits: `64a09ef`, `f53e7a8`, `0e74a82`; full SHA list and diff saved alongside this report.
- Scope: Prompt, Pi runtime/turn service, one worker tool and independent public tests. T06-A implementation read only to trace actual calls, not re-certified here. T04 publication mechanisms and provider configuration remain unchanged.
- Standards: AGENTS, domain/issue-tracker instructions, GLOSSARY, ADRs 0001/0002, T06 staged TASK and integration spec. Twelve prescribed smell heuristics considered; repository overrides respected and tooling-enforced rules excluded. No earlier review-start state or pending Tester run was inherited.

## Findings (under 400 words)

Hard documented violations: none established.

Judgment/smell findings: none established. The lookup/provenance helpers have immediate runtime callers and concrete mixed-result contracts. Error recovery is limited to enumerated graph failures, retains safe causal diagnostics, and does not catch unrelated state/authorization errors. No speculative configuration or redundant compatibility abstraction was added.

Explicit `search_recipe_relations` reaches the existing DishService/KnowledgeService graph path through the run's catalog, preserving its absolute deadline and stop callback. After retrieval the runtime rechecks current anchors and budget; the owning loop rechecks cancellation/deadline before sending a result or advancing the model. Ordinary `search_dishes` remains deterministic and graph-free. Existing activity and kind-context boundaries are retained.

Graph failures produce error outcomes without dish refs; legitimate empty results remain distinct and neither is rendered as proof of absent relationships. Current request-scoped dish refs are issued from canonical records returned by DishService. Python's existing primary-reference validation rejects foreign refs, while final recipe projection re-reads current Offer candidates for requested ingredients. Generated graph descriptions do not become canonical quantities, price, stock or purchase authorization.

Prompt and rendered provenance distinguish model-selected entities from host community expansion and retain unknown/safety boundaries. Graph additions compose with existing policy refs and role-boundary output without broadening purchasing authority. Correcting the stale Prompt text from 30 to the established 15 seconds changes no runtime budget.

Graph attempt, official-call, provider and embedding observations are separate. Missing observations propagate unknown totals instead of false zeros. The per-run graph summary survives event-tail truncation, and recorded provider rows come from the bounded T06-A observation contract. Recoverable failure logs use the existing safe cause projection, not raw provider bodies.

Public test source covers Local/Global, mixed policy/role output, forged refs, error versus empty, ordinary graph-free facts, current Offer change, audited-interim coexistence, truncation and stop/deadline. The graph seam is explicitly controlled; this is not real GraphRAG/provider execution. The current deeper coexistence run is pending and no historical GREEN is claimed for this pin.

Outcome: zero open Standards findings at 0e74a8210371bc00960a2c06b5046ea94b18689f. No tests, builds, installations, services, APIs or product edits were performed. Same-pin Tester, merge verification and final whole-branch acceptance remain separate.

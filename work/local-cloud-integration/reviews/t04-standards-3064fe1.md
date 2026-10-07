# T04 reviewed interim messages: independent Standards review

## Fixed scope

- Confirmed owner worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T04-interim`.
- Baseline: `d9cbb180380515d5d10d0b76fc1bbba299db7385`.
- Candidate: `3064fe1d53bba45e88fd23d471fd9474580e5974`.
- Exact diff: `git diff d9cbb180380515d5d10d0b76fc1bbba299db7385...3064fe1d53bba45e88fd23d471fd9474580e5974`.
- Commit command: `git log d9cbb180380515d5d10d0b76fc1bbba299db7385..3064fe1d53bba45e88fd23d471fd9474580e5974 --format='%H %s'`.
- Full diff and five-commit list are saved alongside this report. Initial Git-object reads used the shared T03 repository; candidate and owner worktree were subsequently confirmed directly. No mutable HEAD changes are included.
- Standards: AGENTS, domain/issue-tracker instructions, GLOSSARY, ADRs 0001/0002; T04 TASK and integration spec. All twelve smell heuristics considered, with repository overrides and tooling exclusions.
- Owner scope: worker/general-claim/Prompt, Pi runtime/turn, guide_run_service event timestamps and independent test file. Existing nullable event-time schema is reused, with no schema/DB definition changes. Frontend integration is outside this candidate.

## Findings (under 400 words)

Hard documented violation: P2, discarded optional-message failure causes, `runtime/pi/src/worker.ts`, new interim audit catch line 285: `catch { /* An uncertain optional audit never grants publication. */ }`. Exceptions from auditor invocation or verdict JSON parsing disappear; the end event records only `approved=false`, indistinguishable from ordinary claim rejection. The new malformed structured-candidate JSON catch similarly discards its cause before auditing. Fail-closed recovery is appropriate, but AGENTS requires error conversion to retain the original cause. Retain bounded safe diagnostic kind/code/fingerprint and failure classification, using existing infrastructure. A pre-audit candidate rejection must not invent model calls/usage. Never publish candidate text, raw verdict/provider bodies, hidden reasoning or credentials to solve this.

Judgment/smell findings: none independently established. Shared validator mechanics resemble the existing general-audit path, but different rejection and continuation contracts make a speculative common abstraction unjustified.

Static strengths: only ordinary text accompanying non-final tool calls becomes an audit candidate; thinking and final-completion prose are excluded. The separate auditor uses the same configured model, with explicit fact/action/privacy rejection and fail-closed parsing. Audits remain within the original run timer. Python checks deadline/cancellation and anchors again before publication.

Interim history/event publication owns a separate Session and transaction, so it does not commit staged memory/shopping state. Session/task write fences and receipt status guard publication. Stable run-scoped message IDs reject conflicting content, deduplicate repeated delivery and avoid duplicate user history; final projection continues through canonical Python validation. Recorded event timestamps are persisted at insertion; absent historical timestamps and derived elapsed values remain null. Audit usage/cost remain unknown when not observed, with summary counts separate from the bounded event tail.

The relay test launches the actual worker using inherited Node `process.execArgv`, preserving the configured execution guard rather than bypassing it. Test source covers reject/uncertain, zero/multiple, cancellation/deadline/stale, replay and isolated publication. This reviewer performed no tests, builds, installations, services, real APIs or product edits. Owner reports 15 interim cases passing but a broader legacy waiting-recovery failure remains under diagnosis; no aggregate acceptance is claimed.

Outcome: one open P2 documented Standards finding. Independent Spec, terminal same-pin Tester evidence, frontend integration and final whole-branch review remain separate.

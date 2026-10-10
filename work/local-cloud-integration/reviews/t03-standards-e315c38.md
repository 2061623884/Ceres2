# T03 native completion: independent Standards review

## Fixed scope and provenance

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T03-native`; clean at inspection.
- Baseline: `ccf272b752f096ce0d80f7d0a4f29b19c05b0a77`.
- Frozen HEAD: `e315c387f31ac130e831b37544c7cf3e82f82a4b`.
- Diff: `git diff ccf272b752f096ce0d80f7d0a4f29b19c05b0a77...e315c387f31ac130e831b37544c7cf3e82f82a4b`.
- Commits: `git log ccf272b752f096ce0d80f7d0a4f29b19c05b0a77..e315c387f31ac130e831b37544c7cf3e82f82a4b --format='%H %s'`.
- Full diff and 15-commit list saved as adjacent `t03-standards-e315c38.diff` and `t03-standards-e315c38-commits.txt`.
- Standards: AGENTS, domain/issue-tracker instructions, GLOSSARY, ADRs 0001/0002. Contract: T03 TASK and integration spec. These sources are unchanged from the already-read baseline. Twelve prescribed smell heuristics considered; repository overrides respected and tool-enforced checks excluded.
- T03 owner confirmed native/Pi/API/Prompt commits: `1780a52`, `df696f5`, `93df5b7`, `eff18a5`, `6829ea1`, `c671fb4`, `5b86f9a`, `87eb046`, `e315c38`.
- Borrowed T02 seams, confirmed by T03 owner: `90d1ac3` = `534c74a` constructors; `499e70a` = `934b49f` constraints; `39b09e5` = `911a7a0` quantity eligibility; `bfaac86` = `7073f37` catalog hybrid; `d177372` = `6232789` terminal projection flag; `27d2ad1` = `a78b9b5` answer deadline forwarding. Equivalence identifiers are owner attribution, not independent source-equivalence certification.

## Findings (under 400 words)

Hard documented violations: none established within T03 and its borrowed integration seams.

Judgment/smell findings: none established. New completion schema and recipe-reference checks serve actual public call paths. Deadline/stop constructor propagation and terminal projection flag have concrete callers and regressions; they are not speculative generality under AGENTS.

`runtime/pi/src/worker.ts` ends the same Agent run through an exclusive `finish_response` tool after `guide_request`; it returns structured references to Python without a second summary call. Mixed finish/tool calls and pre-route completion are rejected. Main sampling uses auto tool selection; existing general validator and official-provider handling remain separate. Policy evidence stays a data message, while existing kind-based prompt/tool narrowing is preserved.

`pi_product_runtime.py` still validates current-request references, both policy forms and source snapshots in Python. Mixed policy/role-boundary/waiting projection is retained. New recipe facts validate dish references and ingredient membership, render canonical quantities/provenance, and read current Offer data for requested ingredient candidates. This branch prepares no purchasing proposal or cart mutation.

`pi_product_turn_service.py` forwards the original absolute deadline through catalog/comparison/question services, including final projection. Stop observation uses a separate read-only SQLAlchemy Session, avoiding rollback or expiration of staged publication. No intermediate publication commit is introduced. Existing final deadline/cancellation checks and exception rollback remain; protected terminal states skip new supply retrieval. Standalone Guide projection/answer requests establish their own bounded deadline, with answer projection reusing it.

T02-owned catalog/constraint/question changes were inspected only as dependencies of these T03 seams. This report does not release or accept the entire T02 ticket, which remains separately in progress.

No tests, installations, build commands, services or real APIs were executed by this reviewer. The owner reports 50 affected tests plus typecheck/build completed at this pin; obtain the dedicated Tester terminal evidence independently. No pending run or prior-pin success is inherited.

Conclusion: zero open T03 Standards findings. Independent Spec clearance, same-pin Tester evidence, merge verification and final whole-branch review remain distinct gates.

## Contract question forwarded separately

After this review, the owner highlighted that the existing per-kind projector ignores unrelated non-primary reference fields, while native `finish_response` permits those fields: for example, `status=waiting` with unused `product_refs`. Such a reference is neither rendered nor written; both policy-reference forms are independently validated. Whether the T03 requirement “Python 逐引用校验” requires rejection of every unused supplied non-policy reference is a Spec-axis question, forwarded to root and Merger. This Standards clearance must not be treated as resolution of that question or overall T03 release.

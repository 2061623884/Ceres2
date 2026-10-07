# T08-A export and annotation: independent Standards review

## Fixed scope

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T08-export`, clean at inspection.
- Baseline: `b25e3c80ee26984f12ae98492ee2ae7bd6323735`.
- Candidate: `cb412dbf2643a4b886225a5b48f0410ee14b3a4a`.
- Exact diff: `git diff b25e3c80ee26984f12ae98492ee2ae7bd6323735...cb412dbf2643a4b886225a5b48f0410ee14b3a4a`.
- Commit command: `git log b25e3c80ee26984f12ae98492ee2ae7bd6323735..cb412dbf2643a4b886225a5b48f0410ee14b3a4a --format='%H %s'`; one commit. Exact diff/list saved alongside this report.
- Scope is exactly the three new evaluation-module files and two independent test files. Existing producer/model contracts were read for context; no runtime collection implementation is included.
- Standards: AGENTS, domain/issue-tracker instructions, GLOSSARY, ADRs 0001/0002; staged T08 TASK and integration spec. All twelve smell heuristics considered; repository overrides respected and tool-enforced rules excluded.

## Findings (under 400 words)

Hard documented violations: none established.

Judgment/smell findings: none established. The two local CLI entry points, annotation schema, projection functions and explicit-owner checks have current callers and direct contract justification. No speculative runtime abstraction, fallback source version or automatic label inference was added.

Export binds receipt selection to the explicit owner. Message association checks owner, session and request together; events are joined to each selected unique run. Annotation requires the same explicit owner across captures and labels, rejects duplicate capture runs, duplicate annotations and unknown run IDs before writing output, and uses only supplied human verdict/reviewer/rationale fields. Business success is not promoted to a positive quality label.

Export reads persisted summary counters independently of the bounded event tail; it neither reconstructs full counts from that tail nor represents it as complete usage. Missing runtime versions, summary, timing and known optional usage remain absent/null. Export-time source hashes have a separate name and explanatory note, and are never substituted for execution versions. Exact navigation linkage is deliberately unknown rather than guessed from nearby events.

Diagnostics are projected through an allowlist, excluding raw SDK messages, tool arguments, reasoning, provider output and credential keys; event payloads are not copied wholesale. Local exported messages are the already-user-visible history associated with that owner's request. Annotation preserves the fixed capture rather than inventing new runtime evidence. Tests operate on synthetic databases/JSONL, inherit the child execution guard and disable dotenv before export imports. No holdout or live runtime data is read by this review or the test source.

The parent reports 11 controlled tests GREEN. This reviewer executed no tests, builds, installations, services, APIs or product edits. Scope A is export/annotation over existing evidence only; new runtime capture, provider-call identity/usage deduplication and broader graph/version fields remain explicitly deferred to authorized T08-B, not silently accepted or reported as an A omission.

Outcome: zero open Standards findings at cb412dbf2643a4b886225a5b48f0410ee14b3a4a. Independent Spec, same-version integration, T08-B and full-ticket acceptance remain separate gates.

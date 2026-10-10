# T03 contract corrections: independent Standards delta review

## Fixed scope

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T03-native`, clean at inspection.
- Previously reviewed baseline: `e315c387f31ac130e831b37544c7cf3e82f82a4b`.
- Frozen reviewed HEAD: `09ed3a3b54a0831b2774a5338cd0c5cb703c9e88`.
- Exact diff: `git diff e315c387f31ac130e831b37544c7cf3e82f82a4b...09ed3a3b54a0831b2774a5338cd0c5cb703c9e88`.
- Commit list: `git log e315c387f31ac130e831b37544c7cf3e82f82a4b..09ed3a3b54a0831b2774a5338cd0c5cb703c9e88 --format='%H %s'`.
- Five commits: `a881022`, `b27304c`, `be4a436`, `d09b57b`, `09ed3a3`. Full SHAs and diff are saved in adjacent `t03-standards-09ed3a3-commits.txt` and `.diff`.
- Standards sources and twelve smell heuristics remain those recorded in `t03-standards-e315c38.md`; repository overrides and tooling exclusions apply. Contract additions read from `docs/plans/ceres2-local-cloud-integration-spec.md`.

## Findings (under 400 words)

Hard documented violations: none established.

Judgment/smell findings: none established.

The new optional-ingredient behavior has an explicit, parent-authorized source contract: `{ingredient_id, quantity_g?, quantity_ml?, quantity_pc?}`. Runtime directly reads canonical `optional_items`, labels missing quantities as unrecorded, distinguishes an empty list, and includes optional ingredient identities in factual reference validation. It does not fabricate quantities or introduce unsupported compatibility fallbacks. The temporary required/optional union is confined to the existing read-only candidate lookup; original recipe purchase requirements, plans and cart writes remain unchanged.

The Python completion projector now uses one applicable-reference map to reject unrelated primary reference fields before rendering. This resolves the previously forwarded ignored-reference concern according to the newly explicit contract. It introduces no multi-primary answer facility. `policy_ref`, `policy_refs` and `role_boundary` remain independently composable, including with waiting, and continue through the existing policy validation/projection path. Prompt wording agrees with this host boundary.

Public regression source covers nonempty and empty optional facts, unknown quantities, invalid ingredient references, and three unrelated-reference combinations. It checks absence of plan/cart side effects and, for rejected finishes, absence of published messages. These tests are read evidence, not execution by this reviewer.

No speculative helper layers, duplicated production dispatch or ungrounded error recovery warranted a smell finding. The additions are bounded to the two corrected contracts; no deadline, stop, provider, transaction, or T02 ownership changes occur in this delta.

The parent reports dedicated Tester GREEN of 46 tests at this exact pin with no source drift. This reviewer ran no tests, installations, builds, services or real API calls. Standards is clear for this delta; it does not replace independent Spec clearance, subsequent T02 same-version integration verification, or final whole-branch review.

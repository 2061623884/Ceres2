# Spec review: committed core documentation and evidence

**No blocking Spec finding.** Reviewed committed core documentation/evidence only, 2026-10-07. The untracked comparison runner, its tests/documentation and support captures are excluded.

## Fixed identity and evidence

- Documentation commit: `a1ef364813c327585716ba2628914ee53b2f7895`; tree `a83701ee80517afe0e4a0a4250762ad94d44b569`.
- Tested core: `d6a40886926bf203b53c52db27d2177b1b3dcb80`; tree `2fad3a1c8e74593dc19ee929211be0d35a323938`.
- All 248 source hashes match the tested core and previous Spec re-review. Manifest: `7c86cf268f5f4d7055626d6db1e3970d23735bd313ed148f638ede0a02c4368f`. No backend/runtime/frontend/data change exists between those commits; core harness hashes also match.
- All five capture record/output hashes match the committed history. Full-suite raw output states **558 passed in 738.36s**; capture duration is separately 756.438s. The raw launch/guard records independently contain 617 distinct launched Node PIDs, 581 Pi workers, every PID guarded, and no unexpected block.

## Requirement-to-document review

Spec `docs/plans/ceres2-judge-prefetch-spec.md:77–83` requires fixed comparable sources and forbids deriving cost improvement from deduplication. `README.md:21–23`, `PROJECT.md:3–9`, total TASK `:56–62`, and handoff `:94–102,133–144,157–161` correctly distinguish the frozen core, overlapping 152/34 counts, bounded event detail, actual summary counters, unknown usage and unperformed live comparison.

The execution decision requires “只有原定的所有适用验收得到同版证据后才写整体已验收”. Tickets 01–03 remain pending acceptance, ticket 04 remains in progress, and handoff `:32–38,135–144,165–167` explicitly retains live-provider, frontend/browser and user acceptance. No mock-to-live or backend-to-browser substitution is claimed.

The frontend handoff preserves ready/switch semantics, explicit navigation, original request identity, full mixed-result messages and current runtime_summary meanings (`:46–102`). Known preference/catalog/Dream failures remain historical handoffs (`:148–155`), not claimed repairs. Generated build hashes are honestly described as first captured during the full run, then checked afterward (`:159`; core report `:32`).

## Remaining gates

Comparison support requires its separate accepted artifact pin, tests and review. Real-provider configuration/finite sampling authorization, real measurements, local frontend/browser and user acceptance remain open. Final publication must verify its own remote SHA/tree; this review does not certify later publication.

Exact file hashes and evidence checks: adjacent `spec-core-docs-final-pin.json`. No tests, builds, installations, provider calls or shared repository edits performed.

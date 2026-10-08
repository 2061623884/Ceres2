# Real-execution Standards delta review

Reviewed fixed commit `4008faacae169d18de80f6a444f59c47a93915b7` against `fbb44854a412da8d77a7ec30426d240756a9d261`; checked overall scope from `170fac0bc75fcc855897b073337ba218abeb5b7d`. This is a read-only review of the committed delta. I did not run tests, scoring, models, builds, or servers, and did not inspect `.env`, raw/ignored data, private cases, or runtime databases. I did not read the Spec review.

## Hard standards findings

- **Unused optional source argument.** In the reviewed commit, `work/local-followup/04/real-model-20261008/harness_config.py:31`, `read_source_values` defaults `source` to `SOURCE_ENV`, while all three current callers (`config_preflight.py`, `provider_job.py`, `memory_dream_smoke.py`) pass `SOURCE_ENV` explicitly. No current caller relies on omission. This conflicts with `AGENTS.md`'s rule against optional parameters without a current caller.
- **Unused optional manifest-hash argument.** `graph_audit.py:13` gives `audit_graph_result` a `manifest_sha256=None` default, but its sole call in `main` at line 144 always supplies the argument, including when its value is `None`. No current caller relies on omission; the same `AGENTS.md` rule applies.

The two hard findings from the fbb review are fixed: Graph missing/unobserved calls, usage, and audit facts remain `null`; successful results access contract fields directly, preserving observed empty/zero values. Both server entry points now apply the selected environment through a shared helper that clears case-folded current `Settings` aliases first. The curated Tester report `work/local-followup/01/tool-combined-after-real-harness-casefold-fix.md` records 35 passing tests in 14.03s; this review did not independently verify that run.

## Judgemental smells

The earlier dotenv-source/field-list **Duplicated Code** smell is resolved by the shared `harness_config.py` reader. I found no new material smell in this delta. The previously documented independent runner/scorer switch trade-off is unchanged.

# Public 40-case manifest static audit

- Manifest: `evals/ceres2-local-followup-dev.json`, version `ceres2-local-followup-dev-2026-10-08-v1`, SHA-256 `818c3426e0266eabd997d31d4464e9ea22a4fee87df69dcc774674155f7383c5`.
- Case IDs: 40/40 unique; scenario families: 40/40 unique; all cases use `split=regression`; `core=true` 20 and `core=false` 20.
- Fact references: 115/115 fragments resolve in their named current fixture/source files; zero missing path or fragment.
- Check operators: `eq` 92, `min_length` 13, `max` 2, `length` 1. These are supported by the current scorer. The min-length and manifest-integrity checks passed on scorer SHA `879a23361b4a893be594e0df390642cb86e14926026760a3a9600690353e32da` (reports `score-batch-min-length-green.md` and `public-dev-manifest-integrity-green.md`).
- Terminal assertions: 12 `waiting_confirmation`, 3 `waiting_clarification`, 21 `completed`, and 4 `role_choice_required`. Role-choice cases explicitly check `navigation.status=switch` and preserve the current opening role; guide cases assert their terminal state and selected public state invariants are independently checked by the scorer.
- The set is a single-message, public-HTTP development/regression set. Its `expected_behavior` and `fact_sources` guide human semantic review; machine checks do not establish recipe/policy answer correctness or naturalness. The rubric explicitly keeps those labels separate.
- Scope checked: current public manifest, static fixture/source IDs, runner/scorer contracts, and current rubric only. No acceptance/holdout case text was read.

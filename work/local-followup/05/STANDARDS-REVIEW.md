# Standards review

Baseline `170fac0bc75fcc855897b073337ba218abeb5b7d`; candidate `e855d691d0a446c9e5385196134b55f2ec609320`. Reviewed the three-dot diff; commit list contains only `e855d69 Add local evaluation workflow and versioned testing evidence`. Scope covered the seven evaluation modules, three public tests, docs/evals, permitted work evidence, and harness sources. This was read-only; I did not run tests, lint, typecheck, build, install, services, models, or scoring, and did not read temporary/independent acceptance bodies, `.env`, caches, or runtime databases.

## Hard standards violations

None found against the applicable `AGENTS.md`, issue-tracker/domain rules, glossary, and ADRs. This review does not establish Spec compliance or overall acceptance.

## Judgemental baseline smells

- **Duplicated Code** — `compare_runs.py:45–58`, `score_batch.py:288–300`, `report_batch.py:57–74`, and `failure_intake.py:50–66` repeat capture/annotation schema checks, `RunAnnotation.model_validate(...)`, and owner/run identity matching. Example: `if (annotation.owner_id, annotation.run_id) != identity`. Consider extracting this shared validation shape for these existing callers.
- **Repeated Switches** — runner dispatches `turn`/`confirm_plan`/`repeat_confirmation` in `run_baseline.py:251–360`; scorer dispatches the same operation names in `score_batch.py:213–278`. Example: `if op == 'confirm_plan'` and `if step['op'] == 'confirm_plan'`. A shared operation map/definition could keep additions aligned across execution and scoring.

All 12 fixed smell-baseline categories were considered; only the two judgement calls above were clear enough to report. No tests or tooling checks were repeated; their evidence remains the Tester’s responsibility.

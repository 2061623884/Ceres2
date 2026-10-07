# T07 Mercury hookup: independent Standards review

## Fixed scope

- Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_t07_aftersales`.
- Baseline: `ccf272b752f096ce0d80f7d0a4f29b19c05b0a77`.
- Reviewed product pin: `79a7efffadaeac3706dc54db2066f6ababcb6848`.
- Observed clean HEAD: `24ee4d03268cfd16b9a171acc7fe6dced465768c`; only subsequent difference is `work/local-cloud-integration/t07/handoff.md`.
- Exact diff: `git diff ccf272b752f096ce0d80f7d0a4f29b19c05b0a77...79a7efffadaeac3706dc54db2066f6ababcb6848`.
- Commit command: `git log ccf272b752f096ce0d80f7d0a4f29b19c05b0a77..79a7efffadaeac3706dc54db2066f6ababcb6848 --format='%H %s'`.
- Commits: `93034dd288f75c546aadbbac0437a815e46dcf41` (public HTTP regressions); `79a7efffadaeac3706dc54db2066f6ababcb6848` (category/deadline hookup). Full diff and commit list saved alongside this report.
- Standards: `AGENTS.md`, `docs/agents/domain.md`, `docs/agents/issue-tracker.md`, `GLOSSARY.md`, ADRs 0001/0002. Context: T07 TASK, integration spec, prior T07 Standards and Spec reports. Repository rules override smell heuristics; tooling-enforced checks excluded.

## Findings (under 400 words)

Hard documented violations: none established.

Judgment/smell findings: none established. All twelve requested smell heuristics were considered. The small adapter change has a current graph caller and directly implements the assigned shared-boundary contract; it does not introduce speculative infrastructure.

`backend/app/mercury/tools.py` now uses the same `policy.CATEGORIES` for advertised schema and argument validation, covering all ten source categories without duplicating a second production list. Public HTTP regression independently enumerates those ten categories, checks actual worker-boundary calls, and confirms no aftersales receipts.

`backend/app/mercury/graph.py:200–203` forwards its existing absolute deadline through the adapter into shared policy retrieval. The existing chain starts from `accepted_at + 15`; model time therefore reduces retrieval time. The ordinary Mercury graph path no longer activates policy/worker standalone 30-second defaults. Worker lock admission, pipe writes/reads and response checking consume that same deadline. Existing timeout cleanup terminates only the owned retrieval worker, while the graph's outer boundary rejects late results.

The delta changes no graph state schema, checkpoint/resume flow, owner identity, selection/responsibility fences, query publication transaction, read-only dispatch gate, proposal/confirmation behavior, status mapping, model configuration or business writes. It adds no new cancellation signal; existing provider cancellation, bounded retrieval cleanup and fenced publication remain intact. This is preservation established by static comparison, not new end-to-end cancellation certification.

The dedicated Tester reportedly completed `t07-mercury-policy-ready-green`: 63 passed, 38.24 seconds, exit 0, no product drift at this pin. This reviewer ran no tests, installations, services or real API calls. The earlier start-only execution is not validation evidence.

Conclusion: zero open Standards findings for this hookup delta. Earlier T07 core findings remain resolved at their separately reviewed pin. Whole-branch review from `37c98400e7152b89e4a58f02fff3bceaa73b0eac` and final exact-pin aggregate acceptance remain separate obligations.

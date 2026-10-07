# Ceres2 integration workspace recovery

This is the independent cloud integration checkout, not the user's desktop or original dirty worktree.

- Checkout: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/Ceres2`
- Branch: `ceres2/local-cloud-integration-20261007`
- Frozen baseline: `37c98400e7152b89e4a58f02fff3bceaa73b0eac`
- Frozen incoming: `6734c7fe79e670df2dae12b065dcc49c0b10a307` (`ceres2-incoming-20261007-frozen`; never move this tag).
- Resume with [current TASK](tasks/ceres2-local-cloud-integration.md), [spec](docs/plans/ceres2-local-cloud-integration-spec.md), and its per-ticket dependency links.
- Existing root AGENTS.md is preserved. Its historical “only 16 tickets/no remote” and old cloud frontend exclusions are superseded for this explicitly approved nine-ticket integration. All identity, authority, isolation, Tester-only execution and no-original-overwrite rules still apply.
- The root agent coordinates publication with authorized tools. No worker shell push, no main merge, no force operations, reset/stash/cleanup of original worktrees, no real API/env/database access, and no holdout reading.
- Source models and settings stay unchanged. All new official DeepSeek paths must preserve thinking disabled for exact official host only. Approved budget is 15 seconds total / 5 tool rounds; actual baseline Guide API was 30 seconds, so T01 must implement and verify 30→15 (Mercury already uses 15).
- Product worker ownership is per file and worktree. Only the Merger writes the integration branch; review fixes return to one designated implementer. Read `git status --short` and exact HEAD before resuming, never assume a previous checkout is clean.
- All tests/install/build belong to the independent Tester. Historical reports do not verify this integration. Final reviews compare `37c98400e7152b89e4a58f02fff3bceaa73b0eac...HEAD` and preserve missing evidence.

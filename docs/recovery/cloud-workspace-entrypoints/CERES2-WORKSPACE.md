# Ceres2 cloud workspace

Current program: integrate the local optimization into the approved cloud architecture.

- Repository: `ceres2_integration_20261007/Ceres2`
- Integration branch: `ceres2/local-cloud-integration-20261007`
- GitHub: https://github.com/2061623884/Ceres2
- Fixed cloud baseline: `37c98400e7152b89e4a58f02fff3bceaa73b0eac`
- Fixed incoming delivery: `6734c7fe79e670df2dae12b065dcc49c0b10a307`
- Spec: `docs/plans/ceres2-local-cloud-integration-spec.md` inside the repository.
- Current task state: `tasks/ceres2-local-cloud-integration.md` and its linked tickets. This root guide is an entry point, not a second progress tracker.

## Resume safely

1. Check the actual checkout, `git status`, branch, commits and worktree inventory. Retain every existing patch.
2. Read the task index, relevant evidence and applicable repository rules before resuming a ticket.
3. Use a single merger and an independent Tester. Reconfirm active worker identities with the main coordinator; historical names are not live routing instructions.
4. Raw test records live in `ceres2_integration_20261007/test-evidence/`; curated deliverable evidence lives in repository `work/local-cloud-integration/`. Start-only or interrupted records are not passes.
5. Publication payloads and receipts live beside the repository in `ceres2_integration_20261007/`. Verify remote commit and full tree equality before claiming a push. Local and connector-generated commit SHAs can differ; the receipt records their identical tree.

Keep the original branches, the user's local main and its 53 uncommitted items untouched. Current cloud work does not inherit credentials, running databases, indexes or holdout data from that local checkout. Main is not authorized for automatic merge.

If this checkout is absent in a future environment, read the verified integration branch and published task/evidence documents before creating a new checkout. Do not guess a deletion cause or claim unfinished local changes are recoverable without evidence.

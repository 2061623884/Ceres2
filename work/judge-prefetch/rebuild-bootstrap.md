# Cloud reconstruction baseline — 2026-10-07

The integration branch starts at the real published Ceres2 main commit `4bed9c891261e382122d424825b649989ea92c92`, with tree `73bb2a44f22fa504448fbc19ab1fb6fec095d724`. A normal public GitHub clone retained its existing history; no synthetic ancestry or previously lost cloud commit was created. The initial checkout was clean. Full tracked-file hashes and the input archive hash are in [rebuild-baseline.json](rebuild-baseline.json).

The approved four-ticket implementation is new work. Existing published implementations and historical verification remain intact and retain their original applicability. Frontend implementation is outside this reconstruction's authorized scope; the current plan records backend/runtime delivery and the user-owned frontend handoff.

## Repository obligations

- `tasks/` remains the canonical local tracker. Follow each current TASK and its linked spec, glossary and ADRs before making business changes.
- All dependency installation, test, lint, typecheck and build commands are reserved to the dedicated Tester. Implementers prepare a failing test, request the independent red run, then request green/regression verification after implementation.
- Assign a single writer for each shared entrypoint, schema, prompt and fixture. The dependency frontier is 01 → 02 → 03 → 04; product implementation of dependent tickets must wait for the predecessor's contract and verification handoff.
- Use one integration branch and separate implementation worktrees. The integrator owns merges and traceable commits. Independent Standards and Spec reviews are read-only.
- Preserve Python business authority, explicit confirmation, owner/request isolation and simulation-only claims. Do not reuse credentials, old runtime databases or dependencies from other projects.
- Latest user authorization for this dated reconstruction and separate-branch publication overrides only the historical restrictions on a remote/push and the old 16-ticket-only statement; it does not authorize frontend changes, deployment, merge to main or destructive cleanup. See the current plan for the precise dated authorization and scope.

## Existing run guidance

Read `docs/NEXT-EXPERIENCE-HANDOFF.md` and `backend/pyproject.toml` before preparing a Tester run. Python dependencies are locked in `backend/requirements.lock`. Pi lives at `runtime/pi/`, with its own lockfile and build/typecheck scripts. No lint script is configured in the published baseline. Historical reports are not proof for this new candidate.

The bootstrap owner did not run installation, tests, build, typecheck, lint or live providers.

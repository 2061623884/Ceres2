# T06-A CLI correction: independent Spec re-review

Fixed candidate: `d37b5e8c39ea47e7a330ea4744fbb553759aa8ba`; prior reviewed pin: `826d71e3d5e4de4fd258942a2123781a20f29780`. Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T06-graph`. HEAD had advanced to `2ad494c424ec5f7fda348176063e24376430cd1a`; only the fixed candidate/delta was inspected. Commands saved alongside: `git diff 826d71e3d5e4de4fd258942a2123781a20f29780...d37b5e8c39ea47e7a330ea4744fbb553759aa8ba` and `git log --format=fuller 826d71e3d5e4de4fd258942a2123781a20f29780..d37b5e8c39ea47e7a330ea4744fbb553759aa8ba`.

## Result

The previous P2 standalone CLI termination finding is resolved by static inspection. No new Spec finding identified in this delta.

`backend/app/knowledge/cli.py::supervise_graph_job` launches a separately killable process. Startup and communicate consume the original absolute deadline; timeout or keyboard interruption kills the entire graph job, including blocked executor threads, without adding another synchronous wait budget. A daemon reaps the process. Query CLI still defaults to 15 seconds; Guide's existing KnowledgeService worker budget/cancellation path is unchanged.

Offline build now requires explicit finite positive --timeout-seconds and rejects a Guide-style --deadline. This is the newly approved finite offline-build contract, not a reinterpretation of the failed earlier pin. Before starting a rebuild, the parent removes the old manifest; error, interruption or late completion removes any newly written manifest. Partial artifacts cannot pass existing graph manifest validation. A fully timely completed child alone leaves the completed build manifest.

Regression source exercises a real child blocked by an executor thread, checks bounded parent return/child termination, and checks invalidation of an old manifest during timed-out offline build. Existing library-harness build timeout is explicitly 120 seconds, while Local/Global query scopes remain 15 seconds. Error traces remain private; structured failure observations preserve unknown call counts/usage rather than inventing zero.

Removing the unused expected revision parameter does not remove post-query provenance validation: graph.search still captures the actual initial manifest and revalidates its revision after execution.

## Limits

No tests, installation, model/API, service, or build execution by this reviewer. Tester reports 40 GREEN on this pin using official GraphRAG 3.2 build/Local/Global with controlled provider and no-weight encoder; that is adapter/library evidence, not real BGE execution or retrieval-quality acceptance. Later bge.py compatibility edits are excluded. Pi integration and final same-pin whole-branch acceptance remain separate.

# T08-A independent Spec review

Fixed HEAD: `cb412dbf2643a4b886225a5b48f0410ee14b3a4a`; baseline: `b25e3c80ee26984f12ae98492ee2ae7bd6323735`. Clean worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T08-export`. Commands: `git diff b25e3c80ee26984f12ae98492ee2ae7bd6323735...cb412dbf2643a4b886225a5b48f0410ee14b3a4a` and matching `git log --format=fuller`; outputs saved alongside.

## Result

Zero new missing, incorrect, or out-of-scope behavior findings for the explicitly bounded A stage.

- T08-A “显式owner过滤及精确run/request/session join”: export requires a nonempty owner, filters receipts by that owner, joins journal rows by the receipt's run_id and messages by owner/session/request. It does not guess nearby navigation linkage; entry_judgment remains null. Annotation rejects cross-owner capture/labels, duplicate capture run IDs, duplicate annotation IDs and unknown run IDs before writing output. CLI tests use synthetic databases/files, not live data.
- T08 “显式owner 导出/人工标签，无自动质量正标签”: export sets labels=null. Only explicit schema-validated human annotations set verdict, rationale, reviewer, timestamp and other required fields. Receipt completion/cart acceptance never generates a quality pass or training action; unreviewed failures remain unlabelled.
- Spec “完整 runtime_summary 独立于裁剪后的详细事件尾部”: the exporter reads the persisted summary's existing baseline counters and policy/interim observations directly, separately projects the diagnostic tail, and labels that tail as incomplete. It does not reconstruct missing counts or usage from events. Safe diagnostic projection excludes raw SDK/provider text and tool arguments while exporting the owner's already-public message history separately.
- T08-A “缺失时间/usage/runtime_version保持unknown”: absent summary/runtime version and unknown event/start times remain null; stored runtime fields are copied rather than manufactured from the current checkout. export_source_snapshot hashes are explicitly labelled export-time evidence, distinct from execution version. Existing usage/cost nulls are preserved.

The five-file scope consists solely of new evaluation modules and independent tests; no production HTTP route, authorization, DB schema, runtime or frontend change is introduced.

## Limits and handoff

No tests, installs, CLI execution, model/API calls or real database reads by this reviewer. The reported 11 controlled GREEN cases are Tester evidence, not this static finding. B-stage provider identities/usage deduplication and expanded runtime capture are explicitly deferred, not A omissions. When B consumes the later GraphRAG/provider summary contract, its exporter projection must be reviewed against that newer schema; this clearance covers the existing b25e3c8 policy/interim summary only. Final same-pin integration and whole-ticket acceptance remain separate.

# T04 safe diagnostics: independent Standards delta review

Worktree: `/workspace/scratch/0c1b4cfa2ef3/ceres2_integration_20261007/T04-interim`, clean at inspection.

Exact diff: `git diff 3064fe1d53bba45e88fd23d471fd9474580e5974...0c77e59f36649dc27e98e1c90552fc8ecf0c4ab1`.

Commits: `git log 3064fe1d53bba45e88fd23d471fd9474580e5974..0c77e59f36649dc27e98e1c90552fc8ecf0c4ab1 --format='%H %s'`. Four full SHAs and exact diff saved alongside this report. Product fix is `39adf78abcfbc49f4efb6b25cb066fbd6fbedb4b`; its successor `0c77e59f36649dc27e98e1c90552fc8ecf0c4ab1` changes tests only.

Applicable standards, T04 contract and smell baseline remain those in `t04-standards-3064fe1.md`. The parent-approved shared waiting fixture correction is included explicitly rather than treated as a production relaxation.

## Findings

The prior P2 cause-preservation finding is resolved. Both new catches retain the existing bounded diagnostic projection, which exposes allowlisted kind/code/transport fields and a SHA256 fingerprint rather than raw error text. Malformed structured candidates emit a distinct rejection diagnostic without claiming an auditor call. Actual auditing now separates approved, rejected and error outcomes; malformed JSON/schema and provider/abort failures retain safe diagnostic identity. Incomplete audit summaries initialize outcome/diagnostic/usage/cost as unknown.

The verdict check remains fail-closed and is grounded in the exact three-boolean audit contract. No new candidate text, raw verdict, provider body, key or reasoning is published. Existing guarded same-model auditing, deadline/cancellation, stable-ID publication and independent history transaction are unchanged.

The shared waiting fixture merely removes product_refs from a waiting result, aligning it with T03's accepted primary-reference contract. New test source exercises candidate parse, audit parse/schema, actual loopback HTTP401 and ordinary rejection; it checks safe diagnostic fields, no private-marker/key/provider-message leak, accurate audit counts and no cart changes. The real-Node relay/guard fix remains intact from the baseline.

Hard documented violations: none open. Judgment/smell findings: none added. This closes the previous T04 Standards finding at 0c77e59.

The owner reports diagnostic RED→GREEN and 17 cases plus TypeScript/build at product pin 39adf78; the expanded final test run at 0c77e59 is pending and is not inherited as passed. No tests, builds, installations, services, APIs or product edits were performed by this reviewer. Independent Spec, final same-pin aggregate evidence, frontend integration and whole-branch review remain separate gates.

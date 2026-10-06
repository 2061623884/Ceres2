# TASK07 expression candidate and comparison readiness

## Scope

Released business-ready baseline: c3747dd1148edc850e090d45b6bbb0f58aa96aa1 (TASK06 controlled release, already including04/05/08/09 composition). The only production change is three string values in backend/app/prompts/experience.json: the Keke and Momo expression prefixes and result_introduction. The role business sections, context selection, tools, data, model selection, host facts, general-claim validator and source/lifecycle contracts are unchanged.

The instructions now request result-first Chinese, only a necessary next step, no repeated current question or courtesy summary, optional restrained emoji, and context-appropriate connective wording. They explicitly avoid a generic shopping invitation after an application receipt or a success celebration for unknown/no-match/failure. Concision cannot remove policy sources/conditions/unknowns/simulation labels or the distinction between a submitted application and approval/payment. The introduction remains at most two separately validated reference-bound units, never unvalidated factual paraphrase. These are intended behavioral instructions, not a demonstrated natural-language improvement.

## Frozen artifacts

- baseline/experience.json: exact released prompt bytes; baseline/{keke,momo}-expression.txt: composed introduction system strings.
- baseline/source-manifest.json: immutable baseline commit, clean tracked-source state, hashes for business/runtime/UI code, public tests, static fixtures/import scripts and dependency declarations/locks. No credentials, local configuration or private holdout was read.
- candidate/: exact candidate prompts and source manifest, explicitly listing the new public test and dirty production path.
- public-cases.json and public-nodes.txt: fixed public development/regression groups and all selected parametrizations, frozen before candidate edits. These are not independent holdout.
- comparison-protocol.md: full visible-turn scoring, immutable business/model/data controls, future paired real-sample order, failure retention, clock domains, usage provenance and separate evidence gates.
- prompt-lengths.json: Unicode code-point sizes only. Candidate instructions are longer. Characters are not tokens; no token/cost/latency reduction is asserted.

The configured real model/provider remains unknown because local credentials/configuration were not read and no external provider was called. Controlled request bodies identify the synthetic model used by the Tester. Existing fixtures instantiate fresh isolated stores/orders; their exact definitions are hash-frozen. A future live comparison must freeze actual model configuration and order clocks/states before sampling, not infer them from this controlled evidence.

## Sole-Tester evidence

Evidence lives under integration work/next-experience/10/runs/ (record.json plus output.log):

- next07-baseline-red: fixture extraction failed because SDK user content is text blocks, not a string. This is a harness failure, not product RED; the extraction was corrected before proceeding.
- next07-baseline-public: the fixed37 public cases pass on the before prompt.
- next07-baseline-red-corrected: both roles preserve host facts, immutable business results and idempotent replay; intended request-contract assertions then fail because the new instructions are absent. Bounded actual generation/validation requests, visible facts and null-usage metrics are retained.
- next07-candidate-contract: both new role cases pass (2/2), retaining actual request messages, visible facts and usage-null metrics.
- next07-candidate-public: the same fixed37 public cases pass with unchanged source during execution. Baseline elapsed42.97s and candidate40.62s are single controlled test-process durations, not user-visible latency or improvement evidence.

The new test observes actual provider-request contents and public result-introduction SSE, immutable cart/application readbacks and replay behavior. It deliberately scripts the same short connective for both candidates. Its equality checks establish factual rendering and instruction delivery, not model adherence, user preference or language quality. Its two observed calls are one generator plus one validator for one scripted unit; they do not prove a production call reduction. Missing usage is null, not zero. Controlled timing is retained for mechanics, not treated as an application SLA.

## Remaining gates

Real-provider before/after transcripts and token/latency comparison, actual browser full-visible-turn capture/timing, blind human natural-language review, independent private holdout and user acceptance are unrun. No external acceptance or measured quality/efficiency benefit is claimed. Full-candidate review/freeze and formal TASK status belong to the parent/integrator. No push was performed.

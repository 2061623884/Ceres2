# TASK05 controlled candidate

Evidence is retained by the sole Tester under integration `work/next-experience/10/`: named public runs in `runs/<name>/{record.json,output.log}`, checks in `checks/<name>/{record.json,output.log}`, and `next05-prompt-byte-equivalence.json`.

## Evidence before composition

- Baseline: ec221f939ef711158f0cd9109d88feec0c94089e. Four fixed public journeys passed; social-aside relevance RED failed because the actual provider request received unnecessary recipe-purchase tools. Evidence: next05-baseline-red and checks/next05-baseline-runtime.
- First minimal GREEN: 11/11 context and shared-policy cases, runtime typecheck/build. Evidence: next05-green-01 and checks/next05-runtime-green.
- Mixed request: initial chat hint recovered constrained shopping after existing Pi guide_request with one Kev call. Independent factual recipe RED caught an over-trimmed read-only tool. Evidence: next05-mixed-green-recipe-red.
- Minimal recipe fix preserves the exact original read/display clause and search_dishes for factual QA without adding proposal tools. Meaningful regression batch:89/89 in115.30s, unchanged source, runtime typecheck/build passed. Includes all7 context cases, clarification, dish/multidish, semantics including30-second deadline, snack/safety, policy, explicit return and Mercury/aftersales. Evidence: next05-regression-02 and checks/next05-runtime-02.

All executions above were by the sole Tester, using fixed isolated data and controlled model transport through actual Pi/public API/SSE. This is not a real-provider quality comparison. Existing output style is intentionally preserved; no token/latency improvement is claimed.

## Composed candidate

- Tested checkpoint7590b80 merged04 integration fde3e71 as5be688f. Only worker prompt conflict was resolved by preserving04's approved beverage/flavor/spec clauses verbatim in the JSON source. Baseline comparisons remain against the same fixed isolated scenarios;04's separate business changes are not counted as modularization improvements.
- Composed public regression:77/77 in71.15s, runtime build/typecheck passed, unchanged source. Evidence: next05-composed-public and checks/next05-composed-runtime.
- Supplemental byte equality against fde3e71: complete COCO prompt3208 characters and Mercury prompt629 characters reconstructed exactly with matching hashes. Evidence: next05-prompt-byte-equivalence.json. This does not replace public behavior or real-model quality evidence.
- Synced09 product integration d74d82a as46e41bc, retaining failure narration, response-loss and receipt truth without changing05 runtime/prompt files. Final targeted combined tests:26/26 in25.22s, unchanged source. Includes09 shopping return, corrected inherited cross-role memory/lifecycle, all7 context cases and shared policy. Evidence: next05-final-composed.
- Synced parent docs-only release7dfa3e6 after those checks. No additional production or test edits.

## Remaining gates

Controlled candidate is ready for parent review/release. Real provider samples, both real pages, language-quality review and user acceptance remain unverified; no complete semantic-quality or real-world acceptance claim. Formal task status is maintained by the parent.08 activity adapter is not part of this candidate and will compose independently; its two-file callback contract was handed to08 after its own RED/GREEN.

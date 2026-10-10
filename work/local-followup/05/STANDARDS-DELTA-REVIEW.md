# Standards delta review

Baseline `e855d691d0a446c9e5385196134b55f2ec609320`; reviewed commit `4e021e46e8c16671ae1366ec09c11f39bad01bd6`; task base `170fac0bc75fcc855897b073337ba218abeb5b7d`. I reviewed the e855-to-final delta and the applicable repository standards, domain guidance, glossary, ADRs, task, and plan. This was read-only; I ran no tests or other validation commands and did not inspect secrets, ignored acceptance inputs, or runtime data.

## Hard standards violations

None found. The changes stay within the evaluation/reporting task. The `TypeError` recovery in `score_batch.py` is supported by the declared non-comparable-check contract and a reproducible recorded failure; it records an evidence gap and preserves the exception type/reason. Unknown check operators still propagate as configuration errors. The added amount checks use declared catalog and captured business evidence, while missing values remain unknown rather than receiving defaults. Product implementation files remain outside this delta.

## Judgemental smells

- **Duplicated Code — addressed.** `batch_runs.annotation_for_capture` now owns the repeated capture/annotation schema validation, model parsing, and owner/run identity check used by compare, score, report, and failure intake. This is a narrow helper for four existing callers and preserves their context-specific errors; it does not add a speculative framework.
- **Repeated Switches — retained as an accepted trade-off.** `run_baseline.py` dispatches HTTP actions while `score_batch.py` independently evaluates their captured effects. Sharing handlers or routing evaluation through execution would compromise the scorer’s independent check. With three contract-defined actions, a polymorphic dispatch layer would add abstraction without a current caller. New actions still require independently maintained execution and scoring behavior, so the operation cases remain a synchronization point.

No other fixed-baseline smell became clear in this delta. This is a Standards result only; it does not establish Spec compliance or overall acceptance. Relevant verification evidence is recorded by the dedicated Tester in [the final combined report](../01/tool-combined-reviewfix-final.md).

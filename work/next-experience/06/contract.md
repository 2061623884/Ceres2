# TASK06 result-first expression contract

## Business authority and transport

Structured question/filter/selection and purchase/refund confirmation endpoints keep their existing deterministic implementation and receipts. The browser first applies and renders that result, then asks for an introduction by its exact persisted source reference. No original user text is reinterpreted; there is no Kev call or business tool in the expression process. Existing text-turn result receipts can also be introduced, including an authoritative empty-search outcome. A retained old plan alone is not a new result.

`POST /api/v1/guide/sessions/{session_id}/result-introductions` accepts `source_kind` (`question_answer`, `purchase_confirmation`, `turn`, or `aftersales_receipt`) and `source_id`. Receipt lookup checks owner/session/task/version and current role. The Mercury receipt convenience route also checks the case before resolving the canonical guide journal. The response returns the existing run identity shape. `GET /runs/{run_id}/stream`, event sequence recovery, and explicit stop use the existing guide run transport. Repeated source admission returns the same expression run; it never generates again or repeats a cart/application write.

The implementation adds no database tables or general workflow engine. It reuses `GuideTurnReceipt`, `GuideRunEvent`, and Keke `GuideMessage`; Momo introductions remain in their expression receipt and never enter Keke message history. Pure introduction messages are excluded from bounded semantic-dialogue receipt lookup. Original business receipts are immutable and untouched by expression success/failure.

## Smallest safe incremental unit

One newline-delimited JSON clause contains exactly `text` and `fact_ref`. At most two short clauses and distinct references are accepted. The reference must exist in the exact committed source's host-built fact map. Price, stock, product identity, execution and refund statements are rendered only from that map. Model `text` is only a natural non-business connective and passes the existing, byte-identical `CERES_GENERAL_CLAIM_CHECK` boundary before publication. A valid reference is never permission for arbitrary factual prose.

The Pi expression process has no tools. It receives only the result facts and expression instructions; its generator runs while complete units are queued for sequential general-claim validation. Each approved unit is independently persisted and committed to SSE while later generation can still be ongoing. Malformed objects, unknown/repeated references, extra fields, excessive units, uncertain/failed validation, provider failure or deadline stop expression. Already published validated units and authoritative business results remain.

This deliberately constrains factual wording to host-rendered summaries while allowing validated connective wording. It does not claim unrestricted model-authored factual prose. The cost is one generator call plus one validation call per attempted clause (maximum two), sharing a bounded total deadline (30 seconds Keke, 15 seconds Momo). Metrics separately journal generation/validation calls, usage, generation start/end, and unit publication time. The SDK observer reads only provider-reported numeric usage, before SDK zero defaults or cache subtraction. Missing fields stay null; explicitly reported zero remains zero. Input tokens are labeled provider prompt-total (including cached input), with separate cache counters that must not be added to that total again. Provider/unreported provenance is explicit; a provider usage object does not imply every field was reported. No speed, cost or real-provider quality improvement is assumed. Deadlines are rechecked for every buffered frame and at the final publication fence after database waits. A blocked SQLite write can delay terminal persistence; this is not a promise that every HTTP response or database operation completes within30 seconds.

## Freshness and UI

Each publication fences the current owner/session/task/version, opening/role metadata, newer user/run admission and non-introduction message sequence. Mercury additionally fences selected order, selection/responsibility/intent version, active query and a digest of its existing message history, including a pre-authorized query completed between checks. A new task, role close/switch or newer turn stops stale expression. Browser interaction/view epochs and AbortController fence local delivery, including navigation away and back with the same task version.

Introduction loading is separate from business typing/confirmation. Cards, proposals and authoritative receipts remain usable during expression. Explicit stop or a later interaction aborts only the introduction. Expression failure says the introduction did not complete and the result/receipt is retained; it never presents business failure or invites repeating a committed transaction. Normal business restoration does not merge expression receipts as new shopping snapshots.

## Evidence scope

All execution belongs to the sole Tester. Evidence is indexed in integration `work/next-experience/10/`.

- First public RED: missing expression endpoint (404 instead of 202).
- First GREEN: actual loopback HTTP/SSE, real Pi SDK, controlled generator held open until first approved client-visible unit. Proven order: card result, generation start, validation, first client unit, generation end.
- Receipt RED/GREEN: unsupported purchase source, then rejected forged payment/delivery wording with unchanged committed cart and idempotent receipt.
- Public matrix: 16 controlled cases passed, including actual socket disconnect/reconnect sequence continuity, malformed/unknown references, fabricated facts/uncertain validation, explicit stop, newer task/turn/close, actual 30-second timeout, text and empty-search sources, refund receipt/ownership and no repeated writes.
- App and receipt DOM REDs reproduced missing post-render admission. Both GREEN harnesses now cover result-first rendering, usable controls, incremental text, sequence deduplication, failure/stop/navigation and unchanged business counts.
- Initial broad backend checks passed107 cases. After the token-provenance correction, current-source disjoint checks passed109 cases (3 usage/timing,4 reviewer-fix and102 selected stream/context/guide/purchase/aftersales cases), including all22 new stream cases. Runtime/frontend builds and strict checks passed.33 inherited DOM/client scenarios plus2 new06 scenarios passed; two legacy fixed-file compiler dependency setup failures were closed with complete temporary dependency compilation, with no behavior assertion or repo compiler change.

Controlled provider/DOM evidence is not a live-provider sample, real browser verification, natural-language review or user acceptance. Those remain separate gates. Formal TASK status is maintained by the parent.

## Trigger matrix and deliberate boundaries

- Category, filter and product/quantity question answers: introduce the committed command snapshot after its cards or prepared plan render.
- Text results: introduce only a newly published question bound to that turn's assistant message, new product evidence/cards, authoritative no-match result, new/replaced plan, or that turn's confirmation. Ordinary/general/policy/memory replies and retained questions/plans do not start another introduction.
- Whole-plan and per-row cart confirmation: introduce the exact immutable confirmation key after a visible simulated cart receipt.
- Aftersales application confirmation: introduce the exact owner/case receipt, preserving requested/unapproved/not-paid-out status.
- Legacy standalone quantity/revision/quote/partial controls retain immediate deterministic feedback and cancel stale narration. They do not request an extra model call for every adjustment. This is the bounded06 trigger scope, not an unfinished07 feature;07 is expression refinement.
- History/restoration/reconnection never starts a new business action or generation. Existing expression events/messages are reused.

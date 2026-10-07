# Bounded, human-operated old/new comparison

This is a bounded smoke/comparison recorder, not a complete performance experiment
or ticket 04 acceptance. Its default command is inert.

**Controlled verification, 2026-10-07:** 22 tests passed, including the current app
and actual Pi SDK/validator against an owned loopback provider with uppercase and
lowercase configuration aliases. Those two smoke parameters also passed in a
separate affected run; they are included in the 22, not added to it. All used fake
credentials. **Real provider execution, real usage/cost, language quality,
browser behavior and user acceptance remain not run here.**

- [Curated verification](04-comparison-support-verification.md)
- [Final source/build/guard pin](04-comparison-support-final-source.json)
- [Retained RED/GREEN history](04-comparison-support-history.json)

The raw final-full-02 and alias-green-01 capture records are retained locally
for audit, not shipped in a fresh checkout. Use the curated source/history
files above for their recorded commands, results, hashes and guard evidence.

The core's 558-test gate remains separate. The unavailable f45c4ff runner and the
legacy hard-coded DeepSeek 41-case runner were not restored or reused.

## Safety and comparison boundaries

- Preview must not import application settings, read `.env`, start a service,
  contact a provider, or create an output file.
- Actual provider transmission is for the user to trigger manually. Agents must
  not run this entrypoint against real credentials or export those credentials.
- Execution requires explicit source directories, revisions, build provenance,
  a finite synthetic case selection, repeats, order, and a user-provided total
  elapsed-time limit. No spending allowance or billing default is supplied.
- Source checkouts must be independently prepared. Existing dirty repositories,
  running services, databases, owners and sessions are not comparison fixtures.
- Each sample must get its own temporary database/checkpoint path and a fresh
  application-created owner/session. Only owned subprocess groups may be stopped.
- Stopping locally cannot cancel work already accepted by a remote provider and
  cannot guarantee that billing stops at the local elapsed-time boundary.
- A real application lifespan starts `MemoryWorker`; any resulting memory calls
  are part of the experiment's exposure. Its independent configured models must
  be retained and recorded, not silently changed to the main model.
- The current public Guide result does not expose complete provider HTTP counts,
  main-call token usage or prices. Unobserved values must remain `unknown`.
  Tool rounds and SDK lifecycle events are not provider HTTP request counts.
- The original `4bed9c891261e382122d424825b649989ea92c92` baseline lacks the
  candidate's official-DeepSeek thinking-off change. Combined with changed
  prompts and policy behavior, this is a **bundled old/new comparison** unless
  actual payload settings have been independently aligned and verified. Never
  attribute the whole difference to prefetch or infer savings from fewer reads.
- A small synthetic sample cannot establish stable P95, quality acceptance,
  browser behavior, full ticket 04 acceptance, or memory/Dream acceptance.

Current source contracts and acceptance boundaries:
[execution decisions](../../docs/REBUILD-DECISIONS.md),
[ticket 04](../../tasks/ceres2-judge-prefetch-04-candidate-evidence.md), and
[local handoff](../../docs/JUDGE-PREFETCH-HANDOFF.md).

## Prepare two frozen sources

Use separate, deliberately prepared POSIX checkouts/worktrees. Do not use the
user's dirty working repository or existing database. Select the original
baseline 4bed9c891261e382122d424825b649989ea92c92 and the exact accepted candidate
from the main handoff. Keep that source selection fixed while using the
separately published runner; later documentation-only commits need not change
the compared product source.

Each source needs its verified backend/.venv/bin/python, locked Pi dependencies,
and matching runtime/pi/dist build. Installation/build verification remains the
dedicated Tester's responsibility. The runner never installs, builds, repairs
a checkout or attaches to/kills a pre-existing application service.

The following commands are inert; descriptions read local Git/files without
importing the app or loading its configuration:

    python3 work/judge-prefetch-rebuild/live_compare.py
    python3 work/judge-prefetch-rebuild/live_compare.py --describe /absolute/baseline
    python3 work/judge-prefetch-rebuild/live_compare.py --describe /absolute/candidate

A description returns a source object containing directory, revision/tree,
product/runtime source, dist, static facts, prompt-related files, numeric budget
declarations and lock fingerprints. Dirty product source, missing builds and
unsupported source shapes fail closed. Reviewed policy/timeout literal
extractions are understood without executing their modules.

The description intentionally leaves build_revision null. From the actual
successful build record, complete three fields in each source object:

- build_revision: the exact selected source revision
- build_source_sha256: that build's runtime-source fingerprint
- build_dist_sha256: that build's produced-dist fingerprint

They must match the selected source. Copying current hashes into these fields
does not prove an old dist came from current source. This is a consistency check
of a human-supplied build attestation, not independent build certification.
Retain the Tester's build evidence.

## Freeze the finite plan

Create a local JSON manifest. This deliberately incomplete skeleton supplies no
approved repetition, order or time/spending allowance and will fail validation:

    {
      "total_time_seconds": null,
      "repeats": null,
      "cases": [],
      "order": [],
      "models": {
        "main": "",
        "memory_extraction": "",
        "memory_dream": ""
      },
      "sources": {
        "baseline": {},
        "candidate": {}
      }
    }

Put each completed description/build record under its corresponding source.
Use the existing approved model names, including the separate memory models.
There is no model-selection or output-token override option.

Select a nonempty, nonrepeated subset of these fixed synthetic cases:

- policy: 一般退货需要满足哪些条件？
- mixed: 帮我选低糖饮品，顺便说明一般退货条件。
- chat: 你好。
- unmatched: 请查一下火星定制商品的退货条款。

Despite its case ID, unmatched is an unsupported/custom-terms probe, **not
deterministic empty-retrieval coverage**. Its word “退货” matches existing rules
in the approved retriever. Only actual observations can establish an empty
subsequent lookup.

Set a positive integer repeats, and explicitly choose either
["baseline", "candidate"] or ["candidate", "baseline"]. Order is repetition,
then the selected case-list order, then side order. The finite sample count is
cases × repeats × 2. No sample is silently retried or added.

Set a user-chosen positive finite total_time_seconds for the whole invocation.
**There is no default billing budget and no cost-only mode.** Unknown usage and
pricing cannot enforce a monetary ceiling. If authorization is only for a cost
ceiling, do not execute this runner.

Preview without loading configuration:

    python3 work/judge-prefetch-rebuild/live_compare.py --manifest /absolute/plan.json

Both sides must match static seed/policy facts, known numeric budget declarations
and dependency locks; prompt changes remain separately fingerprinted. These
checks are not a general proof of identical effective provider payloads.
Manually review unchanged temperature, retries, output limits and deadlines
against the frozen source/build evidence. An unsupported form is a blocker,
not permission to add a default or relax equality.

## Human-only execution and stopping

The human reviews the exact text, model/provider destinations, memory-worker
exposure, source/build evidence, repetition/order and total limit. No agent runs
the following with real credentials.

Only --execute calls each isolated application's normal get_settings() loader.
The existing configuration allowlist is OPENAI_API_KEY, OPENAI_BASE_URL,
LLM_MODEL, LLM_MODE, KEV_BASE_URL, MEMORY_EXTRACTION_MODEL, MEMORY_DREAM_MODEL and
BUSINESS_DATA_MODE. These retain case-insensitive alias handling, original
spelling and environment iteration order. The existing narrow process/network
and controlled-guard variables remain separate; arbitrary variables are not
forwarded. Other local app configuration comes from that checkout's normal
configuration file. Database/checkpoint values are always replaced with owned
temporary paths and verified before app initialization.

Both sources must have configured providers, match the declared models and
agree on provider/Kev endpoints before application samples. This does not verify
credential validity, account pricing or provider availability. There are no
extra model calls to fill missing measurements or probe those facts.

After review and authorization, the **human** invokes:

    python3 work/judge-prefetch-rebuild/live_compare.py --manifest /absolute/plan.json --execute --output /absolute/new-comparison.jsonl

Choose a new output path outside both source checkouts. It is reserved
exclusively with mode 0600; existing files/symlinks are never overwritten.
There is no resume/append option.

Every preflight/sample uses independent temporary database/checkpoint paths.
Every sample gets a fresh app-created owner/session. The normal FastAPI lifespan
runs through TestClient and the actual Pi subprocess, without binding an app
port. MemoryWorker can make additional configured memory-model calls; those
costs/exposure are part of this invocation, not excluded background work.

The total clock starts at CLI entry and covers source/Git checks, configuration,
seeding, startup and samples. Git/application waits observe the shared limit.
Ctrl-C/SIGTERM and deadlines are sticky: no remaining sample starts after the
stop has been observed. Only owned Git/app process groups are terminated,
including the reviewed Pi children that inherit their group. OS/file cleanup
is not a promise of a zero-overhead wall-clock return; already-sent remote work
may still complete and bill.

The flushed JSONL journal retains completed, failed, blocked, cancelled/deadline
and unstarted counts. A normal failure does not add a retry; later explicitly
planned samples can continue while the run remains valid. A role suggestion
is blocked: the runner does not accept it, navigate to Momo or confirm business
writes. Temporary databases are removed after owned processes stop.

Exit codes: 0 = all planned samples recorded completed; 1 = incomplete/failed;
2 = invalid/blocked; 124 = deadline; 130 = cancelled. None is a quality, browser
or business-acceptance sign-off.

## What the journal can establish

- Safe case/side/repetition, stage/status/error codes and source/build metadata
- Overall elapsed time from CLI entry
- Entry-route elapsed time, plus client-observed time from just before /routes
  to observed Guide termination, including the separate role route
- Public tool_rounds and available runtime_summary counts: policy lookups,
  outcomes, tool-origin reads/reuses, observed primary SDK tool starts/turns,
  safe policy-judgment outcome/elapsed time and truncation status

Absent old-side/hard-error summaries remain unknown, never inferred zero.
Tool starts/turns are not all provider HTTP calls. Raw event payloads and
diagnostic prose are omitted.

Total provider HTTP calls, tokens/usage, prices/cost, language quality and render
timings remain unknown. Client-observed time is not an exact server-admission
timestamp, first token/fact time or browser latency. Missing stage timings are
not reconstructed. No P50/P95 or savings claims are calculated.

Different-source runs are labelled bundled old/new; identical-source copies
are smoke only. Thinking transport and full payload alignment remain explicitly
not wire-verified by this CLI. No keys, headers, endpoint strings, raw provider
bodies or old user state are printed. Keep the approved manifest/build records
alongside the local journal; model declarations are fingerprinted rather than
echoed. Share only deliberately selected safe evidence.

## Remaining ticket 04 acceptance, not replaced by this CLI

Use the accepted frozen backend/runtime candidate and its existing controlled
evidence, retaining both independent Standards/Spec reviews. Record its exact
source tree, uncommitted-source status, locks/build and the user's separately
owned frontend commit. Do not rerun unaffected passing core gates merely to use
this CLI; product changes require affected revalidation. Preserve failed/blocked
samples: a terminal event alone is not a quality or safety pass.

The following matrix preserves the full same-version acceptance obligations;
it does not claim that already-covered controlled aspects are untested:

1. Pure policy, mixed shopping/policy, ordinary shopping/chat, role suggestion
   accept/reject, Momo direct input and explicit return buttons.
2. Judge uncertain/error/timeout; empty, partial and failed retrieval; same-scope
   reuse; new questions, changed conditions, insufficient evidence and safe
   follow-up; earlier valid and multiple references.
3. Two owners, replay/different-text conflicts, stale opening/request/source
   versions, forged or cross-owner references, cancellation/resumption, old
   navigation and already-confirmed business receipts.
4. Quantity/constraints/budget, explicit add-to-cart, separate simulated checkout,
   order aftersales proposal and explicit submission, human responsibility,
   history and memory, and result-first presentation. Simulated submission is not
   real fulfillment or refunded money.
5. Full original input and actual evidence/source reaching the same Pi; semantic
   quality, complete mixed-request coverage, concise Chinese and truthful
   unknown/partial results. Shopping writes need their own explicit user choice.
6. Browser suggestion/button flows, refresh, reopening, back/forward, double
   clicks, old SSE arrivals, stop/resume, and simultaneous shopping/policy/error
   presentation using the exact matched frontend/backend versions.
7. A separately authorized and sufficiently observable real-provider experiment
   for actual HTTP calls, retrieval/reuse/follow-up, main-model turns and usage.
   Keep independent entry timing and shared policy/Pi deadlines distinct. Count
   overhead from the extra judge and changed context. A small sample does not
   justify stable tail-latency or cost claims; speed cannot excuse quality loss.

Each layer remains separately marked controlled, real model, browser, or user
acceptance. No missing layer is inferred from another. The local memory/Dream
journey and its genuine 24-hour observation are separate work, not satisfied by
fresh temporary comparison sessions.

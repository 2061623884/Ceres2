# TASK03 implementation and integration contract

## Source and bounded adaptation

- Source transport verified through public GitHub at Ceres `ee7ce104885f731bc48bc8c6338c00d802ba0619`: [Kev provider](https://github.com/2061623884/Ceres/blob/ee7ce104885f731bc48bc8c6338c00d802ba0619/backend/app/llm/kev_provider.py).
- Visual references inspected at that exact commit: `frontend/src/App.tsx`, `frontend/src/lib/chatOpening.ts`, `frontend/src/index.css`. The glass panel/header/surface styles are selectively adapted in `frontend/src/role-chat.css`. Current C2 purchase/compare/order/human/stop/recovery UI remains, with one shared overlay and explicit role capsules/close control.
- No old runtime, opening dictionary, database, session, index or credential is imported. No live provider request was made.

## External protocol

One POST to configurable `KEV_BASE_URL` + `/v1/systemone`, three-second network timeout, model `kev-latest`, `questions.service` with `type: choice`, instructions and criteria. Response is parsed as `{model, answers: {service: {type, choice, probabilities}}}` using the original public wire pattern.

The single joint choice permits four Keke-owned labels (`keke_exploration`, `keke_purchase_modification`, `keke_factual_qa`, `keke_chat`), `momo`, unresolved service `clarify`, and explicit return-only navigation `return_keke`. Momo gets no Keke capability label. The joint criteria are new and require independent real-Kev validation; a passed MockTransport test does not establish external model quality or endpoint readiness. No fallback main-model router, parameter extraction, ordering or write permission is introduced.

## Public contracts and persistence

`/api/v1/navigation/sessions/{canonical_guide_session_id}` exposes:

- POST/GET `/opening`: open or restore the same persisted opening; role entry itself never resets quota.
- DELETE `/opening/{opening_id}`: explicit close invalidates pending handoff; subsequent open alone resets quota.
- POST `/routes`: `{request_id, opening_id, role, message, selected_object?, role_session_id?}`. Object contains only `kind: product|order` and `id`. Mercury session identity is owner-checked before reading relevant recent messages. The original text is retained unchanged.
- POST `/prompt-displayed`: `{opening_id, routing_request_id}`. Only this post-render ACK consumes automatic prompt quota.
- POST `/switches`: `{opening_id, target_role, accept, routing_request_id?}`. Acceptance/manual selection may return the still-current original request and optional object identifier, never a business action/permission bundle. Decline clears that pending request. A newer text, changed shopping anchor, close, or role change fences unadmitted old intent. A provider failure is persisted visibly; explicit manual role selection can resume its original request without fabricating a successful Kev outcome.

Opening metadata reuses `GuideSession.entry_context_json.role_navigation`; route/Query receipts reuse `GuideCommandReceipt`. No new state engine or second business authority. Guide task/state/session versions remain unchanged by navigation. Session-row serialization protects opening/decision receipt state across requests; body digests reject reused IDs with changed content.

Accepted handoff survives refresh until actual public admission. `authorize_text(db, owner_id, guide_session_id, role, body)` validates same request ID/original text/role and returns a stable capability scalar; unknown route references fail. `consume_handoff(...)` clears accepted metadata after admission. Guide ingress is owned/integrated by TASK01; tools, structured choices and SSE reconnect never call the judge. Full original text still reaches the role main model. Reserved navigation metadata is not prompt material.

Mercury query ingress uses the same gate and durable query receipt keyed by original request. Replays return prior terminal result rather than query again. A stale in-flight query receipt becomes an explicit interrupted failure after the existing lease window rather than restarting work. Original selected-order identifiers must match the current destination case; destination business services still recheck facts and responsibility. None of this changes proposal/confirmation authority or human responsibility protection.

## Controlled verification and limits

Tester owns every execution. The first recorded RED was missing public opening endpoint; later REDs caught actual stale accepted handoff execution after close/reopen and after newer text. Those defects received admission fences. The public API tests cover quota ACK, refresh, close, decline, manual resume, provider failure, once-only decision/replay, four Keke capabilities, explicit return, ownership and body mismatch, Mercury result replay and stale handoff fences.

`backend/tests/conftest.py` provides a documented HTTP MockTransport boundary for inherited business tests: current-role results only, not routing-quality acceptance. Dedicated navigation fixtures explicitly change the chooser. All route tests traverse the production external payload/parser contract, and dedicated wire tests validate one SystemOne question/call and malformed-response failure. No test-name conditional behavior or blanket network suppression is used.

`ui_navigation.mjs` executes the actual App in jsdom against controlled transport: visible prompt before ACK, decline, refresh quota, manual original-message resume once, explicit close reset, failure/manual entry. This is DOM-only, not a real browser. `legacy_navigation_transport.mjs` handles only the new navigation endpoints for inherited App harnesses; all old business assertions and unknown-request errors remain.

Real Kev output/latency, real main-model semantics, real browser interaction, visual review and user personal acceptance remain separate and unverified. Final combined regression must run after the TASK01 ingress hook and question UI are merged; passing isolated TASK03 does not substitute for that gate. See Tester records under `work/next-experience/10/` for exact source hashes and commands.

## Checkpoint evidence (Tester, 2026-10-06)

- `next03-green-04`: 16 public navigation/provider tests passed after the third RED safety fix.
- `checks/next03-dom-04`: actual App DOM journey passed, still DOM-only.
- `next03-mercury-regression-built`: 55 composed policy/Mercury/aftersales/human/memory/provider checks passed after rebuilding the composed Pi runtime. Earlier stale-dist failures are not presented as source regressions or hidden.
- `checks/next03-legacy-dom-02`: eight representative inherited UI scenarios passed, including guide/purchase remount, supply, history, comparison, snapshot ordering and plan controls. The fixture now explicitly asserts refresh restores the chat shell instead of assuming home.
- Frontend build and strict typecheck passed in prior captured `checks/next03-frontend-02`; composed ingress/question updates still require fresh final checks.

### Admission and ACK follow-up

Public RED tests exposed and now fence: newer intent and selected order A→B racing between authorization and reservation; a changed shopping anchor after accepting a switch; manual retry of an accepted but unadmitted request; and display ACK arriving after decline. Admission holds the existing session lock through guide run receipt creation. Mercury revalidates the durable decision and exact order after its separate reservation and releases the reservation on rejection. A valid displayed-offer receipt can consume quota even after decline, but an old opening cannot consume a new opening's quota. A still-current accepted request can be manually retried without rejudgment; an already-admitted receipt is replayed.

Tester `next03-frozen-regression`: 83 composed public navigation/provider, guide-gate/snack/policy, Mercury/aftersales/human/memory checks passed against the frozen `b147b90` plus these fixes. Full source hashes and commands are in that evidence record. UI manual-retry behavior is being checked separately; this backend checkpoint does not claim that final UI check or real-provider/browser acceptance.

### UI retry checkpoint

The actual App DOM RED confirmed that the component's remembered handoff ID suppressed an explicit same-role retry after failed business admission. Both role components now clear that duplicate-effect marker only when the parent clears the handoff, retaining protection while a handoff is active. The next explicit manual action can retry the same request ID, relying on server idempotency. Tester `checks/next03-dom-retry-green` and `next03-frontend-final` passed the DOM retry, frontend build and strict typecheck. This checkpoint is separate from subsequent compound explicit-return work.

## Joint criteria revision and TASK05/TASK09 consumer contract

`CRITERIA_VERSION = ceres2-role-capability-v2-explicit-return` extends the same one-question SystemOne choice, not another provider call. Plain `return_keke` is explicitly page-only. `return_keke_exploration`, `return_keke_purchase_modification`, `return_keke_factual_qa`, and `return_keke_chat` combine the user's already-explicit current page choice with one of the same four Coco capability labels. A new shopping goal without explicit page choice still requires the user's switch choice. Conditional future navigation/quoted return words are not current navigation authorization.

For compound explicit return, the public decision has `status: navigation`, `target_role/authorized_role: keke`, the normal capability scalar, and `continue_original: true`. It directly updates role and persists the minimal original request for destination admission. The App forwards the entire unchanged message with the same request ID, not only the shopping clause. This preserves budgets, policy questions and other goals for the actual Pi model, while navigation remains separate from any cart/order/application consent. Pure return has `continue_original: false` and does not invoke a business model. Both preserve the opening's existing automatic-prompt quota.

TASK05 must continue consuming only the four-value Coco capability scalar and all original text; return variants are joint routing choices, not extra business capabilities. TASK09 must reuse this same request identity/minimal handoff and let the destination requery facts. It must not rejudge, manufacture a second agent conversation, replay completed aftersales steps, or interpret navigation as purchase/aftersales permission.

The parser intentionally rejects unknown labels and old service-only three-choice responses as visible provider unavailability. There is no mapping that guesses a Coco capability from an old `stay_current` result. Real endpoint/model accuracy for this new finite criteria set remains unverified regardless of controlled transport/API/DOM results.

### Final composed candidate verification

Tester `next03-release-public`: 52 public cases passed after syncing the released snack fixture/constraint candidate. `checks/next03-release-runtime` passed runtime typecheck/build. `checks/next03-release-ui` passed frontend build/strict typecheck and 10 controlled DOM journeys: compound navigation/manual retry, snack selection, policy in both actual App roles, and inherited guide/purchase/supply/comparison/history/snapshot/plan controls. The frozen source before this final commit is recorded as `b1f2cf6` plus the exact compound-return WIP; the final commit changes no tested product source beyond that captured candidate. Earlier counts above remain scoped to their own candidates.

Root-requested full inherited-suite verification, independent Standards/Spec review, real Kev/main-model accuracy and latency, real browser/visual checks, and personal acceptance are separate gates; none is implied by these focused controlled passes. The direct public guide gate is included in this candidate, so the former UI-only routing gap is closed.

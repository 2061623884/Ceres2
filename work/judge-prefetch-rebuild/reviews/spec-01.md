# Spec review: ticket 01 + bounded thinking transport (interim)

Read-only review on 2026-10-07. Base: `4bed9c891261e382122d424825b649989ea92c92`. Actual HEAD: `a676f3ecf6ed4bd13052852cc7a78e41bc070afe`.

Comparison: `git diff 4bed9c891261e382122d424825b649989ea92c92` (includes tracked working-tree changes). SHA-256: `5437bf0280969694abfbf368a2c614dc9802be4f4d1b386c9129de04e86d5167`. Same at review start/end. Also read untracked schema and both new role/legacy fixture modules; hashes below.

## Finding

**P2 — The role-boundary response cannot coexist with another requested result.**

Spec line 43 requires: “具体售后由可可说明职责并提供显式入口”; line 48 retains “所有子问题和条件.” Ticket 01 requires passing the complete original to Pi when entry judgment is no/uncertain/timeout/error.

`backend/app/services/pi_product_runtime.py:345–350` only permits `role_boundary` following `guide_request question`, and returns no shopping/policy evidence. Shopping answers support only the independent policy attachment at lines 330–335. `backend/app/services/pi_product_turn_service.py:255–263` creates the explicit navigation action only for the exclusive `role_boundary` answer kind. The new prompt (`backend/app/prompts/experience.json:13`) covers “仅此类请求,” leaving the mixed fallback unsupported.

Example: entry fails for “继续选两箱饮品，也查这笔订单退款资格.” A correct shopping `continue` result cannot include the authoritative after-sales boundary/action; returning `role_boundary` instead throws `PI_ROUTE_INVALID`. Using `question` and returning only the boundary drops the shopping clause. Make the host boundary/action composable with the otherwise valid result and cover a mixed fallback through public HTTP/SSE, retaining zero after-sales writes.

## Scope and evidence limits

No additional source-level Spec findings in reviewed role-only routing, explicit button navigation, first-context migration, legacy receipt guards, or seven DeepSeek transport paths. Model identities and existing limits remain unchanged. No test/build/install/API command was executed by this reviewer. Tester results require their own frozen evidence. Tickets 02/03 remain expected future work; frontend/DOM/browser and real-provider gates remain not run here. This is not whole-branch/four-ticket acceptance.

## Untracked source SHA-256

- `backend/app/schemas/navigation.py`: `4722016d24edc408f5d915f7bd4a1ee38519a408ef98295146cb77a4b99b8a5c`
- `backend/tests/test_judge_legacy_navigation_public.py`: `1e5b3d42ad6cf3705f95282b1330ba264d18ef3efee9cb0e147f11ba976447a9`
- `backend/tests/test_judge_role_entry_public.py`: `f9b13a2f495ab4491b6187f80385784fbe42573743a2ed11dadd59615628aa6b`

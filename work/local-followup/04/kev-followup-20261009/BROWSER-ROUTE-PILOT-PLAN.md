# Firefox Kev route and accepted handoff pilot

Status: predeclared before the browser run; one browser journey only. This is a public UI integration observation, not another classifier-quality sample or part of the formal 100-run baseline.

## Frozen input and version

- Worktree HEAD: `9e9be1da8ef7dd7ba630a2025e63835612e4795e`; tree `e28d6b06da5a174a6d739907dc4c5dfacaf7f6d8`.
- Current public navigation input is a new synthetic one-off: `我已签收订单 ORD-DEMO-102，里面有一盒鸡蛋破损，想申请售后退货退款。请帮我转交售后处理。`
- The order id is only text. No real order is selected or looked up. `selected_object` is expected to remain null.
- Input SHA-256: `afefc919769712a15f1ad2a1ce52b2ae59eaf91da9b9c69c385f6331a05a55b4`; the input is not copied into any private batch or acceptance set.

## Bounded browser actions

1. Start a new Firefox WebDriver session with an isolated temporary profile and exact-authority loopback proxy. Load the current built `frontend/dist` through HTTPS `localhost`, proxying only to the running isolated Ceres API at `127.0.0.1:8017`. The API uses the existing Kev service at `127.0.0.1:8009`.
2. Use visible controls to open Keke, enter the exact input once, and submit once. Allow the normal single `/routes` judgment with the existing 3-second Kev timeout. Do not retry, resubmit or change the input.
3. If the page displays a switch suggestion, capture it and click `切换并继续原请求` exactly once. This is user acceptance of the role handoff, not a business confirmation. Do not click order, refund, after-sales or cart actions.
4. The product may automatically send the accepted original message to Momo. If so, observe at most that single handoff turn through the public UI and retain its real outcome; do not send another Momo message. Record any provider/selection wait, timeout or failure without retry.
5. If the Kev decision does not present a prompt, record the visible state and stop without forcing a switch.

## Evidence and limits

- Record HTTP route/switch status, visible prompt and accepted role, the original-message hash, final visible Momo state, runtime/SSE result, bounded elapsed time, and the actual API paths. Do not save cookies, credentials, raw provider payloads or identity/session ids in the curated report.
- Sample only numeric Kev model-card fields immediately before and after the browser window. These counters are global successful-batch counters, not per-owner audit records; unrelated concurrent service traffic cannot be excluded.
- No expectation of semantic success is inferred from HTTP 200, a role switch, or the page's visible answer. This one browser path does not change the prior six-case API matrix or count as independent classifier quality evidence.
- Keep the already-running API and Kev services unchanged. Leave the isolated database/checkpoint for the follow-on baseline tester; do not stage or commit generated runtime state.

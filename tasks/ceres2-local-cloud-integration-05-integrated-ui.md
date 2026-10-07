# T05：本地界面适配新入口与协议

- 状态：待验收（技术实现与受控门槛完成；实际浏览器/真实provider/用户本人验收未完成）
- 负责人：frontend owner；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T02 Canonical 商品召回与当前 Offer](ceres2-local-cloud-integration-02-canonical-shopping.md)；[T04 可选审校过程消息与 SSE](ceres2-local-cloud-integration-04-reviewed-interim-sse.md)；[T07 售后数量照片与工单证据范围](ceres2-local-cloud-integration-07-aftersales-ticket-evidence.md)

## 最终当前结论（2026-10-07）

本票技术实现已进入最终产品 `f963017587b3eab30965ffcd3aab90fcc3852f3e`，受控验证/两轴修复闭环见[最终报告](../work/local-cloud-integration/t09/FINAL-VERIFICATION.md)。全量746通过/5跳过属于`81b02f9`；同版知识环境补齐跳过项，最终狭窄修复183例及合入4例另行绑定，不声称最终pin重新全量。实际浏览器BLOCKED、真实provider/用户本人验收NOT RUN，不能把技术完成等同于整体验收。

以下阶段记录按各自固定pin保留，旧“待实现/待交接”等描述属于历史过程，不推翻本节当前结论。

## What to build / 合同

保留 incoming 视觉页面和购物售后入口；ready/switch、capability=null、entry_judgment；yes 确认/拒绝、Momo 文字零 Kev、纯按钮 handoff=null；混合 messages/navigation_action 和 interim 全量显示；不得恢复旧 unavailable 手动续接授权。

## 验收

- [x] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] Typed DOM/浏览器：yes 接受/拒绝、no/uncertain/error 可可继续、Momo 返回按钮零重放、混合消息、停止/恢复、重复点击、同订单/异单、关闭重开和前后导航。
- [x] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [x] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [x] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

T02/T04/T07已技术放行，frontend owner从最新canonical接管全frontend目录；不得改runtime/共享backend文件。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

恢复检查：T05 WIP `a9c9c51151ffb67934c9d922c949a0bfa379c94e` 已将14份frontend源文件和3份独立UI harness提交，工作树干净；独立备份payload已准备，未合canonical，未验收。已恢复的5项受控检查不能替代完整DOM/实际Chromium/后端fixture旅程及两轴。远端备份是否成功以主会话回执为准。

独立WIP备份已核实：remote `58db7fef475bab34e4c5b53bc3a1e4ba6408dfbb` ↔ local `a9c9c5` / tree `34da6207b0d26c566d99b9750cf13b71bde7a0bb`；回执已保存。此为独立备份分支，不是canonical合入或验收。


## 当前技术合入与未验边界

最终 `4278eea`（production与已审`656cfef`相同）在两轴测试-only绑定清除后，经主会话明确批准无冲突合入 `a871400`；frontend及05 harness与交付pin零差异。受控DOM、strictTS/build及fresh安全fixture21个实际HTTP请求通过，迟到订单response P2有独立RED/GREEN。不同pin/范围分列，不声称一次全量。

实际Chromium/CUA浏览器仍BLOCKED：IPC EPERM及跨执行环境host拒连，未进入产品UI。该阻塞是明确保留的未验门槛，DOM/HTTP不是替代；技术合入不代表浏览器或用户接受。最终T09同版验证与整体现有前端回归仍需执行。[证据摘要](../work/local-cloud-integration/t05/verification-summary.json)、[源码](../work/local-cloud-integration/t05/source-equivalence.json)、[浏览器边界](../work/local-cloud-integration/t05/browser-gate.json)。

- [ ] 剩余实际浏览器、获准的真实provider与用户本人验收按最终报告独立完成；不由受控结果自动勾选。

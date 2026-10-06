# Ceres2 Runtime 13：同用户订单与售后贯通

状态：**待验收**。
负责人：**TASK13 唯一实现负责人（order_case_link）**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过（2026-10-05 16:37 UTC 主会话接受范围内技术结果）**。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户在服务器模拟订单上点击墨墨，真实 LangGraph 查询同一订单权威，刷新/重启继续该 case。角色相关记忆由 P09 独立交付，不阻塞本票及 P14 的订单/退款旅程。

## 阻塞关系

[02 LangGraph 售后查询首切片](ceres2-runtime-upgrade-02-langgraph-aftersales-query.md)；[12 持久模拟结算订单](ceres2-runtime-upgrade-12-persistent-simulated-orders.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [x] 将 P02 的订单服务接缝接入单一权威，保留独立角色入口；不双写演示库、不自动跳转/消息搬运或跨 Agent 委派。
- [x] 所需 owner/order/case 映射、迁移、状态 fixture 与选单 UI 贯通；未知旧 owner/time 不擅自导入。
- [x] 验证结算→准确选单→查询/资格/进度→恢复、空订单、跨 owner/thread 边界及查询无需确认；P16 再验证与 P09 的记忆共享并行集成结果。

- [x] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [x] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [x] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开结算订单入口/墨墨 HTTP/SSE → canonical 订单服务 → case 查询/恢复；不以线程 ID 代替 owner 授权。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

TASK14 沿用 [交接](../work/clean-rebuild/13/handoff.md) 中 canonical owner/order/case 和 generation 契约。TASK16 继续真实 qwen、真实浏览器完整旅程与用户本人验收；本票不把受控 HTTP/DOM 当作这些结果。TASK15 新发现的工单身份回复问题仅阻塞 TASK15，未撤销本票已验证只读订单/case 集成范围。

## 证据

2026-10-05 16:18 UTC：已读取 TASK02/12 新工程技术交接。沿用同库 SimulatedOrder/MercuryCase，无新增 schema 或迁移；新增 checkout→Mercury 公共行为测试，修复准确订单联系入口，不自动发送查询。实际浏览器、真实模型和用户本人验收仍保留。

历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-13-canonical-order-aftersales.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

## 当前新证据（2026-10-05 16:27 UTC）

- [设计边界](../work/clean-rebuild/13/design.md)；[审查源码快照](../work/clean-rebuild/13/review-source-manifest.json)。
- [公共 HTTP 红/绿、DOM 与竞态证据](../work/ceres2-runtime-upgrade/13/test-runs/)：初次 backend-regression-01 为 24/24；新增 identity race 已红→绿；exact-contact StrictMode DOM 和旧迟到回复竞态已绿。
- 新增 same-contact race 确实红：旧 A 选单未完成时再次联系当前 B，跳过 B 的 CAS 会导致 UI/权威不同。已修复为每次显式联系均执行选单 CAS；Tester fresh green-fence-* 复验通过，identity race、typecheck、build 均通过。最终双独立验证仍待审查后冻结。
- 与 TASK15 协作：通过既有同库 guarded publish 后、commit 前调用 record_query_outcome；挂载独立 HumanCasePanel。未引入自由写工具或第二 case 权威。
- 未新增 schema：沿用 P02/P12 同库权威及增量迁移，未知历史门店保留 null，不导入旧 owner/time 或活动数据库。

2026-10-05 16:30 UTC Spec-review P2：完整卸载／重挂会重复消费父级旧联系订单；新 DOM red-remount-contact 已复现 B 覆盖手选 A。改为父级持有原子 contact intent，成功消费后按 sequence 清除；不清空 canonical selection。最终复验和审查重查进行中，不作为技术已验收。

2026-10-05 16:32 UTC：Spec P2 的组件完整卸载／重挂 DOM 已 green-remount-contact；App 原子 intent/稳定 ack 接线已由唯一 App owner 落地并核对，parent-wiring-typecheck/build 通过。此证据为受控组件 DOM 与构建，不声称真实浏览器或完整 App 浏览器 E2E。等待 Spec 重查及 P15 修复冻结后的最终公共行为两次独立验证。

2026-10-05 16:37 UTC：专职 Tester 最终受控 DOM/identity 独立两次通过，旧迟到响应回归与 integrated typecheck/build 通过；公共后端联合 P02/P12/P13/P15 两次均 35/35，相同范围指纹见 [final-shared-source-comparison](../work/ceres2-runtime-upgrade/13/test-runs/final-shared-source-comparison.json)。Spec P2 修复重查／主会话技术释放仍待确认；P15 独立 ticket identity 修复如改变共享输入，以最新重新冻结验证为准。

## 技术释放结论

2026-10-05 16:37 UTC 主会话接受范围内技术结果：Standards 已关闭；Spec consumed-intent 修复于 16:33 重查无问题。35/35 两次公共后端验证具有相同范围指纹，fresh DOM/contact/identity 双次与 typecheck/build 均通过。正式状态仍为待验收，真实模型、真实浏览器与用户本人验收未完成。[释放源码清单](../work/clean-rebuild/13/release-source-manifest.json) 区分 owned source、已验证共享快照与后来独立变化的 consumed reference；不把 TASK15 新回复问题误作为本票技术门禁。

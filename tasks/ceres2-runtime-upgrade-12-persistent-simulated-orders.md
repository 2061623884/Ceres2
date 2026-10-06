# Ceres2 Runtime 12：持久模拟结算订单

状态：**待验收**。
负责人：**TASK12 实现负责人（implement_clean_simulated_orders）；测试由独立 Tester 执行**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过（新工程限定范围：受控事务/API/迁移/DOM，两次独立验证及 Standards/Spec 两轴复审已闭合；真实浏览器与用户本人验收保留至 TASK16）**。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户从已有购物车独立模拟结算，刷新/重启可见同一订单；订单与本次购物车扣减、回执原子一致。

## 阻塞关系

无技术前置。产品排期在 01、02 两个 runtime 首切片之后，不把排期写成技术阻塞。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [ ] 可直接以现有货架明确加购或隔离购物车 fixture 演示，不依赖新 Pi 采购闭环。独立结算摘要/确认、不可变商品价格数量快照、订单列表/详情与“联系墨墨”控件同票。
- [ ] canonical order/receipt schema、最小状态/退货属性 seed、合成旧库迁移保全与 UI 测试随票；旧浏览器订单不默认为权威订单。
- [ ] 验证价格/车变化刷新摘要、原子失败、并发新增不被误清、key 重放及 owner 隔离；P13 再贯通实际墨墨入口。

- [ ] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [ ] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [ ] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开结算/订单/购物车 API 与订单页面；补充结算业务提交 unit-of-work（订单、扣车、receipt）故障与竞争注入。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

最小货架购物车、摘要、显式确认、原子订单/扣车/回执与只暂停购物写入的回退门控已实现。专职 Tester 已完成修复后两次独立公共行为验证与 DOM 组件验证，两轴复审已闭合，主会话于 2026-10-05 16:14 UTC 接受限定技术放行。TASK13 可消费下述唯一 canonical order 契约。真实浏览器页面旅程及用户本人验收保留至 TASK16，尚未完成。

## 证据

新工程实现与选择性来源说明：[TASK12 实现记录](../work/ceres2-runtime-upgrade/12/implementation.md)。公共红测：`work/ceres2-runtime-upgrade/12/test-runs/red-checkout`；购物写入暂停 HTTP 红测：`work/ceres2-runtime-upgrade/12/test-runs/red-shopping-hold`。首次候选结果包含 10 项通过、暂停开关未实现红测；不得视为最终全绿。修复后最终证据：`final-checkout-01/02`（各 12 项）、`dom-orders-03/04`（DOM-only）、`final-frontend-typecheck` 与 `final-frontend-build`，均位于同一 `test-runs/`。历史非空快照投影缺项经 `red-old-order-projection` 红测再修复，原始 snapshot 字节保持不变。历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-12-persistent-simulated-orders.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

限定技术放行交接：[TASK13 canonical 订单契约](../work/ceres2-runtime-upgrade/12/task13-handoff.md)；[自身源码/测试与共享消费引用清单](../work/ceres2-runtime-upgrade/12/release-source-manifest.json)。历史通过没有继承，无真实支付；本次无提交。

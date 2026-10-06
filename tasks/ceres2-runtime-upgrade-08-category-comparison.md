# Ceres2 Runtime 08：品类筛选与真实比较

状态：**待验收**。
负责人：**TASK08 实现线程**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过（2026-10-05 18:33 UTC root 放行受控技术范围：修复后 19 项公共行为/迁移 × 2、DOM、typecheck/build、两轴审查关闭）**。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户浏览或聊天选购可乐等品类，Pi 自主筛选/补查后展示品牌、容量、包装、件数、总价及可比单位价，用户选定后走同一清单与确认入口。

## 阻塞关系

[04 明确选购与双入口确认](ceres2-runtime-upgrade-04-explicit-cart-confirmation.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [x] 比较 response/type、页面上下文与展示引用贯通，真实属性缺失明确未知；有限候选，不新建独立比较管理页。
- [x] 商品属性/多包装 fixture、所需投影或字段迁移、聊天/卡片 UI 与测试同票交付。
- [x] 验证比较前不产生清单/车、空结果不复用旧 ref、真实候选选定、上下文条件保留及无关建议不能自动纳入。

- [x] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [x] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [x] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开商品/导购 HTTP/SSE、比较卡片与选定确认；不依赖内部搜索分支或图拓扑断言。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

受控技术范围已放行，当前总状态仍为待验收。继续 TASK16 综合验证；实际 qwen3.8-27b 采样需安全 provider 配置，真实浏览器环境仍阻塞，用户本人验收未完成。后续 TASK06 共享源码变化属于 successor，须按各自范围复验，不把本次指纹视为整个工作树的永久通过。无新增代码或本地提交。

## 证据

2026-10-05 17:59 UTC：专职 Tester 在真实 Pi SDK＋隔离 HTTP provider fixture 下验证首个 RED：compare_products 尚不存在，公开 SSE 终止为 error；预期应返回事实比较卡片。证据：[red-category-comparison](../work/ceres2-runtime-upgrade/08/test-runs/red-category-comparison/evidence.json)。

实现边界与集成契约：[INTEGRATION](../work/clean-rebuild/08-comparison/INTEGRATION.md)。模型/服务/卡片由 TASK08 维护；guide/runtime/worker/App/saleGuide 由 TASK05 唯一接入；登记和增量迁移由 foundation 维护。真实 qwen3.8-27b、浏览器和用户本人验收未完成。

历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-08-category-comparison.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。


2026-10-05 18:23 UTC 初始冻结基线：[final-comparison01](../work/ceres2-runtime-upgrade/08/test-runs/final-comparison-01/evidence.json)、[final-comparison02](../work/ceres2-runtime-upgrade/08/test-runs/final-comparison-02/evidence.json)，16/16 × 2；实际保留 App 的 DOM 覆盖真实/未知属性、多包装每升价格、选定独立于确认、展示引用、空/失败清理以及已知盒装标签。该基线早于最新 Spec 缺陷，不作为当前最终放行。

关键新增 RED：首工具缺失、跨轮候选 schema、保存筛选条件、比较后未选定却自动出清单、provider 401 旧引用残留、绕过筛选引用、异品类重入、盒装未知误标；每项均有专职 Tester 留证。并发重复提案与新候选替换、owner/task/state/page/displayed 引用隔离、5 候选上限、排除/非体积单位和重复迁移为新增行为回归。

最终交接：[HANDOFF](../work/clean-rebuild/08-comparison/HANDOFF.md)。后续证据需以修复后的源码指纹为准，不继承初始冻结状态。

2026-10-05 18:33 UTC 最终受控技术放行：[修复后行为 01](../work/ceres2-runtime-upgrade/08/test-runs/review-final-comparison-01/evidence.json)、[修复后行为 02](../work/ceres2-runtime-upgrade/08/test-runs/review-final-comparison-02/evidence.json)，19/19 × 2（39.18s / 39.75s）；[四次采集适用源码](../work/ceres2-runtime-upgrade/08/test-runs/review-final-source-comparison.json) 指纹 `2727e3038914adfb340c83dd36924949cbf1e05d1a355b0b1f42ef7e2a54606a`，包含 comparison/shared Pi/App/PurchaseService。仅无关 dish_service 在第二轮变化，不属于本票直接比较执行路径；后续 TASK06 改动另作 successor。

Spec 新增 RED 3 个实际 App DOM（晚到 error / success、reconnect）和 2 个实际 Pi protected close（tool_budget / deadline）均 GREEN，另有 protected close 与新展示并发保护回归；[typecheck](../work/ceres2-runtime-upgrade/08/test-runs/review-final-typecheck/evidence.json)、[build](../work/ceres2-runtime-upgrade/08/test-runs/review-final-build/evidence.json) 通过。独立 [两轴审查归因摘要](../work/clean-rebuild/08-comparison/REVIEW.md) 均关闭；[放行记录](../work/clean-rebuild/08-comparison/RELEASE.json)。这些结果是受控技术/DOM 证据，不代表真实 provider、真实浏览器或用户验收。

18:34 UTC 追加同一修复后实际 App 的受影响 DOM 回归全部 GREEN：`review-affected-ui-comparison`（常规比较/已知盒装/当前引用）、`purchase`（按钮/文字确认）、`display`（新清单可见后才更新确认引用）、`recovery`（成功回执丢失后恢复购物车）。测试路径均位于本票 test-runs，放行记录已列出；没有新增 UI 源码变更。

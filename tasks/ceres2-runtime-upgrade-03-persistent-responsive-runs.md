# Ceres2 Runtime 03：长期任务与可响应运行

状态：**待验收**。
负责人：**implement_clean_responsive_runs**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过**（受控技术范围；2026-10-05 17:11 UTC 主会话确认，两次同版 45／45、DOM／typecheck／build、Standards／Spec 两轴均关闭）。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

同一用户回到长期可可入口，一个购买任务跨多次运行；处理时可问事实问题、询问进度或修改条件；停止当前处理与放弃分开，关页后有界继续，返回可见持久结果。

## 阻塞关系

[01 Pi 商品查询首切片](ceres2-runtime-upgrade-01-pi-product-query.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

以下勾选仅表示已通过的受控技术范围；真实 qwen3.8-27b、真实页面及用户本人验收仍待 16，不据此勾选为整体产品已验收。

- [x] 以查询旅程即可演示，无须先完成加购。唯一长期入口/活动任务、运行状态/消息序号、结果与原版本持久化，必要增量迁移与旧会话 fixture 随票落地。
- [x] 无关事实问答/进度不切任务；新购物目标才换任务；修改及时回应、有用查询继续但结果受新条件校验。停止/换任务 fence 保留，任务结束不清车。
- [x] 完成灰色单动作行滚动替换、三点→流式短消息、自然简洁与适度 emoji；不设未确认的消息条数硬上限。
- [x] 验证多请求响应、旧结果失效、停止与结果竞争、断开 SSE/重连、重启恢复已落库结果、保护终止不自动续跑及迁移保全。

- [x] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [x] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [x] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开 bootstrap/对话/运行 HTTP/SSE、消息分页与任务状态；重新连接/重启后读取持久结果。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

2026-10-05 17:04 UTC 已冻结最终修复，专职 Tester 已完成同版 P01＋P03 两次 45／45（原 21 回归＋新增 24）、最终 DOM／typecheck／build。主会话已于 17:11 UTC 确认 Standards／Spec 两轴复审关闭，放行受控技术范围。普通解释采用实际 SDK 同模型语义核对与宿主引用契约，模型剩余风险单列；真实 qwen3.8-27b、真实页面和本人验收仍归 16。

## 证据

新工程当前开始独立红／绿验证；初始源码 hash 见 `work/clean-rebuild/03/INITIAL-SOURCE.sha256`。01 已于 16:10 UTC 受控技术放行，见 `work/clean-rebuild/01/HANDOFF-P03.md`；不继承为 03 通过。历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-03-persistent-responsive-runs.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

实现、选择性迁移与语义风险说明：[本票执行说明](../work/clean-rebuild/03/README.md)。测试及原始输出由专职 Tester 留存；最终冻结清单与通过数字待复验完成后写入，正式状态仍为待验收。

最终测试证据：[同版源码对比](../work/ceres2-runtime-upgrade/03/test-runs/final-guide-source-comparison.json)、[第一次 45／45](../work/ceres2-runtime-upgrade/03/test-runs/final-guide-05/evidence.json)、[第二次 45／45](../work/ceres2-runtime-upgrade/03/test-runs/final-guide-06/evidence.json)。冻结范围：[发布候选清单](../work/clean-rebuild/03/RELEASE.json)。

接续：由主会话将导购 API／models／Pi runtime／App 的唯一维护权转给 TASK04；TASK09 对导购钩子的修改须经该维护者协调。TASK14 在本票双跑之后新增的共享迁移需由下一轮受影响集成验证覆盖，不重写本票已验证快照。

# Ceres2 Runtime 07：供给适配与部分采购

状态：**待验收**。
负责人：**TASK07 唯一实现负责人 implement_clean_supply_selection**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过**（受控技术范围；2026-10-05 19:42 UTC 主会话释放。150/150 两次，四份源码快照与当前 309 文件一致）。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

单菜或多菜采购遇到规格缺货、库存不足或整种食材无货时，用户看到合法替代与缺项，明确选择部分采购后再独立确认。

## 阻塞关系

[06 多菜合并与来源展示](ceres2-runtime-upgrade-06-multi-dish-demand.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [x] 延续整项需求的整包总价与余量、兼容同食材多规格，保留用户已选规格；不能静默改变目标、条件或把缺货当工具故障。
- [x] 缺货/不足/多规格/整种无货 seed、必需字段迁移、供给预览/缺项 UI 与测试随票。
- [x] 验证完整方案与供给预览/部分清单的差别、两个独立用户决定、购物车防重复、金额/库存变化重确认。

- [x] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [x] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [x] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开导购/供给预览/部分采购/确认接口及缺项页面；观察方案与购物车事实。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

实现、公共行为红绿、独立两轴复核及两项有效 Spec 修复均完成。最终受控行为 150/150 两次，匹配源码下供给/替代 DOM 双跑、受影响 UI、typecheck/build 均通过。主会话已释放，guide/runtime/App/purchase 共享实现所有权交 TASK11；真实 qwen3.8-27b 凭据、真实页面、用户本人验收分别待完成，不能由受控结果替代。

## 证据

实现交接：[HANDOFF](../work/clean-rebuild/07/HANDOFF.md)。当前证据入口：[进展](../work/clean-rebuild/07/progress.md)、`work/ceres2-runtime-upgrade/07/test-runs/`。已由 Tester 记录所选规格缺货预览与显式部分采购两个公共行为 RED→GREEN；后续范围和独立验收尚在进行。历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-07-supply-partial-purchase.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。


2026-10-05 19:42 UTC 最终证据：`work/ceres2-runtime-upgrade/07/test-runs/final-supply-01/`、`final-supply-02/`、`final-supply-source-comparison.json`。两次各 150 passed，耗时 209.28s / 209.61s，exit 0。四份 309 文件源码映射一致，当前零差异；fingerprint `d7e6cd68b2817c910da7f2756a0fc740cb52b7ec7e7dfc6b27b4695abc20e5f9`。历史通过未继承；该结论仅覆盖受控技术范围。

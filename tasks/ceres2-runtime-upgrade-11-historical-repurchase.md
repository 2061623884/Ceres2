# Ceres2 Runtime 11：历史提醒与重新采购

状态：**待验收**。
负责人：**TASK11 唯一实现负责人（主会话协调）**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过**（受控模型／实际 Pi SDK／公开 HTTP 业务与保留 App DOM 范围；主会话 2026-10-05 20:26 UTC 释放）。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

开始新任务时可简短提示一次相关未完成清单；用户选定历史方案后按当前条件和供给生成新清单、展示变化，并重新确认加购。

## 阻塞关系

[07 供给适配与部分采购](ceres2-runtime-upgrade-07-supply-partial-purchase.md)；[09 聊天显式记忆与共享边界](ceres2-runtime-upgrade-09-explicit-role-memory.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

以下勾选仅代表上述受控技术范围；真实模型、真实浏览器和用户本人验收仍分别未完成。

- [x] 提醒先核对购物车，忽略/拒绝即停止，绝不自动恢复；复购沿用来源/目标但不沿用旧金额、库存、ledger 或批准。
- [x] 当前人数/预算/排除/有效记忆、多菜数量及缺货路径完整贯通；历史来源与提醒状态最小迁移、两 owner 新旧供给 fixture、UI 与测试同票交付。
- [x] 验证含糊“上次”先选来源、旧快照不变、当前差异与部分采购、重新确认、防重复及提醒去重。

- [x] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [x] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [x] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开历史来源/导购/方案/确认接口及用户页面，观察提醒去重、当前清单与真实购物车。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

主会话已释放本票受控技术范围并将共享 guide/runtime/worker/App/saleGuide/purchase 唯一实现责任转交 TASK16 新负责人。本票不再修改应用或测试，不提交或推送。TASK16 做整体接入／最终验证；真实 qwen3.8-27b、真实浏览器与用户本人验收单列待完成。

## 证据

最终两次独立行为验证：182/182、182/182，退出码均为 0；四份快照及当前 314 个文件一致，指纹 `0f1be6b11ad91dc1cdd881aace1154101fbe6ed29a2787d0357e4ea202e57d53`。同版本历史 DOM 两次、八项受影响 UI、typecheck/build 均通过；Standards/Spec 两轴及窄修复复审已关闭。[来源一致性核对](../work/ceres2-runtime-upgrade/11/test-runs/final-history-source-comparison.json)、[释放记录](../work/clean-rebuild/11/RELEASE.json)、[TASK16 交接](../work/clean-rebuild/11/HANDOFF-P16.md)。

当前实现及分层证据入口：[TASK11 handoff](../work/clean-rebuild/11/HANDOFF.md)、[进展](../work/clean-rebuild/11/progress.md)、[专职 Tester 原始证据](../work/ceres2-runtime-upgrade/11/test-runs/)。真实 qwen3.8-27b provider 配置、真实浏览器与用户本人验收仍未完成。历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-11-historical-repurchase.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

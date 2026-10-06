# Ceres2 Runtime 02：LangGraph 售后查询首切片

状态：**待验收**。
负责人：**implement_clean_mercury_query**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过**。范围限定于 TASK02 受控技术验证：主会话已确认两轴修复复核关闭，离线同版 14／14 两轮、实际 SDK 受控 HTTP 与新 DOM 通过；真实模型、浏览器和本人验收仍待 TASK16。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户从隔离演示订单选择一单进入墨墨，真实 Python LangGraph 查询订单、物流、资格或政策，澄清后继续；刷新/重启仍能回到同一 case 的可靠查询结果。

## 阻塞关系

无技术前置。

已获代码、必要依赖与专职测试执行授权；当前不提交、不推送，由主会话审查后另行处理。

## 验收条件

- [ ] 以 owner-scoped 合成订单服务适配器工作，不等真实新结算订单；适配器接口与后续单一订单权威一致，不给线上 owner 回退 demo 数据。
- [ ] 持久 case/checkpoint、选单版本及必要消息，沿既有墨墨 UI 展示；最小 schema/seed/兼容 saver 迁移随票交付。
- [ ] 原 create 工具不暴露给模型；框架阶段控制不等于业务授权，runtime 有界且查询失败不冒充无订单/无资格。
- [ ] 验证实际 LangGraph 执行/恢复、两 owner、选单及 checkpoint 越权、查询无多余确认；固定 provider 契约与真实模型另列。

- [ ] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [ ] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [ ] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开墨墨 HTTP/SSE → 实际 LangGraph → owner-scoped 隔离订单服务 → case/消息读取与应用重启恢复。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

当前阶段：scoped-technical-pass／待用户验收。原生 app/mercury 最小实现已冻结；同库 owner/order/case/消息与独立 checkpoint 已接通。已修复 fixture 外键写入次序、日志源码行泄漏、无事实模型虚构成功、未使用状态与查询后澄清丢失。最终两轮各 14 项离线通过，包含实际 SDK HTTP、持久 interrupt/resume；新 DOM 竞态验证通过。主会话 16:14 UTC 已确认修复后两轴复核关闭及本票范围技术通过。真实 qwen／真实浏览器与用户本人验收仍未完成，统一在 TASK16 保留明确门槛；不称完整系统已通过。

## 证据

新红测：[记录](../work/ceres2-runtime-upgrade/02/test-runs/red-mercury/output.txt)；[当前设计](../work/clean-rebuild/02/design.md)；[来源账本](../work/clean-rebuild/02/provenance.json)。离线绿测：[11 项结果](../work/ceres2-runtime-upgrade/02/test-runs/green-mercury-03/output.txt)；虚构成功红测：[记录](../work/ceres2-runtime-upgrade/02/test-runs/red-unverified-claim/output.txt)。尚无完整验收证据。历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-02-langgraph-aftersales-query.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

最终同版离线两轮：[14 项第一轮](../work/ceres2-runtime-upgrade/02/test-runs/final-mercury-05/output.txt)、[14 项第二轮](../work/ceres2-runtime-upgrade/02/test-runs/final-mercury-06/output.txt)、[同版指纹](../work/ceres2-runtime-upgrade/02/test-runs/final-mercury-clarification-source-comparison.json)。[DOM 竞态](../work/ceres2-runtime-upgrade/02/test-runs/dom-races/output.txt) 仅为受控 DOM，不是浏览器验收。

[发布源码清单](../work/clean-rebuild/02/release-source-manifest.json) 区分本票 owned 源码与 consumed 共享基础；[TASK13／15 接缝交接](../work/clean-rebuild/02/handoff.md)。本票未提交，主会话统一协调。

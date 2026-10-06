# Ceres2 Runtime 14：具体确认与售后回执

状态：**待验收**。
负责人：**TASK14 唯一实现负责人（implement_clean_aftersales_commit）**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过**（2026-10-05 17:19 UTC 主会话确认受控技术范围；最终 59／59 两次，含本票 23 场景，配对 DOM、typecheck/build 与两轴复审通过）。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户申请整单仅退款或单明细整行退货，先看具体提案，再明确确认；提交后故障/刷新/重复确认仍得到唯一实际回执。

## 阻塞关系

[13 同用户订单与售后贯通](ceres2-runtime-upgrade-13-canonical-order-aftersales.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [x] LangGraph 的资格→提案→等待确认→重验→幂等提交→回执完整贯通；保留有效 Mercury 政策与金额，不引入上游阈值或人工例外。
- [x] 原子申请/receipt、proposal/approval 版本、case 责任 fence、状态/时间/可退 fixture、所需增量迁移与摘要/确认 UI 同票交付。
- [x] 验证初次意图不写、错误/旧确认拒绝、规则/金额/期限边界、事务失败/提交后 checkpoint 失败、同事项人工负责时不可写。通过受控 case 责任状态测 fence；真实人工后台与此流程的联合演示由 P16 覆盖。

- [x] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [x] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [x] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开墨墨提案/确认/申请/回执 API 与页面；补充售后业务提交 unit-of-work（资格、申请、receipt）故障与竞争注入。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

主会话已确认本票受控技术发布；将 Mercury 钩子交接给后续票据。真实 qwen3.8-27b、真实浏览器与本人验收继续留在 TASK16；不把受控通过写成整体验收。

## 证据

2026-10-05 17:19 UTC：最终源码完成具体提案→真实 LangGraph interrupt→原子申请／回执、重复确认、故障恢复、增量迁移与 UI。迟到模型／人工责任、被拒替代请求和并发意图的有效审查问题均经新公共红测修复；两轴复审已关闭。Tester 最终依赖回归 **59／59 两次**，其中本票 **23** 场景；配对 DOM、typecheck/build 通过。源码指纹 `4e2fb91c6881958f1632256a9970f44338b7b845ff90ba787c2d79ffa4335e1d`。见[当前交接及准确证据链接](../work/clean-rebuild/14/handoff.md)。

历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-14-confirmed-aftersales-receipts.md)。旧测试结果、未提交源码和运行状态不作为本票通过证明。真实模型、真实浏览器及本人验收仍未完成。

# Ceres2 Runtime 09：聊天显式记忆与共享边界

状态：**待验收**。
负责人：**implement_clean_role_memory**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过**。2026-10-05 17:53 UTC 主会话已确认本票受控技术释放。原始同版 74／74 双轮、两轴审查及其后两项精确范围修复复验已完成；最终当前记忆回归 21／21 通过。真实模型、浏览器和本人验收仍待 TASK16。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户可在聊天中保存、查询、更正、删除四类记忆，新购买任务按需使用当前有效偏好；同用户可可与墨墨的实际聊天入口只读取各自需要的背景。

## 阻塞关系

[03 长期任务与可响应运行](ceres2-runtime-upgrade-03-persistent-responsive-runs.md)；[02 LangGraph 售后查询首切片](ceres2-runtime-upgrade-02-langgraph-aftersales-query.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [ ] 修通语义请求→确定性记忆命令→回执→消息展示；SQL 为权威，不加设置页或外部记忆系统。
- [ ] 当前条件/显式来源优先、完整查询与受限召回分开、owner/role/来源校验；四类数据及修改/删除版本 seed/必要迁移随票。
- [ ] 验证聊天 CRUD、跨任务使用、过期/删除立即不可用、跨 owner 拒绝和角色过滤；本票直接接通 P02 的真实墨墨入口，以隔离订单查询展示需要的相关记忆。实际角色共享在本票完整交付，不等待模拟结算或售后写入。

- [ ] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [ ] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [ ] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

两个角色公开聊天 HTTP/SSE、记忆命令回执与后续相关回答；隔离订单查询展示墨墨按需召回。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

按已获主会话释放的 [TASK10 交接](../work/clean-rebuild/09/HANDOFF-P10.md) 继续回复后提取与 Dream。记忆 SQL、两个真实 runtime 的聊天接缝、版本/删除/来源和角色边界已冻结；真实模型、真实页面及本人验收留待 TASK16。

## 证据

新工程实现/角色与事务契约见 [09 执行记录](../work/clean-rebuild/09/README.md)，新红/绿原始输出见 [专职测试记录](../work/ceres2-runtime-upgrade/09/test-runs/)。前置 02/03 已由主会话释放受控技术范围，Mercury 钩子在 14 冻结验收后接入；旧证据不继承。历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-09-explicit-role-memory.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

受控同版双轮：[74 第一轮](../work/ceres2-runtime-upgrade/09/test-runs/final-memory-01/output.txt)、[74 第二轮](../work/ceres2-runtime-upgrade/09/test-runs/final-memory-02/output.txt)、[原版范围指纹](../work/ceres2-runtime-upgrade/09/test-runs/final-memory-source-comparison.json)。其后精确修复：[只读 committed 标识](../work/ceres2-runtime-upgrade/09/test-runs/mutation-flag-successor-evidence.json)、[删除不复活自动前值](../work/ceres2-runtime-upgrade/09/test-runs/deletion-fence-successor-evidence.json)；各有红测与独立两次定向绿测，当前 [21 项记忆回归](../work/ceres2-runtime-upgrade/09/test-runs/deletion-fence-memory-regression/output.txt) 通过。旧 74 双轮不冒称验证了两个后续变更。[当前源码清单](../work/clean-rebuild/09/release-source-manifest.json) 区分 owned/transferred 与 consumed。

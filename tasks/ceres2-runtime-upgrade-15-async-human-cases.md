# Ceres2 Runtime 15：精简异步人工工单

状态：**待验收**。
负责人：**implement_clean_human_tickets**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过（主会话 2026-10-05 16:41 UTC 确认受控范围）：两次独立 36/36、DOM 双次、typecheck/build 通过，Standards／Spec 两轴复审均无剩余问题。真实 qwen／浏览器／用户本人及 P14 联合写事务留待 TASK16，不在本次通过范围**。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户明确要求人工、政策不确定或服务持续失败时，墨墨创建必要上下文工单；人工在小型后台查看、回复/追问、解决/关闭，用户看到进度。

## 阻塞关系

[02 LangGraph 售后查询首切片](ceres2-runtime-upgrade-02-langgraph-aftersales-query.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [x] 可基于 P02 的隔离 owner 订单/持久 case 演示，不等采购/结算完成；信息不足先澄清、明确不符合资格先解释，不承诺例外。
- [x] 最小可信 operator 保护、case 责任/generation fence、工单/消息状态迁移、两用户与处理者 fixture、人工和用户 UI 同票交付。
- [ ] 人工负责时 Agent 同事项写暂停；回复不是用户批准，解决/关闭不恢复旧授权。验证去重、隔离、触发/非触发、回复/追问/进度与责任竞争。
- [ ] 与 P14 共用同一个 case 责任契约，主会话指定共享定义唯一维护者；必要接口协调不伪造整张票阻塞。实际 canonical 订单和售后确认联合场景在 P16 验证。

- [ ] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [ ] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [ ] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开用户工单进度/消息接口与受保护人工后台；通过 case 责任 fence 验证归属和在途写竞争。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

两轴修复复审及主会话受控技术验收已完成；P14 在真实写事务中消费同一 canonical responsibility/generation，P16 验证联合旅程、真实 provider、真实浏览器和用户本人验收。实现源保持冻结，不提交或生成处理者凭据。共享定义、迁移与安全回退见 [当前交接](../work/clean-rebuild/15/handoff.md)。

## 证据

新实现与证据边界见 [当前交接](../work/clean-rebuild/15/handoff.md)，冻结源清单见 [source manifest](../work/clean-rebuild/15/release-source-manifest.json)。

- 初始公共 HTTP、业务服务异常、无效政策输入、业务服务超时、UI 新草稿丢失、旧工单回复新工单均有新工程 RED 证据；逐项最小修复，不继承归档通过。
- [最终第一次 36/36](../work/ceres2-runtime-upgrade/15/test-runs/final-human-05/evidence.json) 与 [第二次 36/36](../work/ceres2-runtime-upgrade/15/test-runs/final-human-06/evidence.json)：包含 P02/P13/P12 必要回归。实际 Python LangGraph + 受控业务/模型，SDK HTTP 兼容回归不等于 live 模型质量。
- [精确范围源码一致性](../work/ceres2-runtime-upgrade/15/test-runs/final-ticket-fence-source-comparison.json)：四次前后快照一致，fingerprint `1565ea10bc47ffdff768f8051cc85f5892089b0389287910269a24b4d8efcd31`。
- [用户／处理者 DOM 第一次](../work/ceres2-runtime-upgrade/15/test-runs/ticket-fence-dom-01/evidence.json)、[第二次](../work/ceres2-runtime-upgrade/15/test-runs/ticket-fence-dom-02/evidence.json) 均通过：精确 ticket_id、进度/追问/回复/解决、owner/case 展示、新草稿保留。实际 App `/operator/human-cases` 路由 [受控 DOM 通过](../work/ceres2-runtime-upgrade/15/test-runs/final-operator-route/evidence.json)。
- [typecheck](../work/ceres2-runtime-upgrade/15/test-runs/ticket-fence-typecheck/evidence.json)、[build](../work/ceres2-runtime-upgrade/15/test-runs/ticket-fence-build/evidence.json) 通过。仅受控 DOM，不声称真实浏览器、布局、真实凭据或用户验收。
- 处理者凭据默认关闭；全部测试使用明确命名的隔离合成值，未复用 provider key、未生成永久密钥。业务订单始终模拟，无退款/退货提交能力。

历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-15-async-human-cases.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

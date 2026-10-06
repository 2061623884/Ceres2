# Ceres2 Runtime 01：Pi 商品查询首切片

状态：**待验收**。
负责人：**implement_clean_pi_query**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过（2026-10-05 16:10 UTC，主会话批准的受控范围）**。真实 qwen3.8-27b、真实页面与用户本人验收仍待 TASK16 同版验收，不包含在本次技术通过结论内。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户在可可输入一个商品/品类目标，真实 Node/TypeScript Pi SDK 调用 Python 查询服务、读取结果后自主决定再查详情，最后在现有对话展示有事实依据的回答。只读商品旅程首先可用，不先恢复全部采购业务。

## 阻塞关系

无技术前置。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [ ] 交付最小宿主→Pi→只读工具→事实回复的 stdio 协议和配置契约；保留可信 owner、原 revision、真实 SDK 事件，不把旧完整路由包成工具。
- [ ] 使用最小两用户商品/供给 fixture；沿用公开 HTTP/SSE 与现有 UI。补本路径必需的类型/ContextPlan 声明，不扩大为整体 V2 helper 恢复。
- [ ] 一开始即实现 5 工具轮/30 秒探索上限、早完成/等待、停止闸门与无额外模型的可靠收口，不能先交无限循环再等后票修安全。
- [ ] 验证真实 SDK＋受控模型边界、多步工具证据、非法写工具/伪造引用、预算耗尽；真实 provider 兼容与模型自主性另列实测，不用 mock 证明。

- [ ] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [ ] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [ ] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开可可 HTTP/SSE → 实际 Pi SDK → 只读 Python 领域服务 → 用户可见事实；模型 transport/IPC 契约另测。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

宿主异常诊断修复及公开接缝红/绿已完成；最终两次公共行为复验均通过且 TASK01 与所依赖共享文件指纹相同。主会话已确认 Standards 问题修复闭环、Spec 无剩余问题并批准受控技术释放。下一步由主会话校验本票来源清单后本地提交并释放 TASK03；真实 qwen3.8-27b、真实页面与用户本人验收保留至 TASK16。

## 证据

2026-10-05 16:04 UTC：已选择性实现实际 SDK worker、Python adapter，以及全新最小 guide 模型/API/原子历史回执服务。新证据见下；历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-01-pi-product-query.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

2026-10-05 15:52 UTC：已明确共享 core/identity/catalog 由 foundation 单一维护，TASK01 独占 guide 模型/API/Pi adapter 与实际 SDK worker。选择性迁移来源及边界见 [清单](../work/clean-rebuild/01/MIGRATION.md)。所有技术结果重新验证。

### 新工程执行证据（截至 2026-10-05 16:04 UTC）

- [首次公共红测](../work/ceres2-runtime-upgrade/01/test-runs/red-pi/evidence.json)：缺失 app 实现，未继承旧通过。
- [首轮完整行为](../work/ceres2-runtime-upgrade/01/test-runs/green-pi-all-01/evidence.json)：20 passed；运行期间其他并行任务修改了全仓文件，结论仅针对 Tester 确认未变化的 TASK01 文件集合，不作为全仓同版通过。
- [IPC 关联红测](../work/ceres2-runtime-upgrade/01/test-runs/red-ipc-correlation/evidence.json)及[聚焦绿测](../work/ceres2-runtime-upgrade/01/test-runs/green-ipc-focused/evidence.json)：opaque run_id 与双向序号，真实 Node Pi SDK。
- [实际 SDK 构建](../work/ceres2-runtime-upgrade/01/test-runs/runtime-build-02/evidence.json)及[类型检查](../work/ceres2-runtime-upgrade/01/test-runs/runtime-typecheck-02/evidence.json)。
- [选择性来源与实际依赖](../work/clean-rebuild/01/MIGRATION.md)、[最小契约](../work/clean-rebuild/01/CONTRACT.md)。
- 当前无真实 provider/模型自主性、真实页面或用户本人验收结论；受控 HTTP 模型 fixture 只验证 SDK/业务契约。

### 最终修复复验（2026-10-05 16:08 UTC）

- Standards 宿主异常诊断问题：公开 SQL 驱动故障注入先红，再验证安全 run_id／允许列表异常类型／原因 SHA256 日志，用户只见通用错误；不记录原始错误正文或 traceback。见 [红测](../work/ceres2-runtime-upgrade/01/test-runs/red-host-diagnostics/evidence.json)、[绿测](../work/ceres2-runtime-upgrade/01/test-runs/green-host-diagnostics/evidence.json)。
- 最新 [完整第 1 次](../work/ceres2-runtime-upgrade/01/test-runs/final-pi-01/evidence.json)：21 passed，49.57s。
- 最新 [完整第 2 次](../work/ceres2-runtime-upgrade/01/test-runs/final-pi-02/evidence.json)：21 passed，49.58s。
- [源码一致性比较](../work/ceres2-runtime-upgrade/01/test-runs/final-pi-source-comparison.json)：四个前后快照中 TASK01、依赖的共享 core/main/model registry/migration、测试、依赖锁与编译 worker 完全一致；指纹 `fed4017d9923ecc8ba976f65b16b0ea0f6513fb68fddd18b25222759382e66c0`。第二次全仓只变化无关 Mercury graph/tests，不声称全仓完全冻结。
- 实现者没有执行测试、lint、typecheck 或 build；以上全部由专职 Tester 新工程执行。没有提交或推送。

### 主会话技术释放（2026-10-05 16:10 UTC）

受控通过范围（技术放行时）：实际 Pi SDK 1.0.3＋公开 HTTP/SSE＋受控模型 HTTP transport、两用户隔离、候选事实引用与有限澄清、5 工具轮／15 秒保护、停止闸门、最终原 revision CAS 与同事务历史／回执，以及诊断安全。2026-10-06 用户将当前导购保护边界调整为 30 秒；本次回归和真实运行按新边界记录，不改写原受控证据。Standards P2 已闭环，Spec 无剩余问题；最终 21 场景两次稳定验证为本工程新结果，不继承 archive。

提交边界见 [本票清单](../work/clean-rebuild/01/RELEASE.json)；共享依赖仅引用见 [依赖指纹](../work/clean-rebuild/01/CONSUMED-FOUNDATION.json)；[TASK03 接口交接](../work/clean-rebuild/01/HANDOFF-P03.md)。实现者未提交。

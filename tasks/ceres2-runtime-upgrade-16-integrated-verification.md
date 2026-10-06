# Ceres2 Runtime 16：同版完整生命周期验收

状态：**阻塞／待验收**（受控同版技术集成通过；真实 provider／真实浏览器／用户体验门槛未完成）。
负责人：**implement_clean_final_integration**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
受控技术验收：**通过（294／294 两次，45 项匹配源码检查通过，两轴源码审查关闭；主会话 20:58 UTC 确认）**。
整体验收：**未完成，不标已验收**。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

在同一固定版本和隔离数据上，完成两类 P0、V2 人数/多菜/供给/比较/记忆/复购、模拟订单、售后确认与精简人工的完整演示和分层验收清单。

## 阻塞关系

[08 品类筛选与真实比较](ceres2-runtime-upgrade-08-category-comparison.md)；[10 可恢复提取与 Dream](ceres2-runtime-upgrade-10-recoverable-memory-dream.md)；[11 历史提醒与重新采购](ceres2-runtime-upgrade-11-historical-repurchase.md)；[14 具体确认与售后回执](ceres2-runtime-upgrade-14-confirmed-aftersales-receipts.md)；[15 精简异步人工工单](ceres2-runtime-upgrade-15-async-human-cases.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [ ] 场景包括：新目标比较→精确确认→模拟结算→售后提案/回执；历史多菜复购→当前缺货/条件修订→重新确认；人工工单与在途售后写竞争→进度/关闭；停止、关页与恢复穿插验证。
- [ ] 固定源码/未提交变动、依赖、schema/seed/index、模型/Prompt/时钟；整合最小数据重建、重复迁移、事实保全和安全只读回退，不对活动生产库操作。
- [ ] 补齐所有前票残留的真实 provider/页面证据，离线与 live 不混用；记录自然完成/等待/保护终止/失败和可靠结果，保护终止不算成功。两次独立新增业务验证、最终 Standards/Spec 两轴审查与有效修复复验。
- [ ] 交付已证实/未证实/阻塞清单与用户本人体验步骤；本人验收单列，历史失败不追认，未达全部条件不标整体已验收。此票不能替代各前票的必要测试。

- [ ] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [ ] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [ ] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

同版公开 HTTP/SSE、真实页面、持久业务结果与既定三类提交事务边界；真实 Pi、LangGraph 和模型分层留证。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

1. 安全手动配置实际 provider：`LLM_MODEL`、`MEMORY_EXTRACTION_MODEL`、`MEMORY_DREAM_MODEL` 均为 `qwen3.8-27b`；配置正确 endpoint 与凭据，不使用聊天中粘贴的密钥，不复制旧 `.env`。人工后台使用独立 operator 凭据。
2. 提供获准且可用的真实浏览器路径。保留既有 localhost `ERR_BLOCKED_BY_CLIENT` 与 shell Chromium `EPERM` 阻塞记录，不绕过限制。
3. 在全新隔离 DB/checkpoint 启动后，由用户体验：比较→选择→报价接受（如需）→独立加购→模拟结算→同订单售后提案/确认/回执；历史多菜复购改条件/缺货后重新确认；人工进度/关闭后新提案；停止与关页恢复；记忆更正/删除。均为模拟业务。本人验收单独记录。

完整命令、已证实/未证实范围及体验步骤见 [DELIVERY](../work/clean-rebuild/16/DELIVERY.md)。

## 最终受控证据

- `work/ceres2-runtime-upgrade/16/test-runs/final-backend-01/` 与 `final-backend-02/`：全量 294／294 两次，退出码 0／0，369.68 秒／368.93 秒。
- [四份源码与最终检查核对](../work/ceres2-runtime-upgrade/16/test-runs/final-integrated-source-comparison.json)：四个 before/after、冻结 inventory 与当前 320 文件一致；45 项最终 DOM/build/typecheck/pip 记录均同源通过。指纹 `b711e091dd35bd646062946a76c1f57b4e514f6a243eb1a9efe917874b63b6ba`。
- 同目录 `inventory/` 保留源码内容、依赖/静态数据、空库重复迁移/seed、时钟与配置范围。最终全量包括合成旧库、事实保全和只读回退；无旧活动库迁入。
- [两轴源码审查关闭](../work/clean-rebuild/16/final-review-closure.md)。预算报价、过期页面快照、数量控件、澄清/菜品候选上下文与等待确认语义都有对应公共 RED→修复→GREEN；初始完整旅程本来通过，不伪造 RED。
- 真实 Pi SDK／LangGraph 与受控 provider 的通过不证明实际 qwen、真实页面或本人验收。全部外部门槛仍未完成。

历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-16-integrated-verification.md)。旧结果不作为本票通过证明。

## 2026-10-06 配置与测试隔离补充

用户已手动配置凭据；本地配置加载检查通过，未验证真实接口。发现受控测试可能继承配置后，新增测试收集前隔离与合成子进程回归。独立受控全量 **295／295 两次通过**，322 个源码文件同版，两轴审查关闭；生产源码未改动，真实凭据未被使用或发送。详情见 [隔离复验](../work/live-validation/TEST-ISOLATION-REVIEW.md)。这不替代真实 qwen、真实浏览器或用户验收，当前外部门槛仍保留。

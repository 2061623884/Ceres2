# Ceres2 Runtime 16：同版完整生命周期验收

状态：**待验收**（最新隔离 DeepSeek API 生命周期批次通过；真实浏览器、扩展场景与用户本人体验门槛未完成）。
负责人：**implement_clean_final_integration**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
受控技术验收：**通过（294／294 两次，45 项匹配源码检查通过，两轴源码审查关闭；主会话 20:58 UTC 确认）**。
整体验收：**未完成，不标已验收**。
用户本人验收：**待验收／未完成**。
最新真实 API 批次：**41／41 checks 通过**，Pi 比较、选品、模拟结算/重放及 Mercury 退款提案/确认/重放均完成；Dream 因阈值未达到而跳过。

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

1. 用户本人在已打开的真实浏览器中验收当前工作区，确认页面交互、错误提示与启动/恢复体验。若进程需重载以读取本轮后端提示词改动，先保留活动数据库与会话，只重启服务进程。
2. 补齐未覆盖场景：历史多菜复购改条件/缺货后重新确认；人工进度/关闭后新提案；停止与关页恢复；记忆更正/删除；Dream 阈值触发。保持隔离数据并记录证据。
3. 对新增版本完成两次独立行为验证与最终 Standards/Spec 审查；重新核对固定源码、依赖、seed、模型/Prompt、时钟和迁移范围。

最新批次细节：2026-10-06，`deepseek-flash` / `api.deepseek.com`，fresh isolated DB，34.02 秒，exit 0；`api_batch_passed`，41／41 checks。`test_mercury_public.py` 与 `test_aftersales_public.py` 为 31／31。证据：[脱敏 evidence](../work/live-validation/tmp/live-20261006T062210Z-0575eb5f534d/evidence)。之前的失败证据保持原状，不追认为成功；原 `run_live_batch.py` 未修改，实际写入只在本次临时 demo DB。浏览器、历史复购、供给修订、独立第二次运行、记忆修订/删除与人工工单仍未覆盖。

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

### 本地接手与真实 API 尝试

在 `3283e28` 上，Tester 使用 Python 3.11.15 创建 `.venv`；后端 lock 安装和 `pip check`、Pi runtime build、前端 build 通过。Node 22.19.0/npm 10.9.3。Python 3.12.14 未能从当前 uv Python 源获取；现用版本满足 `>=3.11`。前端构建有 Vite 配置警告，npm 提示一项 high severity 依赖漏洞。

用户明确要求后，Tester 于 2026-10-06 03:42 UTC 仅运行一次 bounded live API batch，退出码 1。配置、隔离路径、seed 和 live health gate 通过；Pi 比较返回 `protected`、`runtime_status=deadline`、`answer_status=failed`。15 秒边界前完成 4 轮工具交互，第 5 轮模型调用未完成。没有观察到上游 HTTP 状态或传输原因；购买、结算和 Mercury 未运行。保留原失败记录：[脱敏 evidence](../work/live-validation/tmp/live-20261006T034233Z-d66f017a40aa/evidence)。未自动重试，未查看相邻 `private-state`。此结果不满足 live 验收条件，TASK16 仍阻塞／待验收。

### 用户要求改为 30 秒后的复测

Pi runtime `npm run typecheck` 和 `npm run build` 均退出 0。将 admission 测试锁等待更新为 31 秒，并把测试 fixture 自身 SQLite busy timeout 调至 40 秒后，完整受影响模块复跑 **23 项全部通过**（87.70 秒，退出码 0）。

用户于 2026-10-06 要求将导购保护上限调至 30 秒后，专职 Tester 在更新的未提交工作树上执行一次 bounded live batch，退出码 1，耗时约 9.87 秒。配置、隔离、seed 和 live health gates 通过；Pi 比较阶段返回应用级 `422 PI_UNKNOWN_REFERENCE`（`retryable=false`）。这不是 deadline；公共证据没有 `runtime_status`、工具轮数、provider upstream HTTP status 或 transport cause。比较未完成，购买、结算、Mercury、提取和记忆阶段未运行。证据：[脱敏 evidence](../work/live-validation/tmp/live-20261006T044045Z-ade5f6652231/evidence)。未重试，未查看相邻 `private-state`。TASK16 仍阻塞／待验收。

# T09：同版回归两轴审查与交接

- 状态：进行中（冻结81b02f9，全部同版门槛与两轴并行执行）
- 负责人：Tester + 独立 Standards/Spec；Merger 只整合；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T08 统一评测事件与运行版本](ceres2-local-cloud-integration-08-evaluation-provenance.md)

## What to build / 合同

同一冻结候选覆盖九票组合；两轴基于 baseline...HEAD 全范围只读审查；有效问题集中修复后重冻重验受影响项；受控、真实模型、真实浏览器、本人接受分开，未运行不称通过。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] backend 全量、Pi typecheck/build、frontend strict TypeScript/build、相关 DOM/受控浏览器、wire、九票跨域回归；审查修复源 pin、依赖与构建证据；列出 blocked/not run。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

固定候选 `81b02f956298361cf9044ee289c0821a8275fab8`：backend/runtime等于T08-B `c1a99cf`，frontend等于T05 `4278eea`，合并无冲突。Tester在独立冻结工作树执行最终backend full、Pi/frontend严格编译/build及相关DOM/HTTP/wire；两轴并行审查 `37c984...81b02f9` 全范围。

实际浏览器保持BLOCKED（IPC权限/跨环境host不可达，未进入UI），真实provider与用户验收NOT RUN。test-support launcher的进程组清理P2由独立owner修复，若仅support变化则单独固定源/测试/审查绑定，不冒充产品全量已包含该后继。未有终态报告的项保持PENDING。[冻结清单](../work/local-cloud-integration/t09/frozen-source.json)。

# T09：同版回归两轴审查与交接

- 状态：待开始
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

尚未实现；等待上列依赖交付。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

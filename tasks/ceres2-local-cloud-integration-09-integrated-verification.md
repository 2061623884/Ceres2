# T09：同版回归两轴审查与交接

- 状态：待验收（技术实现与受控门槛完成；实际浏览器/真实provider/用户本人验收未完成）
- 负责人：Tester + 独立 Standards/Spec；Merger 只整合；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T08 统一评测事件与运行版本](ceres2-local-cloud-integration-08-evaluation-provenance.md)

## 最终当前结论（2026-10-07）

本票技术实现已进入最终产品 `f963017587b3eab30965ffcd3aab90fcc3852f3e`，受控验证/两轴修复闭环见[最终报告](../work/local-cloud-integration/t09/FINAL-VERIFICATION.md)。全量746通过/5跳过属于`81b02f9`；同版知识环境补齐跳过项，最终狭窄修复183例及合入4例另行绑定，不声称最终pin重新全量。实际浏览器BLOCKED、真实provider/用户本人验收NOT RUN，不能把技术完成等同于整体验收。

以下阶段记录按各自固定pin保留，旧“待实现/待交接”等描述属于历史过程，不推翻本节当前结论。

## What to build / 合同

同一冻结候选覆盖九票组合；两轴基于 baseline...HEAD 全范围只读审查；有效问题集中修复后重冻重验受影响项；受控、真实模型、真实浏览器、本人接受分开，未运行不称通过。

## 验收

- [x] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] backend 全量、Pi typecheck/build、frontend strict TypeScript/build、相关 DOM/受控浏览器、wire、九票跨域回归；审查修复源 pin、依赖与构建证据；列出 blocked/not run。
- [x] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [x] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [x] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

固定候选 `81b02f956298361cf9044ee289c0821a8275fab8`：backend/runtime等于T08-B `c1a99cf`，frontend等于T05 `4278eea`，合并无冲突。Tester在独立冻结工作树执行最终backend full、Pi/frontend严格编译/build及相关DOM/HTTP/wire；两轴并行审查 `37c984...81b02f9` 全范围。

实际浏览器保持BLOCKED（IPC权限/跨环境host不可达，未进入UI），真实provider与用户验收NOT RUN。test-support launcher的进程组清理P2由独立owner修复，若仅support变化则单独固定源/测试/审查绑定，不冒充产品全量已包含该后继。未有终态报告的项保持PENDING。[冻结清单](../work/local-cloud-integration/t09/frozen-source.json)。

- [ ] 剩余实际浏览器、获准的真实provider与用户本人验收按最终报告独立完成；不由受控结果自动勾选。

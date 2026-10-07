# T06：显式 GraphRAG 与规范菜谱事实

- 状态：待开始
- 负责人：knowledge/runtime owner (T04→T06 交接)；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T02 Canonical 商品召回与当前 Offer](ceres2-local-cloud-integration-02-canonical-shopping.md)；[T04 可选审校过程消息与 SSE](ceres2-local-cloud-integration-04-reviewed-interim-sse.md)

## What to build / 合同

官方 GraphRAG 显式工具与 deterministic recipe_facts 共存；基准用量/必需食材来自规范事实；未知调料数量保持未知；模型选择/规范关系区分，GraphRAG 调用也官方 hostname thinking disabled、受剩余预算约束。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] 显式图查询 vs 普通 recipe_facts；规范用量和 unknown；缺索引/图失败；当前商品证据、官方/非官方 transport；真实 GraphRAG 和 BGE 只有 Tester 授权环境实际执行才记通过。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

尚未实现；等待上列依赖交付。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

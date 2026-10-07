# T08：统一评测事件与运行版本

- 状态：待开始
- 负责人：evaluation/runtime owner (T06→T08 交接)；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T05 本地界面适配新入口与协议](ceres2-local-cloud-integration-05-integrated-ui.md)；[T06 显式 GraphRAG 与规范菜谱事实](ceres2-local-cloud-integration-06-explicit-graphrag.md)；[T07 售后数量照片与工单证据范围](ceres2-local-cloud-integration-07-aftersales-ticket-evidence.md)

## What to build / 合同

policy judgment/lookup/reuse/summary、model usage、retrieval、graph retrieval、interim 审校独立计数；未知保持 null/unknown；真实 runtime version 在运行时记录，export source snapshot 只代表导出时；显式 owner 导出/人工标签，无自动质量正标签。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] 运行事件→导出→人工标签：usage 去重/缺失、事件尾裁剪计数、runtime/export 版本不同、owner join、失败登记不自动训练，安全输出无凭据。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

尚未实现；等待上列依赖交付。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

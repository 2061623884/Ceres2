# T03：同 Pi 原生完成与混合引用

- 状态：待开始
- 负责人：runtime owner (T01→T03 交接)；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T01 Hybrid 政策与有界预取复用](ceres2-local-cloud-integration-01-policy-hybrid-deadline.md)

## What to build / 合同

同 Pi guide_request→finish_response，兼容 policy_ref/policy_refs、购物/菜谱/general/role boundary/waiting 的合法组合；Python 逐引用校验；维持 cloud kind 工具限制、5 轮、15 秒、取消和事务回滚。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] 受控真实 Node JSONL 与 Guide HTTP/SSE：原生终止、混合 refs、非法/陈旧 refs、waiting+policy+role boundary、取消/超时与零业务副作用。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

尚未实现；等待上列依赖交付。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

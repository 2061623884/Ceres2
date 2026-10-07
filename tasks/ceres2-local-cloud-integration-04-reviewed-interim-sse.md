# T04：可选审校过程消息与 SSE

- 状态：进行中（T03 技术门槛已放行，交接 runtime/message owner）
- 负责人：runtime/message-schema owner (T03→T04 交接)；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T03 同 Pi 原生完成与混合引用](ceres2-local-cloud-integration-03-native-finish-mixed-refs.md)

## What to build / 合同

候选文本经独立同模型审校后才能发布；零条允许；稳定 message ID、message.interim 与真实事件时间；恢复去重，停止/过期/超时后不发布；不泄露 reasoning 或绕过最终事实投影。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] 受控 Pi→Python→SSE/回执：审校通过/拒绝/超时、稳定 ID、重连/重复消息、停止栅栏、私有内容不公开、未知历史时间不补造。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

依赖 T03 已合入 canonical `4fd13b3` 并经固定 postmerge 37例验证，技术放行；runtime owner 从此产品基线接管。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

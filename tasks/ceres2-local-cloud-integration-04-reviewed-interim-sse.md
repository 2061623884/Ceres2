# T04：可选审校过程消息与 SSE

- 状态：待验收（技术门槛/两轴已过并合入，固定共存postmerge通过，最终验收开放）
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


## 技术交付

最终 `4cf49a7` Tester 92例/161.64s通过、源码/harness稳定，其中本票19专属interim例。typecheck/build在`0c77e59`，最终候选runtime源码及dist哈希完全相同，有独立binding。诊断丢失P2修复后两轴复审关闭；最后仅把旧primary官方wire期望与T03 native auto/no response_format对齐，validator/额度/官方hostname边界不变。原90通过/2失败记录保留，不以最终结果覆盖历史。

`4cf49a7`无冲突合入`e0f57cd`，T04 runtime/Guide源码与受测pin相同，T06-A knowledge/Dish源码与`277c110`相同。固定detached `e0f57cd` 共存postmerge37例/46.30s与独立锁runtime安装/build通过，无源码/harness漂移。T06-B runtime正式转交，T05依赖已解除；无需等待发布。

[验证摘要](../work/local-cloud-integration/t04/verification-summary.json)、[build绑定](../work/local-cloud-integration/t04/final-build-binding.json)、[源码关系](../work/local-cloud-integration/t04/source-equivalence.json)。不声称前端或最终整体验收。

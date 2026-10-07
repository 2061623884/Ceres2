# T04：可选审校过程消息与 SSE

- 状态：待验收（技术实现与受控门槛完成；实际浏览器/真实provider/用户本人验收未完成）
- 负责人：runtime/message-schema owner (T03→T04 交接)；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T03 同 Pi 原生完成与混合引用](ceres2-local-cloud-integration-03-native-finish-mixed-refs.md)

## 最终当前结论（2026-10-07）

本票技术实现已进入最终产品 `f963017587b3eab30965ffcd3aab90fcc3852f3e`，受控验证/两轴修复闭环见[最终报告](../work/local-cloud-integration/t09/FINAL-VERIFICATION.md)。全量746通过/5跳过属于`81b02f9`；同版知识环境补齐跳过项，最终狭窄修复183例及合入4例另行绑定，不声称最终pin重新全量。实际浏览器BLOCKED、真实provider/用户本人验收NOT RUN，不能把技术完成等同于整体验收。

以下阶段记录按各自固定pin保留，旧“待实现/待交接”等描述属于历史过程，不推翻本节当前结论。

## What to build / 合同

候选文本经独立同模型审校后才能发布；零条允许；稳定 message ID、message.interim 与真实事件时间；恢复去重，停止/过期/超时后不发布；不泄露 reasoning 或绕过最终事实投影。

## 验收

- [x] 以上端到端业务合同完整实现，保留来源与安全边界。
- [x] 受控 Pi→Python→SSE/回执：审校通过/拒绝/超时、稳定 ID、重连/重复消息、停止栅栏、私有内容不公开、未知历史时间不补造。
- [x] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [x] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [x] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

依赖 T03 已合入 canonical `4fd13b3` 并经固定 postmerge 37例验证，技术放行；runtime owner 从此产品基线接管。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。


## 技术交付

最终 `4cf49a7` Tester 92例/161.64s通过、源码/harness稳定，其中本票19专属interim例。typecheck/build在`0c77e59`，最终候选runtime源码及dist哈希完全相同，有独立binding。诊断丢失P2修复后两轴复审关闭；最后仅把旧primary官方wire期望与T03 native auto/no response_format对齐，validator/额度/官方hostname边界不变。原90通过/2失败记录保留，不以最终结果覆盖历史。

`4cf49a7`无冲突合入`e0f57cd`，T04 runtime/Guide源码与受测pin相同，T06-A knowledge/Dish源码与`277c110`相同。固定detached `e0f57cd` 共存postmerge37例/46.30s与独立锁runtime安装/build通过，无源码/harness漂移。T06-B runtime正式转交，T05依赖已解除；无需等待发布。

[验证摘要](../work/local-cloud-integration/t04/verification-summary.json)、[build绑定](../work/local-cloud-integration/t04/final-build-binding.json)、[源码关系](../work/local-cloud-integration/t04/source-equivalence.json)。不声称前端或最终整体验收。

- [ ] 剩余实际浏览器、获准的真实provider与用户本人验收按最终报告独立完成；不由受控结果自动勾选。

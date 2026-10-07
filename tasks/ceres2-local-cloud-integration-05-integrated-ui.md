# T05：本地界面适配新入口与协议

- 状态：待开始
- 负责人：frontend owner；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T02 Canonical 商品召回与当前 Offer](ceres2-local-cloud-integration-02-canonical-shopping.md)；[T04 可选审校过程消息与 SSE](ceres2-local-cloud-integration-04-reviewed-interim-sse.md)；[T07 售后数量照片与工单证据范围](ceres2-local-cloud-integration-07-aftersales-ticket-evidence.md)

## What to build / 合同

保留 incoming 视觉页面和购物售后入口；ready/switch、capability=null、entry_judgment；yes 确认/拒绝、Momo 文字零 Kev、纯按钮 handoff=null；混合 messages/navigation_action 和 interim 全量显示；不得恢复旧 unavailable 手动续接授权。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] Typed DOM/浏览器：yes 接受/拒绝、no/uncertain/error 可可继续、Momo 返回按钮零重放、混合消息、停止/恢复、重复点击、同订单/异单、关闭重开和前后导航。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

尚未实现；等待上列依赖交付。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

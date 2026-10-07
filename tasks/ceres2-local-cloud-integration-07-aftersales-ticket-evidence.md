# T07：售后数量照片与工单证据范围

- 状态：待开始
- 负责人：implement_aftersales_evidence_slice（售后/DB/migration 唯一 owner）；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：无（可开始，与 T01 无共享文件）

## What to build / 合同

问题包装数量、最多三张合法图片、选单版本与模拟顺序订单推进；明确确认后申请/回执/人工工单同事务；工单列表和照片 GET 必须精确关联该票证据，阻止同 case/order 无关、后续代次和跨 owner 读取。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] 公开模拟订单/售后/人工 API：数量澄清、越量、照片 MIME/大小/个数、跨 owner/case/order/selection、旧工单与后续代次、无关同单照片、重放幂等和事务回滚。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

尚未实现；等待主会话分配独立工作树；无需等待 T01。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

共享 model/migration registry 由本票 owner 唯一维护。T04 的事件时间列通过该 owner 串行登记或正式提交后交接。T01 Mercury deadline 接线亦由本票 owner 写入其文件。

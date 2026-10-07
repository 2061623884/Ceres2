# T07：售后数量照片与工单证据范围

- 状态：待验收（核心与 Mercury 技术门槛通过并合入；postmerge 通过，最终整合仍开放）
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

售后核心已合入，postmerge 最小检查13 passed。T01 后 Mercury 产品 pin `79a7eff`、交接 `24ee4d0` 已有63 affected passed / 38.24s，无源码/harness 漂移；首次缺 Pi SDK 的运行标记 invalid setup，不算产品失败或通过。该小 delta 两轴已无发现，交接 `24ee4d0` 无冲突合入 `4616798`；backend/runtime/frontend/data 与受测 `79a7eff` 零差异。Tester 在固定 detached `4616798` 的 postmerge 最小验证11 passed / 7.25s，无源码/harness 漂移；T05 的本票依赖已解除，T02/T04 依赖保持。

共享 model/migration registry 由本票 owner 唯一维护。T04 的事件时间列通过该 owner 串行登记或正式提交后交接。T01 Mercury deadline 接线亦由本票 owner 写入其文件。

## 已合入核心阶段

产品 pin `0a6e8fa83d14165844e81f3d8e8d1a016c35ece2`，交付 `0ff65a0a16a7a8a281452357ebdb2ca3b7d25385`，无冲突合入 `5f592575e9117ecdf2ae354faa14dad2bb2a92a8`。集成 backend/runtime/frontend/data 与产品 pin 零路径差异（Git source equivalence，不是重新测试）。专职 Tester 75 affected passed，两轴已关闭精确工单关联和图片实际解码两项问题；[验证](../work/local-cloud-integration/t07/verification.md)、[交接](../work/local-cloud-integration/t07/handoff.md)。postmerge 最小核验13 passed；Mercury 后续候选状态见上文，T05 的本票依赖已解除；不称整体已验收。


Mercury 证据：[受控验证](../work/local-cloud-integration/t07/mercury-verification.json)、[源码等价](../work/local-cloud-integration/t07/mercury-source-equivalence.json)、[Standards](../work/local-cloud-integration/reviews/t07-standards-79a7eff.md)、[Spec](../work/local-cloud-integration/reviews/t07-spec-24ee4d0.md)。同版最终整合、真实验证与用户验收仍为独立门槛。

固定 postmerge 证据：[11 例最小验证](../work/local-cloud-integration/t07/mercury-postmerge-minimum.json)。

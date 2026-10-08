# 03 同版完整测试与组件/浏览器覆盖

- 状态：待验收；实际分层验证与失败补验已完成，整体本人验收未发生。
- 负责人：专职 test_optimization；缺失行为测试由主会话分配唯一实现 owner。
- 所属：[总 TASK](ceres2-local-followup.md)；[规格](../docs/plans/ceres2-local-followup-spec.md)。
- 前置：01/02 最终源码冻结；无真实 provider 的范围不依赖 04 配置。

## 范围与验收

- [ ] 当前 backend 全量，Pi/frontend typecheck/build；安装/测试/服务/浏览器命令全部由 Tester 执行。
- [ ] BGE/BM25/RRF 实际组件与官方 GraphRAG 受控合同；真实 provider 的 Graph 构建/查询另归 04。
- [ ] 公共购物/模拟订单/售后、确认/幂等、身份隔离、停止/SSE 恢复，以及 Memory/Dream 时钟和重启合同。
- [ ] 实际浏览器旅程另列 provider 是否受控，错误与未运行如实保留；不把 DOM 或 API 通过称本人验收。
- [ ] 所有结果对应源码、未提交内容、fixture、索引、模型/Prompt 和命令；历史计数不继承。

证据：[产品完整752/4与环境补验](../work/local-followup/01/product-baseline-170-full.md)、[最终补修后新工具29项](../work/local-followup/01/tool-combined-final-delta.md)、[构建](../work/local-followup/01/node-builds-final.md)、[官方库5项](../work/local-followup/03/graph-official-library.md)、[真实BGE4项](../work/local-followup/03/real-bge.md)、[18开发指标v2](../work/local-followup/03/retrieval-dev-metrics-v2.md)。产品source为170 tracked freeze；新工具对应代码`739f13ead0c53ce9d82519efc30f51263e29ab45`及213文件manifest，不把两者混成同一全量pin。原[26项](../work/local-followup/01/tool-combined-final.md)保留e855候选证据。当前没有产品源码变化。

现有本机Firefox run11保持170对应产品证据；当前不新增浏览器运行，不称真实model/UI本人通过。739最终两轴审查完成，下一步用户审阅；只对新发现真实问题作必要复验。

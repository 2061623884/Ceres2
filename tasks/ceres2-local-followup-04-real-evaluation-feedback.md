# 04 真实模型评测与失败反馈

- 状态：阻塞；真实 provider/模型、Kev、Memory/Dream 独立配置缺失，100计划均未执行。
- 负责人：主会话协调，Tester 运行与维护隔离验收；产品缺陷另指定唯一 owner。
- 所属：[总 TASK](ceres2-local-followup.md)；[规格](../docs/plans/ceres2-local-followup-spec.md)。
- 前置：01/02 场景/脚本/评分冻结，可信本地配置就绪。不得挪用旧配置或凭据。

## 范围与验收

- [ ] 40 公开回归、20 新隔离验收、20 核心各三次，共 100 计划执行；先核对 pilot，再同版继续，失败/未执行均保留。
- [ ] 实际功能、关键违规、等待/拒绝、逐轮时延、首个有用结果、usage 覆盖与核心稳定性分别报告。
- [ ] 真实官方 GraphRAG build/local/global，以及 Memory 提取/Dream 所需实际调用；不以脚本 fixture 代替。
- [ ] 采集→显式标注→失败回归→有依据修复→同条件版本比较形成一次闭环。自然度由人工判断，模型诊断不替代业务事实。
- [ ] 本人接受 UI/语言质量；未完成保留待验收，不因程序结束关闭。

证据：[20新验收与60bundle/100计划](../work/local-followup/04/ACCEPTANCE-MANIFEST.md)。100planned/0attempted/100not_run/100unknown，原未执行误评分8fail和离线修正版本均留存，没有HTTP/模型调用。来源、病例隔离局限明确，不能称盲测/泛化。

另一个明确未完成项是完整订单/售后/Memory状态setup与更多动作driver；当前工具只支持小型采购续问/确认/重放，受控生命周期测试不能替代这些真实任务评测。下一步：可信配置就绪后先核心pilot与评分核对，按模型质量缺口补必要driver和有依据的产品优化；不提前付费采样或猜模型。

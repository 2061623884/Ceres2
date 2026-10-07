# T02：Canonical 商品召回与当前 Offer

- 状态：待开始
- 负责人：prepare_shopping_filter_slice（shopping owner）；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T01 Hybrid 政策与有界预取复用](ceres2-local-cloud-integration-01-policy-hybrid-deadline.md)

## What to build / 合同

商品 hybrid 服从 canonical 分类/审核/条件和允许 ID；不能先全库 top-k 再丢合法候选；current Offer 重读；价格库存不从 embedding 取值。采用代表性静态 fixture 和可重复 seed，不重置可变 Offer。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] 公开 products 与 Pi 商品工具：品类+检索、多合法候选被全局 top-k 挤出、未知 SKU、当前 Offer 变动、重复 seed 不重置库存、明确加购。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

尚未实现；等待上列依赖交付。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

负责 catalog/comparison/explore 运行内检索链透传原 deadline/取消；普通商品 HTTP 明确单请求预算，不因检索调用重置预算。不得写 knowledge core 或共享 schema；接口需求交当前 owner。

## 合成演示数据与正负例

允许最多两条最小可重复的合成演示正例：明确 selling_unit=case 且有字段来源的箱装水，以及 attribute_evidence.sugar_free={value:true,source:...} 的茶。来源必须明确是合成演示定义，不得伪称外部真实商品事实。packaging 是容器类别，pack_count 是内装数量，均不单独证明箱装；保留现有12瓶水不推定箱装、无可靠无糖事实的原茶仍 unknown/noverified。新增正例与原数据负例分别验收，不能用新商品掩盖原事实缺口。别名在匹配边界处理且保留原始条件；不增加无调用方 schema。21st-candidate 和其他负例保持 test-local。

为避免 T01↔T02 循环，五份 incoming 静态检索来源由 Merger 在 prerequisite 提交精确迁入（products/recipes/ingredients/policies/knowledge-provenance）。offers 及 seed/current Offer 仍由 T02 负责；该源码迁入不代表已建索引、已运行 seed 或 RAG 通过。T01 消费此提交后，后续 fixture 改动必须与来源 snapshot/version 同步；T02 获得明确所有权后再新增演示字段。

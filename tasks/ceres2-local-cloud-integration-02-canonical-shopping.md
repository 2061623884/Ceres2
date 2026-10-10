# T02：Canonical 商品召回与当前 Offer

- 状态：待验收（技术实现与受控门槛完成；实际浏览器/真实provider/用户本人验收未完成）
- 负责人：prepare_shopping_filter_slice（shopping owner）；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T01 Hybrid 政策与有界预取复用](ceres2-local-cloud-integration-01-policy-hybrid-deadline.md)

## 最终当前结论（2026-10-07）

本票技术实现已进入最终产品 `f963017587b3eab30965ffcd3aab90fcc3852f3e`，受控验证/两轴修复闭环见[最终报告](../work/local-cloud-integration/t09/FINAL-VERIFICATION.md)。全量746通过/5跳过属于`81b02f9`；同版知识环境补齐跳过项，最终狭窄修复183例及合入4例另行绑定，不声称最终pin重新全量。实际浏览器BLOCKED、真实provider/用户本人验收NOT RUN，不能把技术完成等同于整体验收。

以下阶段记录按各自固定pin保留，旧“待实现/待交接”等描述属于历史过程，不推翻本节当前结论。

## What to build / 合同

商品 hybrid 服从 canonical 分类/审核/条件和允许 ID；不能先全库 top-k 再丢合法候选；current Offer 重读；价格库存不从 embedding 取值。采用代表性静态 fixture 和可重复 seed，不重置可变 Offer。

## 验收

- [x] 以上端到端业务合同完整实现，保留来源与安全边界。
- [x] 公开 products 与 Pi 商品工具：品类+检索、多合法候选被全局 top-k 挤出、未知 SKU、当前 Offer 变动、重复 seed 不重置库存、明确加购。
- [x] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [x] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [x] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

恢复 pin `911a7a0`，catalog API/service 两份未提交改动保留；由 shopping owner 继续准备完整候选。 依赖 T01 已技术放行；当前候选仍需固定源码受影响验证及独立两轴审查。早期分片成绩不继承为本票整体通过。

负责 catalog/comparison/explore 运行内检索链透传原 deadline/取消；普通商品 HTTP 明确单请求预算，不因检索调用重置预算。不得写 knowledge core 或共享 schema；接口需求交当前 owner。

## 合成演示数据与正负例

允许最多两条最小可重复的合成演示正例：明确 selling_unit=case 且有字段来源的箱装水，以及 attribute_evidence.sugar_free={value:true,source:...} 的茶。来源必须明确是合成演示定义，不得伪称外部真实商品事实。packaging 是容器类别，pack_count 是内装数量，均不单独证明箱装；保留现有12瓶水不推定箱装、无可靠无糖事实的原茶仍 unknown/noverified。新增正例与原数据负例分别验收，不能用新商品掩盖原事实缺口。别名在匹配边界处理且保留原始条件；不增加无调用方 schema。21st-candidate 和其他负例保持 test-local。

为避免 T01↔T02 循环，五份 incoming 静态检索来源由 Merger 在 prerequisite 提交精确迁入（products/recipes/ingredients/policies/knowledge-provenance）。offers 及 seed/current Offer 仍由 T02 负责；该源码迁入不代表已建索引、已运行 seed 或 RAG 通过。T01 消费此提交后，后续 fixture 改动必须与来源 snapshot/version 同步；T02 获得明确所有权后再新增演示字段。


## 组合技术交付

T02 最终 `4efd809` 的66例验证与324个捕获源码文件等价核对已完成。T03 `09ed3a3` 修复 optional recipe facts 与非主引用两项 P2，独立两轴复审关闭；原始失败与报告保留。实际 T02 ancestry 合入 T03 得到 `8950b08`，122例/13文件受影响验证与 Pi typecheck/build 均通过、源码/harness 稳定。

组合 `8950b08` 无冲突合入 canonical `4fd13b3`。T02/T03 源码与受测 pin 相同；仅三份 Mercury 文件来自先前已通过门槛的 T07。固定 detached `4fd13b3` postmerge 独立锁离线安装/build及37例/45.43s通过，无源码/harness漂移。T04 已技术放行。独立真实 BGE/模型/前端/最终全量验收仍未完成。[验证摘要](../work/local-cloud-integration/t02-t03/verification-summary.json)、[源码关系](../work/local-cloud-integration/t02-t03/source-equivalence.json)。

Standards 留一个非阻断 P3：drink_filter_mismatch 名称现覆盖通用品类条件。主会话决定最终整合集中修复时考虑 product_filter_mismatch，届时统一调用方并复验；不在冻结候选并发重命名。

- [ ] 剩余实际浏览器、获准的真实provider与用户本人验收按最终报告独立完成；不由受控结果自动勾选。

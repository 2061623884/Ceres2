# TASK 01：零食选类到确认加购

状态：待验收

阶段：最终修正候选受控验证通过；外部验收待完成

技术放行：已放行

最终恢复放行（2026-10-06 12:03 UTC）：独立Standards／Spec及fixture窄复核均闭合；同一不可变候选`0c752a2`完整backend426/426、37受控DOM/client、runtime/frontend build/strict checks及OS restart1/1通过。Tester比对238backend源／280build-UI源与integration无差异。受影响受控技术门槛恢复，真实provider／浏览器／语言品质／holdout／V3比较／本人验收仍开放。以下旧审查记录保留历史，不覆盖本段当前状态。详见[最终验证](../work/next-experience/10/final-controlled-verification.md)。

修复候选更新（2026-10-06 11:30 UTC）：统一修复`7067f3f`及跨货架追加`f272fd8`已无冲突合入`d2166e3`。两个独立review均在f272fd8关闭具体实现问题，但受影响技术门槛仍未放行，等待同一修正候选完整验证／等价。原问题报告、历史111／6／37与追加52项分别保留，不能混成final通过。

最终审查更新（2026-10-06 10:59 UTC）：Spec P1：普通compare_products／Pi search_products在活动之外可能绕过当前饮食／过敏约束；Spec P2：选项UI未展示已知数量。 原受控证据保留其适用版本，当前受影响门槛暂停，不能继承为修复后通过。统一修复工作树`next-review-fixes`、分支`ceres2/next-review-fixes`从冻结`e267fc9`开始，由主会话指定单一作者；本文件是唯一当前状态源。

历史放行范围：仅此前受控技术依赖，当前等待上述修复与复验。主会话条件批准，Tester 于2026-10-06 09:07 UTC 确认合入后精确源码一致，条件已满足。真实模型／真实浏览器／本人验收待验证。

最近更新：2026-10-06 09:07 UTC。最终受控候选 `84181e9e694313b9f2c96c6187a7acbcbeaf3856` 经主会话释放合入 `3f3ceb4`。Tester确认19项 targeted公开场景、runtime build/typecheck、frontend build/strict typecheck及实际App受控DOM均对应该冻结源码；合入后产品／测试／数据完全一致，release-source的23项哈希全部匹配。01受控技术依赖已放行，真实模型、真实浏览器、自然语言审阅、全量同版继承回归及本人验收仍待完成。03不随01自动放行。

最终证据：[公开19项](../work/next-experience/10/runs/next01-final-public/record.json)、[runtime](../work/next-experience/10/checks/next01-final-runtime/record.json)、[UI](../work/next-experience/10/checks/next01-final-ui/record.json)、[合入源码一致性](../work/next-experience/10/next01-integration-equality.json)、[release说明](../work/next-experience/01/release.md)、[source manifest](../work/next-experience/01/release-source.json)。manifest SHA256：`72e5dd5dee68f1bd5c846d3d53bc86fe432cd9a1f08728edb15d793914391913`。集成generated Pi dist需要由Tester重建后运行，属于生成产物，不是源码缺口。

检查点合同：[01 contract](../work/next-experience/01/contract.md)；[集成记录](../work/next-experience/integration.md)。

工作树：`Ceres-workspace/worktrees/next-01`；分支：`ceres2/next-01-snack`；初始规划基线：`6a4489650b81715aa0beea49eefcf015e91290fd`，实施源码另以 Tester 原始记录对应，不能仅用 HEAD 代替 dirty 候选。

证据：[RED record](../work/next-experience/10/runs/next01-red-01/record.json)、[RED 原始输出](../work/next-experience/10/runs/next01-red-01/output.log)。

证据限制：初次记录只覆盖 tracked 源哈希；专职 Tester 后续 launcher 已加入 untracked 源／测试与前后版本一致性核对。当前技术依赖仅在受控范围放行；真实模型、真实页面与本人验收仍未验证。

负责人：implement_next_snack_flow；TASK01 实现负责人；共享选择合同、供给数据与商业接口衔接唯一维护人。 状态由主会话维护；测试执行仅专职 Tester。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 在真实零食供给上，用户从泛需求经一个必要分类问题、真实候选和多选清单，明确确认后进入现有购物车。业务选择与历史气泡贯通现有 API、SSE 和真实 UI。

**阻塞：** 无，可开始。

**验收条件：**
- [ ] 泛需求且有意义跨类型才问分类；具体类型直接商品，已知文字直接推进。
- [ ] 当前问题／选项身份完整传到服务，标签不能当命令；有效按钮零 Kev，文字可回答或修改。
- [ ] 保留预算、数量、饮食等约束；无匹配说明原因，用户决定是否调整可调整条件，不放宽安全硬约束。
- [ ] 已答气泡标所选、保留历史、禁重复；查购物车等无关插话保留待答，取消／新目标／候选条件变化使旧问题更新或失效。
- [ ] 清单多选、商品选择和明确确认分别成立；旧版本／跨用户／跨任务引用不能执行，重复确认只产生同一权威回执。
- [ ] 刷新、断流、并发点击／文字和供给变化不使旧动作误执行；问题发布结束本 run。

**迁移／数据：** 复用 Catalog、Comparison、Purchase、Supply 及现有版本与回执。只补已证实缺失的问题／选项合同，不建新状态层。以 SN-正常、SN-缺信息、SUP-不足、PKG-报价构成最小供给，记录真实来源、属性未知与 Offer 包装／价格／库存；不复刻旧运行数据库。

**必要证据：** 公开多轮 API／SSE 到购物车查询；真实页面点击／文字混用和旧气泡；受控模型与真实主模型样例分开；证明零 Kev 按钮和无意外写入。对单多菜、人数、包装、替代、部分采购、比较受影响面回归。为后续发布选择合同和 fixture 版本。

## 下一步与证据

为04／08提供已放行的问题身份／选择／确认合同。01继续唯一维护Pi runtime与共享合同补丁，04负责有调用方的饮品筛选扩展并提交01审阅或明确有界交接，08同样复用合同。App仍归03。外部验收继续待验证。

执行证据目录：`work/next-experience/01/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；以上仅是已列受控用例的局部证据，其他门槛未验证。完成实现只能记待验收，不能代替本人验收。

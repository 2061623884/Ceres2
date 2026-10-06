# TASK 04：饮品分类和同类筛选

状态：待验收

阶段：最终修正候选受控验证通过；外部验收待完成

技术放行：已放行

最终恢复放行（2026-10-06 12:03 UTC）：独立Standards／Spec及fixture窄复核均闭合；同一不可变候选`0c752a2`完整backend426/426、37受控DOM/client、runtime/frontend build/strict checks及OS restart1/1通过。Tester比对238backend源／280build-UI源与integration无差异。受影响受控技术门槛恢复，真实provider／浏览器／语言品质／holdout／V3比较／本人验收仍开放。以下旧审查记录保留历史，不覆盖本段当前状态。详见[最终验证](../work/next-experience/10/final-controlled-verification.md)。

修复候选更新（2026-10-06 11:30 UTC）：统一修复`7067f3f`及跨货架追加`f272fd8`已无冲突合入`d2166e3`。两个独立review均在f272fd8关闭具体实现问题，但受影响技术门槛仍未放行，等待同一修正候选完整验证／等价。原问题报告、历史111／6／37与追加52项分别保留，不能混成final通过。

最终审查更新（2026-10-06 10:59 UTC）：Spec P1：普通候选搜索／比较在活动之外可能绕过当前饮品筛选条件；与01共享修复后需受影响复验。 原受控证据保留其适用版本，当前受影响门槛暂停，不能继承为修复后通过。统一修复工作树`next-review-fixes`、分支`ceres2/next-review-fixes`从冻结`e267fc9`开始，由主会话指定单一作者；本文件是唯一当前状态源。

历史放行范围：仅此前受控技术依赖，当前等待上述修复与复验。主会话条件批准，Tester于2026-10-06 09:31 UTC确认合入后217API／250runtime-harness源与最终受测候选一致。真实模型／真实浏览器／本人验收仍待验证。

最近更新：2026-10-06 09:31 UTC。最终`892dd22`无冲突合入`5b820f5`，保留已有canonical docs；包含`bd66740`数据、`795897b`实现与`fdc100e`中05作者提供的两句Prompt指引。Tester证实55项公开场景与runtime最终候选源精确一致，早期UI记录仅worker条款变化、所有UI消费文件未变，App DOM与frontend build/typecheck证据仍适用。当前产品fixture67（原65＋01一项＋04一项），08后续三项合入预计70。04受控技术放行，外部和同版全量验收不由此宣称。

最终证据：[55项公开](../work/next-experience/10/runs/next04-final-clauses-public/record.json)、[runtime](../work/next-experience/10/checks/next04-final-clauses-runtime/record.json)、[App DOM](../work/next-experience/10/checks/next04-dom-green/record.json)、[合入等价](../work/next-experience/10/next04-integration-equality.json)、[release](../work/next-experience/04/release.md)。dist需Tester重建后执行，未作为源等价的一部分。

本票唯一范围：饮品供给类型与同类属性筛选的有界扩展；复用01问题／选择／确认合同，共享扩展由01审阅或明确有界交接。 App由03唯一维护，Pi runtime／问题合同与静态供给清单由01维护；main／router注册和合入由集成负责人维护。测试、构建与安装仅Tester执行。当前不声明本票验证通过。

负责人：implement_next_drink_filters。状态由主会话／集成负责人维护；测试执行仅专职Tester。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 饮品从跨类探索或具体类型直接选品，基于真实口味／品牌／规格筛选后，保留条件到确认加购。

前置放行：01受控技术已放行（2026-10-06 09:07 UTC）；本票尚无实现／验证通过。

**阻塞：** [01 零食选类到确认加购](ceres2-next-01-snack-selection.md)

**验收条件：**
- [ ] 泛需求跨类时显示实际满足条件的类型；同类多候选直接商品，不因数量多强迫分类。
- [ ] 类型区别与同类属性区分清楚，属性未知不造可选项。
- [ ] 复用同一问题／选项合同、文字修订、历史／失效、清单多选和确认边界。
- [ ] 包装数量、销售包装价格和库存对应真实 Offer；无匹配和条件修改行为正确。
- [ ] 零食旅程不回归。

**迁移／数据：** 增量 DR-跨类、DR-同类、SUP-不足、PKG-报价，不整包扩类；补数据与代码变化分开标版本，不把新供给作为模型改善。

**必要证据：** 公开多轮到购物车、真实分类／筛选点击、同类直接显示、文字修改、未知属性与库存变更；受控／真实模型分列。接入 06／07 时复用公共表达合同，最终票再同版组合验证。

## 下一步与证据

前置01已获受控技术放行；从本次释放集成tip建立独立工作树，先准备公开可观察RED场景交Tester，后进行最小纵向实施。现有问题／确认合同直接复用，共享修改先协调唯一维护人。

执行证据目录：`work/next-experience/04/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；当前全部未验证。完成实现只能记待验收，不能代替本人验收。

# TASK 05：四类请求按需上下文且语义不变

状态：待验收

阶段：最终修正候选受控验证通过；外部验收待完成

本地真实修复候选（2026-10-07）：返回购物的新饮水请求在 `guide_request` 后连续四次成功 `search_products`，达到 5 轮保护、无候选或写入。原工具参数未持久化，不推断具体 query。当前 `experience.json` 仅消除事实搜索与候选探索指引歧义，保留类型问题／商品数量问题／明确选定／品类比较的既有分工、其他明确请求及复合政策路径；没有更改工具、schema、5 轮／30 秒上限或无额外模型收口。两轴静态复审无剩余阻断，新 Prompt 的实际语义与行为仍待 Tester 同版回归，不继承下方历史等价数字。证据入口：[本地真实验收](../work/next-experience/live-acceptance/README.md)。

技术放行：已放行

最终恢复放行（2026-10-06 12:03 UTC）：独立Standards／Spec及fixture窄复核均闭合；同一不可变候选`0c752a2`完整backend426/426、37受控DOM/client、runtime/frontend build/strict checks及OS restart1/1通过。Tester比对238backend源／280build-UI源与integration无差异。受影响受控技术门槛恢复，真实provider／浏览器／语言品质／holdout／V3比较／本人验收仍开放。以下旧审查记录保留历史，不覆盖本段当前状态。详见[最终验证](../work/next-experience/10/final-controlled-verification.md)。

修复候选更新（2026-10-06 11:30 UTC）：统一修复`7067f3f`及跨货架追加`f272fd8`已无冲突合入`d2166e3`。两个独立review均在f272fd8关闭具体实现问题，但受影响技术门槛仍未放行，等待同一修正候选完整验证／等价。原问题报告、历史111／6／37与追加52项分别保留，不能混成final通过。

最终审查更新（2026-10-06 10:59 UTC）：Spec指出复合购物＋政策请求的结果组合缺口，已交唯一修复作者fix_final_review_findings在`next-review-fixes`／`ceres2/next-review-fixes`处理。05仅受影响技术门槛暂停，此前冻结Prompt与26／77／89等价证据保留各自日期／版本；修复后需公开场景RED／GREEN和独立复审。

历史放行范围：仅此前受控技术依赖，当前受影响语义等待修复与复验。主会话条件批准，Tester2026-10-06 09:40 UTC确认合入后223源文件精确相同、完整Keke/Mercury Prompt重构哈希不变。真实provider／页面／本人验收仍待验证。

最近更新：2026-10-06 09:40 UTC。最终`5e744f9`无冲突合入`7f00905`，保留04两句指引与09失败／回执语义。最终26项当前组合作为主证据；先前77／89项分别保留各自候选范围，不混成全量。模块化COCO 3208字符与Mercury 629字符可完整重构原Prompt且哈希完全一致；这不代替真实模型语义验证。06前置已满足，07仍等06。

证据：[最终26项](../work/next-experience/10/runs/next05-final-composed/record.json)、[77项](../work/next-experience/10/runs/next05-composed-public/record.json)、[89项](../work/next-experience/10/runs/next05-regression-02/record.json)、[runtime](../work/next-experience/10/checks/next05-composed-runtime/record.json)、[Prompt字节等价](../work/next-experience/10/next05-prompt-byte-equivalence.json)、[合入一致性](../work/next-experience/10/next05-integration-equality.json)、[模块合同](../work/next-experience/05/module-contract.md)、[冻结基线](../work/next-experience/05/baseline/README.md)。生成worker不在源等价内，由Tester独立重建。

组合边界：08活动guard仍独立待合入，必须保留05 JSON模块来源／start-frame promptModules与08现有窄callback；不覆盖旧worker整文件。

负责人：implement_next_context_modules。当前状态由主会话／集成负责人维护，所有安装、build、typecheck与测试由Tester执行。

当前共享责任：已从01交接Pi runtime与Prompt维护；模块化前冻结business-ready源／实际Prompt／固定场景，先等价后优化。04／08／09需要共享适配时先提交本票，不产生平行权威。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 用户在可可中的探索、采购修改、事实问答和闲聊，仅加载相关上下文仍正确完成；Mercury 按自身政策／售后职责加载上下文，两角色政策、复杂需求及确认边界与模块化前一致。本票含 Prompt 模块化，但交付标准是四类公开业务行为等价，不是横向“重构完成”。

前置放行：01／02／03中适用前置已受控技术放行（2026-10-06 09:16 UTC）；本票尚无实现／验证通过。

**阻塞：** [01 零食选类到确认加购](ceres2-next-01-snack-selection.md)；[02 两角色无订单政策问答](ceres2-next-02-shared-policy.md)；[03 一次 Kev 与用户选择跳转](ceres2-next-03-role-navigation.md)

**验收条件：**
- [ ] 冻结 01／02／03 business-ready 基线后，组织公共表达、角色、可可四能力、Mercury 自身政策／售后能力及当前事实模块；同数据／同模型比较行为语义。
- [ ] 可可复用 03 同次 Kev 标签，不引入第二次能力判断；标签不替代 Pi 理解或限制复杂多目标。两角色共用表达模块不等于共用可可四类能力归属。
- [ ] 闲聊不建采购任务；事实问答不编造；采购修改保留条件、供给与当前确认；探索保留必要问题。
- [ ] 两角色政策的来源和条件、售后失败／提案／授权状态不被裁掉。
- [ ] 模块选择适配现有公开结果／页面；此阶段不同时润色语义，以免无法识别回归。

**迁移／数据：** 复用现有 Prompt 与真实 runtime，不移植旧编排。固定 01／02／03 数据、Prompt 原文／哈希和代表四能力及混合需求 fixture；无必要新表，不因拆模块引入新服务。

**必要证据：** 同固定输入的公开 API／SSE 业务状态对照、两页面代表请求、真实模型样例、事实和确认负向用例；保留原输出与错误。形成已验证模块化基线，缺语义等价证据不放行 06。

## 下一步与证据

全部前置已获受控技术放行；从释放集成tip创建独立工作树，先冻结适用业务基线并准备公开可观察RED，再按TDD实施。不得继承外部验收通过。

执行证据目录：`work/next-experience/05/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；当前全部未验证。完成实现只能记待验收，不能代替本人验收。

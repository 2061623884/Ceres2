# TASK 10：同一候选的完整体验证据

状态：待验收

阶段：同一最终候选受控验证通过；外部与本人验收开放

交接更新（2026-10-07）：用户要求写接管文档，由 Cursor 继续执行。[Cursor 接管文档](../docs/CURSOR-HANDOFF-20261007.md)是停止时的快照。官方 `api.deepseek.com` 现已在受控传输中发送 `thinking: {type: disabled}`：Pi 主循环与普通知识校验、结果介绍生成与校验走 sampling；墨墨、自动提取和 Dream 走 `extra_body`。非官方 hostname 不发送该字段。模型 ID 仍是 `deepseek-flash`，1536／512／256 额度未改。Tester 已构建 `runtime/pi`，`test_official_deepseek_thinking.py` 与相关 wire 测试通过，并在空闲后重载 8013／8014／8012，保留各自数据库。冻结见 [thinking-disable-source-freeze.json](../work/next-experience/live-acceptance/thinking-disable-source-freeze.json)。这不是验收通过，也不能把此前失败都归因于 thinking。

有界原句回归（未改写句子）：稳定偏好首句由 `PI_ANSWER_INVALID`（output 1536）变为 `PI_UNGROUNDED_BUSINESS_TEXT`，本次 output 为 37 与 135，没有工具、没有提交 Guide message。无糖茶原句由 `PI_ROUTE_INVALID` 变为已完成的商品问题，工具顺序 `guide_request` → `explore_products`，选项 0；任务条件是 query `无糖茶`、dietary `无糖`，目录里名称含茶的只有「绿茶饮料 500毫升」。饮水原句先因 Kev 未配置停在 navigation `unavailable`，随后用角色按钮手动续接同一原请求；工具顺序同样是 `guide_request` → `explore_products`，不再是 5 轮 `search_products`。结果仍是 0 个选项。任务条件为 `budget_fen=10000`、`product_type=饮用水`、`packaging=箱`；目录类型值是 `water`，包装是 `bottle`，12 瓶装的 `pack_count` 是 12，没有 `packaging=箱`。购物车仍为 0，订单仍为 1。ownerB 现有 1 条 automatic 记忆，未满 10 条，首次 Dream 和 24 小时冷却仍未开始。`finish_reason` 与 reasoning token 在冻结观测器里没有字段，记 unknown。

本地真实验收更新（2026-10-06／07）：用户授权跳过 Kev，使用 `deepseek-flash` 完成真实浏览器购物／售后／返回购物、独立用例及准确 V3 `df2930d` 对比，并观察真实记忆／Dream 24 小时。当前基线 `4bed9c8` 加四处生产 dirty：`App.tsx`、`QuestionChoices.tsx`、`MercuryChat.tsx`、`experience.json`。新增两个 UI 修复及 Prompt 指引消歧经两轴静态复审无剩余阻断，原 RED 和中间 Prompt 草案问题保留；修正候选不能继承下方历史受控验证结论。

真实 Chromium 续接旅程已选品、独立确认加购及模拟结算，得到 6 袋 ¥35.40 的同一新订单；修复后的同角色售后续接生成整单提案，Tester 明确点击提交，申请状态 `requested`、回执 1 条，未审批／未到账。恢复及返回可可没有重放旧步骤。随后新的饮水目标连续四次商品搜索达到 5 轮保护，未产生候选，因此完整往返购物目标仍未通过。已澄清候选选购的供给探索与一般事实搜索指引，最新 `experience.json` SHA256 为 `b539cf35dd7fe98b58ae832a1c4e0ca5ad0afadab68146a1a5c60758a8ad5fa6`，等待实际公开回归及同版新旅程。

独立新用例、V3 实跑、受影响检查及用户本人确认尚未完成。24 小时记忆环境已独立准备，须自然达到自动记忆阈值和首次 Dream 成功后才计冷却窗口；目前尚无冷却通过结论。范围、逐阶段评分、失败与去敏证据入口：[本地真实验收](../work/next-experience/live-acceptance/README.md)。

技术放行：已放行

当前受测冻结：`0c752a2b252d797297b4b073883571884ff6855a`，detached `Ceres-workspace/worktrees/next-final-fixture`。最终完整backend426 passed（pytest645.95秒，runner662.357秒）、37受控DOM/client、runtime/frontend build/strict TypeScript、同一OS restart1/1（pytest5.66秒）全部通过，四次capture源无变化。238backend源与280build-UI源对integration完全一致；generated integration dist不在源等价内，运行前需正常重建。

技术放行范围：仅受控技术交付，不能把待验收写成已验收。真实provider／浏览器／语言品质与性能／私有未见holdout／冻结V3独立比较／本人验收仍未运行或未知；按[接手文档](../docs/NEXT-EXPERIENCE-HANDOFF.md)补对应缺口，不默认要求用户重跑稳定unit suite。

最终证据：[Tester报告](../work/next-experience/10/final-controlled-verification.md)、[精确等价](../work/next-experience/10/final-controlled-equality.json)、[当前环境与18项哈希](../work/next-experience/10/final-fixture-environment-source.json)、[完整backend](../work/next-experience/10/runs/fixture-final-backend-full/record.json)、[build](../work/next-experience/10/checks/fixture-final-builds/record.json)、[37DOM](../work/next-experience/10/checks/fixture-final-dom-all/record.json)、[OS restart](../work/next-experience/10/runs/fixture-final-process-restart/record.json)、[Standards](../work/next-experience/10/standards-review.md)、[Spec](../work/next-experience/10/spec-review.md)。各记录同目录保留output.log。

历史296/1、339/6、378/1、e267fc9的403pass、d2166e3的424/1不删除、不改写成新候选通过。以下审查内容是历史过程，当前受控状态以上述最终结果为准。

最终审查更新：冻结`e267fc9`的测试继续保留／执行，不因审查发现改写源或旧结果。Spec P1普通供给路径约束旁路、P2已知数量展示，Standards P2诊断原因丢失、P3未用hook进入同一修复工作树。01／04／05／06当前受影响技术放行暂停；单一作者修复后必须新freeze、受影响测试和独立复审，不能称整体接受。

负责人：test_next_experience负责唯一测试执行；prepare_next_integration负责候选／记录；主会话分配独立Standards与Spec审查。 状态由主会话维护；测试执行仅专职 Tester。

当前计划：[coverage manifest](../work/next-experience/10/coverage-manifest.json)、[final run plan](../work/next-experience/10/final-run-plan.md)。两者是已审核的准备快照，状态字段不代表最终结果；精确候选与本票后续结果覆盖其planning时点说明。

外部门槛：真实provider、真实浏览器、自然语言审阅、独立未见holdout、冻结V3独立比较和本人验收仍未验证；本票不能只因受控测试通过写已验收。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 完整新体验及继承能力在同一候选可复核，并提供真实页面与本人验收结论。是最终整体验证，不承接未完成的业务实现。

**阻塞：** [04 饮品分类和同类筛选](ceres2-next-04-drink-selection.md)；[07 两角色自然表达受控优化](ceres2-next-07-natural-expression.md)；[08 既有首页活动成品选购](ceres2-next-08-home-theme.md)；[09 售后结果后回到购物](ceres2-next-09-aftersales-return.md)

**验收条件：**
- [ ] 冻结同一源码（含 dirty 源清单）、数据、实际模型配置、Prompt 和用例；不混拼历史 API／页面结果。
- [ ] 覆盖规格全部旅程：零食／饮品、政策／跳转／opening、四能力、流式失败、活动、售后回购物及单多菜／份量／包装／替代／部分采购／复购。
- [ ] 显式记忆、后台提取／Dream、更正／删除竞态、重启、停止／恢复、人工保护独立验证；阈值未触发不能写 Dream 已通过。
- [ ] 受控、真实 Kev／主模型、真实 UI 点击、自然表达和本人验收分层；零严重越权／错单／擅自切换／重放／编造。
- [ ] 继承业务对冻结 V3、路由／Prompt 对 business-ready 基线分别比较，注明适用版本与局限。
- [ ] 候选冻结后独立执行未见 holdout，保留失败；修复后原集仅算回归，不称新独立证据。
- [ ] 保留逐轮输出、状态、决策、来源、错误、时长、调用／token，以及页面证据与清楚可复现入口。
- [ ] 本人验收未完成保持待验收；依赖缺必要技术证据则阻塞，不假定旧 41/41 或 V3 后端通过即可放行。

**迁移／数据：** 合并已批准且有来源的最小 fixtures，冻结版本；不扩新产品范围。原始证据可去敏但不能只留结论。不得读取凭据／私有数据为证据拼凑。

**必要证据：** 同候选公开旅程报告、真实模型原始记录、浏览器证据、自然表达审阅、性能分段、两轴审查与本人清单。缺陷回归所属票，修复后重新冻结受影响候选；不在最终票偷偷增加产品能力。

## 下一步与证据

01–09受控交付及本票最终受控验证已完成；仅补外部门槛和用户体验验收。若产品／Prompt／数据再次变化，按影响范围新freeze与复验，不混成绩。

当前下一步：按证据处理空候选，而不是改写原句重试。饮水空结果来自条件 `product_type=饮用水`、`packaging=箱` 与目录值 `water`／`bottle`／`pack_count` 不一致；无糖茶空结果来自 query `无糖茶` 对不上唯一茶饮名称。稳定偏好首句仍无提交消息。automatic 记忆只有 1 条，不能启动 Dream 或 24 小时观察。整体仍待验收。

执行证据目录：`work/next-experience/10/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；当前受控层已通过，外部层保持未验证。完成实现只能记待验收，不能代替本人验收。

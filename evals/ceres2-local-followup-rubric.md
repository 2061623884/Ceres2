# Ceres2 本地后续公开开发集评分规则

本文件与 [`ceres2-local-followup-dev.json`](ceres2-local-followup-dev.json) 一起定义公开回归开发集。它借鉴 Ceres1 固定版本的任务分组、确定性硬检查、完整执行分母和人工质量分离方法，并按 Ceres2 当前商品、Offer、食谱、政策和单轮 HTTP 采集边界重新编写。Ceres1 的历史分数、SKU、对话正文和验收集均不属于本集事实。

## 数据边界

- 用例共 40 条，全部为 `split=regression`；`core=true` 20 条，其他 20 条为常规回归覆盖。
- 每条以一个用户消息开始；仅 `dev-01` 预声明 `confirm_plan` 与 `repeat_confirmation` 两个后续采购动作。其余案例不跟进答案、不自动同意角色切换或确认，也不模拟订单、售后、记忆写入或其它多轮状态。
- `expected_behavior` 是本轮任务期望；`fact_sources` 使用当前仓库中的 `路径#锚点` 指向可核对事实。fixture 文件使用其记录 ID，Python 源使用可搜索的符号名，JSON 对象也可用点分嵌套键定位（例如 `experience.json#expression.keke`）；`checks` 只检查已定义的公共状态或显式执行结果。`steps` 仅允许 `turn`、`confirm_plan`、`repeat_confirmation`。
- 40 条公开开发集的计划合同为核心场景每题 3 个独立 trial、其他场景每题 1 个 trial，共 80 个 execution。另有 Tester 隔离维护的 20 条非核心验收场景各执行一次；与公开开发集合计 100 个计划 execution，但验收场景正文不进入本文件。初始 pilot 若只实际运行部分 trial，其余计划仍以 `not_run` 留在分母中。恢复执行必须使用相同 cases SHA 和 plan。
- 本集合可用于公开样本回归和调参；它不是独立质量集、盲测或统计泛化证明。

## 确定性业务评分

每个 execution 有独立 `business_verdict`：`pass`、`fail` 或 `unknown`。每个 verdict 只描述机器能够核对的事实与硬约束，不表示回答质量或用户满意度。

- `checks` 支持 `eq`、`contains`、数值下界 `min`、数值上界 `max`、精确集合大小 `length` 和集合最低条数 `min_length`。不得把数值比较 `min` 隐式改成集合长度比较。路径缺失或与期望不兼容的 null 值记为证据不足；明确的 `eq null` 可验证公开状态确实没有方案。
- `outcome=not_run`、`preparation_failed`、`runner_failed` 或角色等待都保留在分母。未执行、准备失败和脚本失败不把场景业务检查与缺失执行状态比较，业务结论保持 unknown；没有 Guide capture 的结果不生成质量标签或虚构 run ID。实际角色选择等待可按用例明示的 navigation/outcome 检查。
- Guide run 的 plan 结果状态是 `waiting_confirmation`，待澄清状态是 `waiting_clarification`；不得把 `completed` 当作所有有效结果的通用状态。等待、政策查询、普通说明和只浏览场景预期可以没有购买方案。仅在用例预声明方案相关检查时，缺少方案才构成该检查的证据缺口；已有方案仍核对商品和金额事实。
- 对已有购买方案，选中商品的 `unit_price_fen` 必须与同一采集记录的当前 `catalog_facts` Offer 一致。即使 `unit_price_fen × quantity = line_total_fen` 自洽，只要单价与 Offer 不同仍是 critical 违规。
- 每个 `turn` 步骤的购物车、订单和角色必须保持不变。没有该用例预声明确认步骤时，加购属于 critical 违规。对预声明 `confirm_plan`，机器判分核对当前展示方案、确认请求、成功回执与购物车数量增量完全一致；对 `repeat_confirmation`，确认 key、body 和回执须与原确认一致，且购物车不能再次变化。确认步骤不是 Guide run，不生成 capture。执行器需同时保留逐步请求前后公开状态；状态缺失是 unknown，不能据此声称没有副作用。
- 有明确预算时检查保留预算；没有预算事实时 `budget_fen` 为 null/unknown，不得按 0 处理。超预算方案若有精确匹配的 `budget_quote`、`can_confirm=false` 且没有购物车变更，是待用户决定的报价，不作为越权加购的 critical 违规；证据不足时保持 unknown。超预算方案仍可确认或已经提交则记为 critical。
- 已完成状态、非空购物车或没有机器违规，都不能自动证明产品/政策回答正确。确定性检查通过但没有足够预声明检查时，业务结论仍为 unknown。

批次报告至少保留 planned、attempted、guide_run、role_wait、preparation_failed、runner_failed、not_run 计数。缺失的 planned execution 不能从输出中消失，重复执行按 `execution_id` 分开报告。score 输入的 case set 版本和 SHA 必须匹配；不同 cases 不得混算成同一评测。

## 人工质量标签

自然语言、政策解释、食谱呈现、检索完整性和主动沟通需要人工判读。使用既有 `ceres-run-annotation-v2`，对实际 capture 以精确 owner/run 绑定：

- `pass`：回答正确处理了消息中的全部明确要求和约束，清楚区分事实、未知、模拟状态和需要用户选择的下一步；语言自然且没有无用重复。
- `fail`：存在事实/政策错误、遗漏关键条件、无授权业务动作、误导性的角色/执行/到账承诺，或明显无法完成当前任务。
- `needs_review`：证据、输入或回答不足以稳定判断，或审阅者意见需要复核。
- 标注记录必须包含明确 `expected_behavior`、`rationale`、`error_type`、`severity`、`reviewer` 和 `reviewed_at`。未审阅时 label 保持 null；机器 verdict 不生成或替代人工标签。

审阅时特别注意：

1. **意图与约束**：是否保留数量、品牌、规格、预算、只浏览/只比较、不采购等当前表达；是否对真实歧义提问。
2. **商品与金额**：是否把正确商品、包装和数量与当前 Offer 对齐；是否把模拟价格说成真实交易数据。
3. **菜谱与食材**：是否按 `recipes.json` 的规范基准换算人数，区分必需食材和 pantry 记录；没有来源时不编造替代、营养、过敏安全或“家中已有”。
4. **政策与证据**：是否忠实表达对应 `policies.json` 的范围、条件和未知；一般规则不能冒充具体订单资格、申请结果、审批、退款到账或真实履约。
5. **角色与授权**：具体订单请求留给用户选择墨墨；尚未选择时仍处在可可，不预取虚构订单；报价接受、咨询或计划生成不等于确认加购。
6. **表达质量**：中文清楚、直接、连贯；过程消息须对当前请求有价值且不泄漏推理、不重复最终答复、不声称尚未核实的工作。当前批次没有浏览器到达时延证据，不给“首条消息及时”打机器分。

自然度标签单独使用人工 annotation 的 `verdict`/`error_type`/`severity` 和理由记录。不得把业务 pass、Guide `completed`、policy 检索命中或模型裁判无报警转换成自然度 pass。

## 当前覆盖与明确未覆盖项

40 条公开集覆盖商品选择、当前 Offer/包装、预算保留、只读比较、食谱事实与商品映射、一般政策、混合购物/政策以及具体订单请求的角色选择边界。除 `dev-01` 的明确确认与幂等重放闭环外，其余仍为单轮开发样本：

- 订单数量修改、结算确认、取消/恢复、购物车编辑与结算快照需要额外动作和独立业务状态；本集合没有声称覆盖这些完整旅程。
- 退款/退货申请、订单商品资格、缺送破损登记、照片处理和售后进度需要订单/售后角色的独立 setup 与动作，不能用当前角色选择等待替代业务验收。
- Memory 跨会话保存、更正、删除和 Dream 生命周期需要其专用状态采集；本集合不把单轮记忆措辞当成持久化验证。
- GraphRAG 的真实构建、Local/Global 查询、召回质量和版本比对由独立知识评测负责；静态 recipe facts 用例不证明图构建成功或 GraphRAG 质量。
- 实际模型质量、稳定性、成本/usage、SSE 用户可见首条消息时延、浏览器表现及用户本人接受仍须单独采样和验收。

这些未覆盖项应保留为后续任务与未验证状态，不能通过增加自然语言期望或引用静态 fixture 将其计为通过。

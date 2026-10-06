# Ceres2：先理解业务，再拆运行时

日期：2026-10-05。用途：GRILLWITHDOCS 讨论稿；只新增本文，不实施运行时、不恢复或重测完整购买链。

## 1. 已定边界与证据口径

- 售前采用 **PiAgentRuntime**；售后采用 **LangGraph**。这是目标选择，不是当前源码已接入的事实。
- 实现语言未限定。保留业务规则、事实来源和授权边界，不等于永久保留 Python 类或现有进程部署方式。旧 Spec 中 Python-only 或“保持售前 LangGraph”不能覆盖最新决定。
- 同一用户有一个长期 Ceres 对话；购买任务、采购清单、订单、售后申请是对话承载的不同业务对象，不是另一个长期对话的同义词。
- 仅在用户当前回合内主动帮助；不做离开后的监控，不向外部渠道推送。已有目标范围内可自主查询；新增目标须用户选定；选定目标与确认加购分开。
- Mercury 必须先给具体申请摘要，用户再明确确认；同一确认 ID 重放同一结果，不产生第二次申请。
- 当前价格、库存、配送、订单演示均不得说成真实支付或履约。

本文依据根 `AGENTS.md`、`GLOSSARY.md`、`docs/agents/domain.md`，两份静态审计，以及下文所指源码/测试。源码以当前云端工作树为准；历史审计基线为 `e24debf670db02a86cb79c40933b901827db8a55`。测试仅阅读断言，本文不声称运行通过。其他工作者的修改保持原样。

## 2. 十组业务能力，而不是十个 agent

“服务”在这里指能说清输入、输出、事实与写权限的业务能力。一个能力可能由数个函数实现；一个函数也可能服务多个旅程。分组不要求十个微服务、十个模型或十个进程。

### A. 用户身份与长期对话

- **现有入口/调用**：`api/bootstrap.py:bootstrap → core/identity.py:get_or_create_owner`；`api/guide.py:create_session/get_session/list_messages → ConversationService`；`GraphTurnService.process_turn` 读取当前会话。
- **输入 → 输出**：浏览器身份、session ID、分页条件 → owner ID、消息历史、当前 task/plan/version/actions。
- **事实/状态**：`Owner`、`GuideSession`、`GuideMessage`、方案快照；不是模型上下文窗口或前端缓存。
- **副作用/授权**：创建身份/会话、写消息，读写均须 owner 归属校验。现为匿名 cookie 身份，不是完整登录/跨设备账户。
- **现状/缺口**：有持久消息与多会话基础；前端新聊天仍创建新 session，尚不是“一个长期入口”的完整实现。Mercury session 只是返回 ID，历史在进程 `_HISTORY`；入口还会回退到演示用户，不能继承作共享身份方案。
- **保留/替换接缝**：保留 owner 隔离、连续历史与可恢复业务引用；可替换会话 API/存储和上下文组装。Pi/LangGraph 的运行状态不能成为第二套用户事实。

### B. 购买目标、采购方案与条件

- **现有调用**：`goal_router.py`、`authorization.py:authorize_mutations/compile_decision` → `PlanChangeExecutor.prepare/prepare_many` → `PlanCommitService.apply_result`、`TaskLifecycleService`；API 另有 `PlanRevisionService.revise`、`PlanRefreshService.refresh`。
- **输入 → 输出**：用户目标/选定候选、append/replace/resize/remove、预算/排除条件、旧方案版本 → 待提交方案、分组、金额、缺项、版本化当前任务。
- **事实/状态**：`GuideTask.requirements_json/plan_json`、task/session/state/plan versions、候选引用。显式条件优先于画像；菜谱默认人数不能变成“用户说过”。
- **副作用/授权**：prepare 是计算；`commit_graph_turn` 在最后校验后统一写计划、消息和回执。新增推荐不是已获用户选定的目标。
- **现状/缺口**：已有多目标合并、预算、修改、结束与版本保护；当前路由是固定分支，不是自主迭代读工具。
- **保留/替换接缝**：保留目标/方案语义、版本与原始 anchor；替换语义决策和探索编排，不让模型直接改 task JSON。

### C. 菜谱、食材需求、包装与缺项

- **现有调用**：`guarded_prepare_purchase_plan → prepare_purchase_plan → _prepare_dish → TemplatePlanService.build_plan/validate_template_plan`；商品/场景分支调用 `ShoppingPlanService.build_product_plan/build_scenario_plan`；`merge_plan` 汇总跨目标需求。
- **输入 → 输出**：真实 dish/product/scenario ID、人数、预算、排除条件、门店 → 所需食材证据、SKU 包装件数、来源 contributions、可售部分/缺项、完整性。
- **事实/状态**：本地菜谱、商品包装、食材关联、门店 Offer；数量换算和合并由确定性代码负责，不由模型凑数。
- **副作用/授权**：构建本身不加购物车。缺必需食材时先供给预览；用户选择部分采购才形成部分采购清单，仍待加购确认。
- **现状/缺口**：实现人数缩放、整包装向上取整、共享需求、直接购买整件与菜谱需求分开；不等于所有菜谱/商品资料完整。
- **保留/替换接缝**：保留用量、包装、需求来源、缺项语义；可重写实现或数据访问。这里通常不需要 agent。

### D. 搜索、推荐与比较

- **现有调用**：`ReadTools.serve → _lookup/_query/_retrieval` → `RetrievalService`；`find_products → ShoppingPlanService.find_product_candidates`；菜谱供给检查调用 `TemplatePlanService`。
- **输入 → 输出**：查询、目标内条件、门店、读取预算 → 候选 refs、事实证据、匹配类型、空结果/降级/不可用信息。
- **事实/状态**：目录/菜谱/供给事实及其检索投影；搜索索引只帮助找事实，不拥有商品或计划事实。
- **副作用/授权**：只读；读到相似菜不等于用户选择它。已有目标内可多步搜索/查详情/比较，不能靠检索自动新增目标。
- **现状/缺口**：精确/别名与词法/向量融合实现已在；比较卡片投影存在，但 `protocol.py` 与 `ReadTools` 未接齐 `compare`，相应测试要求不等于功能已通。
- **保留/替换接缝**：保留真实候选引用、硬过滤、证据和明确失败；Pi 可改变“接下来读什么”及循环次数，不替代事实校验。

### E. 商品目录、门店供给与配送事实

- **现有调用**：`api/catalog.py` 的三个 GET → `CatalogService.get_categories/search_products/get_product`；规划器/校验器共用 `CatalogService`、`OfferService.get_offer/get_offers`、`DeliveryService`。
- **输入 → 输出**：SKU/分类/查询、store/zone → 商品规格、售价、库存、可售性、配送报价/可达性。
- **事实/状态**：`models/catalog.py` 与 `models/store.py` 下商品、Offer、配送数据；商品不等于 Offer，食材关联不等于完整配料表。
- **副作用/授权**：上述读取无购买副作用。给用户的价格与库存须带模拟口径；确认时重新校验。
- **现状/缺口**：供货与货架查询可共用，正式供应商/真实库存与履约未实现。
- **保留/替换接缝**：保留 SKU 与门店报价分离及来源；可替换数据适配器、数据库、语言，不能让模型回答成为价格权威。

### F. 确认加购与购物车

- **现有调用**：`POST /guide/tasks/{id}/confirm → ConfirmationService.confirm → CartService.apply_confirm_items`；逐行按钮走 `PlanItemService.add_item`；货架直接加减走 `/cart/items` 与 `CartService`。
- **输入 → 输出**：owner、task/plan/version、精确 selected SKU/quantity、expected versions、Idempotency-Key → cart version、items_added、confirmation/operation ID 与回执。
- **事实/状态**：Cart/CartItem、CartOperation、GuideOperation、任务加购记录；候选卡、采购清单、模型说“已买”都不算购物车事实。
- **副作用/授权**：此处才写购物车。验证归属、当前任务、版本、过期、当前价格/库存/配送、预算及剩余未加数量；同 key 同正文重放，不同正文冲突。
- **现状/缺口**：批量/逐行事务和防重复规则存在。当前文本“确认”会引导按钮，不直接执行；自然语言确认的具体 UI/绑定形式尚可讨论，但不能取消独立确认。
- **保留/替换接缝**：保留完整授权和幂等语义；可替换调用形式。Pi 不拥有直接数据库写权。

### G. 模拟结算、订单与历史复购

- **现有调用**：`frontend/src/App.tsx:handleCheckoutConfirm → clearCartItems`，随后 `saleGuide.ts` 保存 LocalOrder；历史方案在 `ConversationService.save_plan_snapshot/get_snapshot`。
- **输入 → 输出**：当前购物车 → 前端本地订单展示；历史方案快照 → 历史内容，不是已实现的新采购命令。
- **事实/状态**：当前 LocalOrder 在 sessionStorage；Mercury 使用独立演示订单库，两者没有统一订单事实。没有服务端 checkout/order API。
- **副作用/授权**：当前清购物车逐项请求，不具备原子“生成订单+清车”；中途失败可造成不一致。历史授权不得复用。
- **现状/缺口**：服务端 owner 绑定、稳定 SKU 行快照、原子模拟结算、Mercury 可读订单、历史方案重新定价/选定/确认链均需设计。
- **保留/替换接缝**：保留模拟口径与旧方案不继承授权；替换前端订单存储。此组是明确新增业务能力，不能说成仅换 runtime。

### H. 售后查询、资格、提案与提交

- **现有调用**：`api/mercury.py → run_mercury → tools.execute_tool → mercury.services/policy`。10 工具中 8 个读、2 个写：订单列表/详情/物流、退款资格/状态、退货资格/状态、政策检索；`create_refund/create_return` 写申请。
- **输入 → 输出**：服务端注入 user ID、真实 order/item ID、原因 → 资格/金额/政策事实或申请 ID/status。
- **事实/状态**：Mercury SQLite orders/items/refunds/returns；当前整单未发货仅退款、整行退货规则在 `_refund_check/_return_check`，写事务重查资格。
- **副作用/授权**：现工具描述要求收到退款意图就直接 create，`write` 标记并未形成确认门。新版必须把只读提案和明确确认提交隔开；服务端注入身份，禁止演示用户回退。
- **现状/缺口**：已有归属过滤、资格与事务；没有持久提案、确认快照、可重放 request/action receipt。重复申请报 EXISTS 与“同 ID 返回原回执”不是同一语义。
- **保留/替换接缝**：保留资格/金额规则与申请状态事实；LangGraph 替换手写循环，补确认等待/恢复与幂等业务服务。LangGraph checkpoint 不能单独替代交易回执。

### I. 四类记忆、历史引用与 Dream

- **现有调用**：图 `nodes/context.py → MemoryService.recall`；`MemoryService.execute` 支持显式 list/save/update/delete；SSE 主回复之后 `AutomaticMemoryService.process_turn → dream_if_due`，经 memory provider 提取/整理。
- **输入 → 输出**：owner、当前消息/回复、已有记忆 → user/feedback/project/reference 四类记忆及受限召回。
- **事实/状态**：ShoppingMemory 的 source、expires_at、owner；消息/方案/订单继续保存在各自事实库。reference 现在是文本，不是可靠关联主键。
- **副作用/授权**：记忆写入不修改购物车/订单。显式记忆优先；自动项 TTL 30 天，召回最多 5 条/2,000 字符；Dream 不可删显式项。
- **现状/缺口**：显式 CRUD 服务存在但当前聊天路由未接通；自动提取/Dream 为主回复后的 daemon 工作，非持久队列，进程死亡不能保证重试。Dream 不是主动导购调度器。
- **保留/替换接缝**：保留四类语义、用户修正优先、过期/隔离；可替换整理触发和工作队列，不赋予离开后发消息权限。

### J. 模型适配、运行时、事件与提交

- **现有调用**：`api/guide.py:process_turn_stream → TurnStreamService.stream_turn → GraphTurnService.process_turn → graph runtime/coordinator`；provider/transport 负责模型接口；`respond → commit_graph_turn → final_guard`，然后返回 committed 结果。
- **输入 → 输出**：message、request ID、会话/任务预期版本 → progress/SSE、模型提案、工具事实、已提交 final/receipt/error。
- **事实/状态**：业务数据库与 TurnReceipt/Operation；trace 是观测记录，SSE 是传输，模型上下文是工作材料。
- **副作用/授权**：入场先归属与重放；退出前 recheck 原 anchor、stop、deadline、CAS；不得提前播报未提交成功。前端断开 SSE 当前不等于服务端停止。
- **现状/缺口**：当前售前八节点新图/请求，无 checkpoint、interrupt、resume、回边；Mercury 当前五轮手写 tool loop，可再一次无工具总结，并不是 LangGraph。
- **保留/替换接缝**：售前 Pi 替换模型—工具循环；售后 LangGraph 组织资格→提案→确认→提交→回执。两者共用业务契约，不能各自复制购物车、订单、记忆权威状态。

## 3. 实际调用关系的量级

以下是已逐项定位的关系，不是全仓静态 call graph，也不是把类数当架构复杂度：

1. 一个售前回合现有 **8 个顶层节点**，decide 后三条实际执行路径 retrieve/mutation/answer；所有路径汇入 answer/respond。读取至多一个批次，之后不能回到读取。
2. 方案准备现有 **3 个目标分支**：dish、product、scenario；三者最后都受供给/金额/条件校验，不是三套独立 agent。
3. **3 种进入购物车的用户路径**：确认整份方案、逐行显式加购、货架直接加购；需复用库存/版本规则，但并非都必须经过聊天模型。
4. `ShoppingPlanService` 构造时依赖 **CatalogService、OfferService、PlanValidator 三项**；`TemplatePlanService` 依赖 **CatalogService、PlanValidator 两项**；`PlanValidator` 又依赖 **OfferService、DeliveryService、CatalogService 三项**。这八条明确依赖说明事实/校验是共享层，不应包成八个 agent。
5. Mercury **10 个工具入口 → 9 个 services 函数 + 1 个 policy 函数**，其中 **2 个写函数**。模型可调用多个读函数，但写权限仍应只有被确认的业务提案能取得。
6. 主回合与记忆是 **前台回复链 + 回复后整理链两条生命周期**，不是两条都能发主动消息的用户任务。

## 4. 三条完整业务旅程

### 旅程一：购买任务规划——“两个人自己做番茄炒蛋”

1. 用户给目标；模型提取 dish/人数/条件，只提出意图，不能自产 SKU/价格。
2. `ReadTools`/检索定位真实菜谱，`mutation._resolve_named_target` 区分精确/别名与相似候选。相似候选必须先让用户选定。
3. `authorize_mutations/compile_decision → PlanChangeExecutor.prepare → guarded_prepare_purchase_plan → TemplatePlanService.build_plan`：算食材与包装，再由 validator 给价格、库存、缺项和预算结果。
4. `respond → commit_graph_turn → PlanCommitService.apply_result`：原版本仍有效才写采购清单；这是**计划写入**，购物车仍空。
5. 用户单独确认精确 SKU/数量；确认 API → `ConfirmationService.confirm → CartService.apply_confirm_items`，原子写购物车与回执。重放同 ID 返回原确认。

最小现有例子：`backend/tests/test_ceres2_controlled_purchase.py` 明确断言“问候无任务→两人番茄炒蛋方案→恢复相同方案→确认前购物车为空→确认/重放同 confirmation_id”。fixture 预期是一包 500g 番茄、一盒 6 枚鸡蛋、1,660 分；这是**测试数据预期，不是实时商品报价或本文测试结果**。这条例子足以讨论新 runtime 应继承的边界，无需先恢复整套历史购买验收。

复杂度扩展已有源码证据：`test_v2_shared_demand.py` 断言加一人份番茄蛋汤后番茄需求 300g+125g、鸡蛋 3+1 枚分别合并成一包/一盒；该测试引用缺失 fixture 模块，不能据此说当前跑通。服务职责仍清楚：模型决定问什么/建议什么，需求与包装服务负责合并算术。

### 旅程二：品类内选购——“想买可乐，先比较，再选一款”

1. 用户指定品类，尚未选定具体 SKU；Pi 目标是在范围内自行查候选、规格与价格，再决定是否需要补查。
2. 当前可调用 `CatalogService.search_products/get_product/comparison_cards` 取事实；比较意图到 `ReadTools` 的完整通路有缺口，必须标为待接入，不能用模型常识填补。
3. 展示候选与证据，不建购物车；用户选择真实候选后 `PlanChangeExecutor.prepare → _prepare_product → ShoppingPlanService.build_product_plan → validator` 形成选定商品的采购清单。
4. 同旅程一的版本提交与独立确认加购。顺手推荐薯片是新增目标：可以建议，未选定不能并入清单。

`test_v2_cola_comparison.py` 的预期是先返回五张真实卡、无 plan/购物车，再选择；六罐 330ml 共 1,980ml、18 元、9.09 元/升是 fixture 事实。当前 compare/schema/前端类型缺口使这不是完整现状演示。最小不依赖缺口的 P0 路径是“商品查询→用户明确指定 SKU→build_product_plan→独立确认”；完整对比是对这条路径的读取能力扩展。

### 旅程三：模拟订单售后——“这单能退吗？可以的话帮我申请”

1. 先以可信 owner 查 `list_orders/get_order_details`，绑定真实 order/item；需要时 `get_delivery_status/search_policies`，再查对应 eligibility。
2. 服务返回能否退、原因、金额；模型只能据此解释。新版生成具体申请摘要，包含对象/数量/金额/条件，等待明确确认。
3. 确认后 LangGraph 调用确定性提交边界；边界再次校验归属/资格/提案未变化，调用 `create_refund` 或 `create_return` 的保留规则，写申请与动作回执。
4. 重放同一确认 ID 返回第一次回执；“已提交/待审核”不得说成“已退款”。

现状只能证明资格与 create 规则存在：**可信统一订单、持久提案、确认门、回执重放尚缺**。最终售前—结算—售后闭环需要模拟结算与订单桥接，不能仅替换 `run_mercury` 就宣告闭环完成；但这不是先做 Mercury LangGraph 运行时的前置条件。可先基于现有隔离演示 fixture 与服务契约验证运行时，再整合完整闭环，遵循“运行时先行、闭环后接”的顺序。退货现是整行数量；是否需要部分数量是额外产品范围问题，不能从字段里猜。

## 5. Pi、LangGraph 与前端各做什么

这里“前端 Pi”若指售前智能体，应理解为**售前模型/工具循环编排**，不是已经决定将 runtime 跑在 React 浏览器。部署位置和跨语言接口要在服务边界明确后决定。

- React：显示对话/候选/清单/确认摘要/结果，发送用户动作与预期版本。
- PiAgentRuntime：理解目标、在已授权范围内反复读取、提出有事实依据的下一步；交出待验证的业务提案。
- LangGraph：售后流程与等待确认/恢复；消费同一个身份和订单事实。
- 共享业务服务：目录、用量、供给、条件、购物车、订单、资格、记忆、回执，决定“事实是什么”和“现在是否允许写”。

保留业务行为可以通过移植服务、RPC/HTTP 适配或共进程调用完成。现在不把语言、网络边界或每组一个服务实例偷偷写成既定方案。

## 6. 真正待用户决定的下一层问题

已知事实与已定范围不再问；以下才会改变产品行为：

1. **可可/墨墨保留两个入口，还是使用统一界面交接？** 已确认的是售前一个长期对话，尚未决定售前/售后共用时间线。当前待用户选择：先保留两个入口、共享可信 owner 与业务对象，或统一界面并标识角色及售后申请。建议第一版保留独立入口、共享 owner；该问题已由主会话提出，等待答复，不重复询问。
2. **关联新目标用哪种用户动作选定？** 推荐候选上的“加入本次采购目标”与明确文字均可；“好/看看/比较”只推进说明，不含糊当作新增目标或加购授权。
3. **确认加购保留按钮，还是也接受明确自然语言？** 推荐先保留按钮绑定方案版本；若文字也支持，必须绑定正在展示的精确清单，不能降低已经确定的独立确认边界。
4. **售后范围是否维持整单仅退款/整行退货？** 推荐第一版维持既有规则；部分数量意味着提案、金额和 ledger 都要新增规则。是否需要讨论由主会话结合既有决定去重。

交接 UI 决定不阻止厘清共享服务；语言/部署选择应在业务旅程认可后讨论；源码已能证明的规则与缺口不交给用户猜。

## 7. 来源与未验证范围

- [售前静态审计](../../../archive/ceres2-before-clean-20261005/work/ceres2-upgrade/research/presales-audit.md)、[Mercury 静态审计](../../../archive/ceres2-before-clean-20261005/work/ceres2-upgrade/research/mercury-data-audit.md)。审计旧建议里先恢复全链、Python/LangGraph baseline 的优先级不作为当前任务指令。
- 主要实现：`backend/app/api/{guide,cart,catalog,mercury}.py`；`backend/app/agent/{authorization,goal_router}.py`、`agent/tools/`、`agent/graph/{graph,turn_commit}.py`；`backend/app/services/` 下本文逐项方法；`Mercury/mercury/{agent,tools,services,policy}.py`。
- 断言来源：`test_ceres2_controlled_purchase.py`、`test_v2_shared_demand.py`、`test_v2_cola_comparison.py`、确认/并发/记忆测试族；引用表示预期与保护意图，不表示这轮执行或验收。
- 本轮未安装依赖、运行测试/模型/服务、查看活动数据库/凭据/cookie、操作 Windows、修改任何业务源码。产物仅本文。

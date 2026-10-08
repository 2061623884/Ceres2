# Ceres2 本机后续开发方案

本方案以九票集成后实际使用效果为目标。执行状态只在
[本轮 TASK](../../tasks/ceres2-local-followup.md)维护；本文件不是新的验收通过声明。

## 起点与已完成范围

固定起点 `170fac0bc75fcc855897b073337ba218abeb5b7d`，本地分支
`codex/ceres2-local-followup-20261008`，工作树 `Ceres2-integration-20261008`。
旧本地优化分支 `6734c7f` 保留为交付快照，云端集成分支保持独立。

当前已有 BM25/BGE/RRF、显式 GraphRAG、规范菜谱事实、同 Pi 原生完成与可选审校过程消息、模拟商品/订单/售后闭环、运行采集和人工标注接口。
本机依赖、构建、新 BGE hybrid 索引、静态 seed，以及受控模型/检索端口下的 Firefox HTTPS 旅程已通过，见
[本机结果](../../work/local-cloud-integration/local-acceptance-20261008/LOCAL-ACCEPTANCE-RESULTS.md)。
真实模型的对话质量、真实 GraphRAG、完整记忆生命周期和用户本人接受仍需要单独证据。

本轮重点是可复跑的测试、任务评测及失败反馈，产品改进由真实样本、当前合同和可复现失败驱动。订单后端以闭环为范围，不预先重写已交付模块。

用户新增固定参考为 Ceres1 `2061623884/ceres` 的 `codex/ceres-v4-evaluation`，SHA `72bb1b99bf040c8b0bae5d026888bc059bc9423d`。借鉴任务级用例、独立状态、代码判分、完整分母、重复执行与版本冻结方法，重新适配本工程事实；不导入 Ceres1 runtime、运行库、索引、凭据、历史成绩或既有 holdout。

## 1. 建立真实场景基线

原拟定的 24 条公开场景扩展为 Ceres1 对齐的覆盖方案：40 条公开开发/回归、20 条由 Tester 隔离维护的新验收场景，20 条核心各独立执行 3 次，其余 40 条各一次，共 100 次计划任务执行。先核对代表场景与评分规则，再执行同版剩余计划；模型配置未就绪的部分保留未执行，不虚构样本。记忆/Dream、GraphRAG组件和浏览器另列，不混进 API 任务分母。

覆盖购买任务规划、品类约束选购、修改/明确确认、政策与购物混合、角色选择、菜谱人数/已有食材、显式关系查询、售后续购和取消/恢复。单次执行包含初始状态、用户目标、预声明后续动作、业务成功条件、硬约束、禁止行为、来源和允许变化；不要求唯一措辞或唯一合格SKU。

每条场景先定义期望行为及事实依据，再由专职 Tester 使用用户当前批准的模型/provider/temperature/输出额度采样。真实采样需要本工作树独立配置；不得从模板或历史文档猜模型。单批调用范围及独立 graph build 的有限正数 timeout 在执行前记录。

记录任务结果、事实/引用错误、预算终止、澄清等待、首条可见过程消息时间、最终结果时间和 provider usage。分别观察入口判断、政策预取/检索/复用、主 Pi、审校和图调用；未知值保持未知。

开发/回归与新验收按场景族分开，已看过/调参使用的样本不重新命名为未见。实施者不读取原 holdout 或新验收正文；Tester记录来源和首次使用版本。新验收不自动等于统计泛化或严格盲测。改版比较绑定源码、模型、Prompt、语料、索引、执行器与评分规则及相同输入条件。

## 公共评测接口与接缝

沿用公共 HTTP/API/SSE 和现有 capture/annotation v2，不新增产品测试专用会话接口。代码探索确认每 owner 只有一个 canonical Guide session，故独立用例/重复执行创建独立合成 owner，而不是假设同 owner 可创建任意新会话。

公开开发输入为 `ceres-local-followup-dev-cases-v1`，包含 `version` 与 `cases`，用例的 `case_id`、`message` 为执行器必需输入，另记录 category、scenario_family、split、core、expected_behavior、fact_sources 与机器 `checks=[{path,operator,expected}]`。operator 为 eq/contains/min/max/length/min_length；min/max用于数值，min_length用于数组条数。规则路径使用当前公共证据，缺失或非可比较值不算满足；eq预期null可明确表示合法无方案。采集输出为 `ceres-local-followup-batch-v1`：`case_set={version,sha256}` 与 `cases=[{case_id,capture,...}]`，每个实际 Guide run 的 capture 沿用 `ceres-eval-capture-v2`；按稳定 case/execution ID 配对，不把不同 owner 冒充同一身份。

首条case.message后允许预声明 `steps` 三种动作：turn（带message）、confirm_plan、repeat_confirmation。首轮与续问走公共角色判断/Guide run；确认使用当前公开方案及版本、选中项与固定幂等key，重复确认复用完全相同body/key。未支持的setup或动作明确记录unsupported，不能只执行首句后假称整个任务成功。新40集包含39条单轮和1条确认/重放闭环，不以其代替完整售后/Memory driver。

row.before/after覆盖整个任务，row.steps包含index0首轮turn和所有后续动作，逐步保存before/after、真实run capture或确认receipt。row.capture为最后实际Guide run，row.captures为全部真实Guide captures，确认不能伪造Guide run。评分按预声明动作逐步检查：turn默认不写cart/orders/role，confirm_plan允许该次cart结果，repeat_confirmation不得再改变cart；后续授权不向前一轮借用。

fact_sources的路径#anchor按实际源类型定位：JSON record ID、JSON结构路径（如experience.json#expression.keke）或Python符号；不能把结构路径当成必须出现的字面字符串。静态引用完整性不等于真实模型遵守来源。

逐题额外证据为 `before/after={guide,cart,orders,opening}` 与 `catalog_facts={items,total,page,page_size}`，均从该题公共 HTTP 读取；未取得保持 null并记原因。当前目录73条，使用500页上限并保留total以识别不完整事实，不声称支持任意规模。GET cart初始化属于准备，不算Agent写入成功。每题读取当前Offer，不用批次开始的同一快照冒充全程。

客户端逐条 SSE 到达以 run POST 开始的 monotonic 时钟记录 `first_interim_ms`、`first_final_ms`、`stream_complete_ms` 和 `timing_source`；first_final指首个answer.delta。它不包含前置角色判断，也不是人工判定的“首个有用结果”；没有对应消息保留 null，tool progress 不冒充 interim。服务端事件 recorded_at 与客户端计时分别留证。多轮顶层计时仍指首轮，timing_run_id明确该run；各turn step另留其计时，不能把顶层和steps重复计入样本。

重复计划置于 batch 的 `plan=[{case_id,trial,execution_id}]`，execution_id 为 `{case_id}:trial:{trial}`。首批核心trial1、其他trial1、核心trial2/3按固定计划运行；正式调用 `--core-repeats 3`，默认单次仅供窄smoke。`--max-executions`限制实际执行而不截断计划，未执行项保留not_run；`--resume`只续not_run，要求用例hash与计划一致，不重跑已尝试失败或改写旧轨迹。无plan的既有单次批次以case_id配对；有plan必须按execution_id，标注仍绑定准确owner/run。

执行器只向用户明确选择的评测 API 发请求，不自启真实服务。角色切换、问题回答、确认等只能按用例预声明动作执行；无动作授权时保留等待状态。没有 Guide run 的角色等待/准备失败/执行器错误保留独立 outcome 和 `capture=null`，不伪造 run ID 或 Guide 历史；一题失败不使后续题消失。重复执行记录独立 trial，重评分和脚本纠正记录来源且不增加产品执行次数。

版本对照、人工标注与失败 intake 使用上述批次包。人工运行标注仍使用既有 v2字段与精确 owner/run关联；无运行的 case 质量保持未知，等待与业务事实检查单列。实现者准备公共CLI/HTTP行为测试，专职Tester证实RED后最小实现，再GREEN；这些接缝已由本方案和 implement-spec 授权，不重复询问。

## 2. 可可对话与时延优化

用户想要的是同一请求进行中按需要说多条有价值的话。简单问题可直接完成；复杂任务依据实际工作产生过程消息。自然度采用人工标签：是否及时、有必要、连贯、重复或套话、与最后结果一致。

基线明确暴露问题后，对对应 Prompt、Pi 审校/发布调用路径或前端消息展示作最小改进。消息数量不固定，不通过把 final 文本机械拆成气泡达成目标。使用同一主 Pi loop；过程消息仍经审校、有稳定 ID，不能泄露推理或声称未经证实事实。

保持当前 15 秒/最多 5 轮合同及原有模型额度，定位判断、冷知识加载、主模型、审校等实际耗时后再优化对应步骤。不能提高预算或换模型来宣称原条件下改善。界面沿用统一 Grok bot 风格，由用户本人接受自然度和视觉效果。

## 3. 检索、菜谱与显式 GraphRAG

在同一 demo 语料上完成获准真实 provider 的官方 GraphRAG 构建、Local/Global 查询及版本/调用证据。图构建使用独立有限正数预算；图缺失或失败不能视作空结果或冒称已执行。

比较 BM25、dense、RRF 候选与最终 canonical 商品结果；覆盖别名、品类/规格、缺商品、政策不匹配和混合查询。只有实际错误或漏召回才能驱动 query、召回/排序、来源或必要 demo fixture 补充，保持规模适当。

菜谱任务验证人数、规范用量、必需/可选食材、用户已有食材和 SKU 映射；确认前不写购物车。图关系选择与规范数量分别留证，不把图边当成营养、过敏或替代安全事实。用相同公开任务比较图辅助与已有路径的收益，保留显式图查询和确定性 recipe_facts 的边界。

## 4. 评测与反馈闭环

沿用已有 owner 限定导出和人工标注接口，形成一次实际的“运行采集 → 显式标注 → 错误归类 → 修复 → 同条件回归 → 版本对照报告”。错误分类至少区分检索、事实/政策、业务动作、角色、对话、时延和恢复。

失败样本以脱敏、可复现的公开开发用例进入回归；标签保留期望、理由、严重程度和审阅者。独立质量集不进入 Prompt/调参数据，未人工审阅的质量标签保持 null。优先交付可复现数据和报告，不预先新增无调用方后台面板或自动训练。

代码判分检查公开业务事实与用例事先定义的硬条件：实际商品/数量/当前Offer金额、预算、确认/切换授权、目标订单、重复副作用与取消后发布。模型裁判只提供未校准语义诊断，不代替这些检查；完成回执、非空购物车和无裁判报警均不自动证明任务正确。自然度/自由文本不能由现有证据判定时保留未知或显式人工标签。

报告同时列计划/尝试/完成/达标/失败/准备失败/脚本失败/未执行与分组分母，失败/未执行不得从计划分母剔除；正常可完成任务与正确澄清/合规拒绝分开。功能、关键违规、逐轮15秒、首个有用结果、P50/P95、核心三次均达标、usage覆盖率分别报告，不合成无解释总分。未采集时间/usage/费用保持未知；TestClient缓冲与真实客户端SSE计时分开。

## 5. 闭环与记忆剩余门槛

商品/订单/售后已有实现以维持闭环为目标；补用户确认、重复点击幂等、数量修改、照片范围、停止和真实断网 SSE 重连证据。仅对阻碍这些行为的实际缺陷实施修复。

Memory/Dream 按既有合同独立验证保存/读取/更正/删除、迟到结果与重启不复活、真实模型提取，以及 10 条/24 小时门槛和冷却/时钟边界。一次聊天提取不能替代 Dream 验收。此部分不引入活动提醒或跨回合自主通知。

## 执行顺序与交付

先对齐 Ceres1 方法并准备覆盖矩阵、公开场景及判分规则，独立Tester验证评分器，再固定真实基线。允许执行的产品缺陷按最小复现单独处理，保留失败批次；不得在评测中悄悄修产品再沿用旧冻结。产品优化复验后再生成同条件比较。按用户加强的完整测试要求，在最终冻结版本执行适用backend全量、Pi/frontend typecheck/build、真实BGE/官方GraphRAG受控组件及必要真实浏览器。Standards/Spec独立只读审查绑定最终候选，技术、真实模型、浏览器和本人接受分开记录。

最终交付包括有依据的产品差异、公开评测/回归集、去敏运行与标注样本、质量/时延/usage 对照，以及版本与未验证项。硬门槛是没有已知越权/未确认业务写入、未证事实冒充、取消后发布或重复业务副作用；语言自然度需要用户本人接受。质量数值目标根据基线与产品期望制定，不能先写虚构的通过率。

## 合并约定

用户最新明确要求按 implement-spec 完成后不合并，先审阅；这撤销此前“完成后合并”的约定和待选目标。全部变更留在本轮独立分支，提交可审阅交付，不合入 main 或 cloud 集成分支。用户本轮提供的AGENTS另禁止推送或修改原项目，本轮只协调本地提交；历史分支发布记录不作为新推送授权。

implement-spec 的内部合并步骤也按本次不合并要求调整为同分支、唯一文件owner的纵切实施；主会话协调提交，专职Tester独占验证，两轴独立只读。原工作树53项现场、旧分支与运行数据保持独立；不执行 merge、rebase、cherry-pick、force push、部署或清理旧数据。

# Ceres2 下一阶段体验总 TASK

状态：进行中（01／02／03 已进入依赖并行 TDD 实施；其他票等待依赖技术放行）

授权：用户 `Sentinel_8fc34df15f788191a593e0c1e46dde89` 批准 10 票粒度、依赖并行 TDD 持续实施及最终 Standards／Spec 审查。唯一当前状态入口为本文件及各票；历史 16 票及原有验收状态不改写。

规格：[完整规格](../docs/plans/ceres2-next-experience-spec.md)；[批准拆分](../docs/plans/ceres2-next-experience-ticket-proposal.md)；[当前决定](../docs/plans/ceres2-next-experience-decisions.md)；[来源与基线](../docs/plans/ceres2-next-experience-provenance.md)。

## 当前执行快照

更新：2026-10-06 12:03 UTC。同一最终冻结0c752a2完整426backend、37受控DOM/client、runtime/frontend build/strict检查与OS restart1/1通过；Tester源等价和两轴独立复审均闭合。01–09受控技术门槛全部恢复／保持已放行、待验收；10受控交付通过但仍待验收，真实provider／浏览器／自然语言／holdout／V3比较／本人验收开放。历史失败及旧候选成绩保留，不拼接成当前结论。见[最终报告](../work/next-experience/10/final-controlled-verification.md)与[接手文档](../docs/NEXT-EXPERIENCE-HANDOFF.md)。

本集成 checkout 的 TASK 是唯一当前状态源；各工作树只提交其实现及证据，不维护竞争状态。可视看板读取本索引与十张 TASK，仅用于展示。01／02／03 的证据入口已在各票登记；Tester 执行证据集中于集成目录 `work/next-experience/10/runs/`，保留实际来源工作树与候选。

## 任务与依赖

- [01 零食选类到确认加购](ceres2-next-01-snack-selection.md)；前置：无。
- [02 两角色无订单政策问答](ceres2-next-02-shared-policy.md)；前置：无。
- [03 一次 Kev 与用户选择跳转](ceres2-next-03-role-navigation.md)；前置：无。
- [04 饮品分类和同类筛选](ceres2-next-04-drink-selection.md)；前置：01。
- [05 四类请求按需上下文且语义不变](ceres2-next-05-context-equivalence.md)；前置：01、02、03。
- [06 先显示结果再流式介绍](ceres2-next-06-result-first-stream.md)；前置：05。
- [07 两角色自然表达受控优化](ceres2-next-07-natural-expression.md)；前置：06。
- [08 既有首页活动成品选购](ceres2-next-08-home-theme.md)；前置：01。
- [09 售后结果后回到购物](ceres2-next-09-aftersales-return.md)；前置：02、03。
- [10 同一候选的完整体验证据](ceres2-next-10-candidate-evidence.md)；前置：04、07、08、09。

## 执行与放行

01／02／03 为初始前沿。前置票提供下游所需行为、稳定合同及必要技术证据后，主会话放行依赖；无需等待逐票本人验收。缺真实页面／必要模型等证据必须明确阻塞，不用最终票替代逐票技术门槛。状态按待开始／进行中／阻塞／待验收／已验收管理。

TDD 每次先由实现者准备公开可观察场景，再由专职 Tester 执行 RED；实现最小行为后由 Tester 执行 GREEN／必要回归。安装、测试、lint、typecheck、build、服务及浏览器验证均由 Tester 独占执行。最终冻结同一候选，Standards／Spec 独立只读审查，修复后复验。

## 唯一责任与共享改动

- 集成负责人：prepare_next_integration。独占 integration 分支、backend main／router 注册、跨票合入和当前任务索引；仅在主会话技术放行后合并完成分支。
- 01（implement_next_snack_flow）：问题／选项、选择 DTO／共享 schema、静态供给清单版本和既有商业事务接口的最小衔接。其他票先提交适配要求，不平行改此权威。当前Prompt／Pi runtime已交05，问题／供给合同仍由01维护。
- 03（implement_next_role_navigation）：页面外壳／App 导航与公共客户端、单次 Kev／角色能力／重放协议。页面实现由 03 单一作者；integration 负责人统一合入。
- 02（implement_next_policy_help）：一般政策及两角色读取接缝；与 03 协调 UI，向 05 交固定政策基线。
- 01 在初始 01–03 前沿曾独占的 Python Pi runtime／tool dispatch 与 worker.ts 工具注册。02 提交政策工具合同和最小注册请求给 01；03 的 runtime envelope 需求同样交 01。02 可独立实现政策及其测试，必须在共享适配集成后才技术放行，避免循环等待。
- 04（implement_next_drink_filters）：饮品筛选有界扩展，复用01问题／选择／确认合同；共享合同变更交01审阅／有界移交，不能另造状态权威。
- 08（implement_next_activity_flow）：既有活动入口与限定成品关联记录；共享fixture清单与问题合同交01协调，App适配交03。
- 05（implement_next_context_modules）：公共、角色与能力Prompt／事实表达模块唯一维护；共享Pi runtime责任现由01有界交接给05，其他票提交适配请求，06／07顺序基于冻结对照修改。
- 09（implement_next_shopping_return）：现有售后结果／失败保留和回购物纵向接缝，商业规则与订单权威不重建，App适配交03，公共Prompt／runtime适配交05。
- 06：已释放结果先行／解释流与恢复合同；runtime／Prompt现交07继续受控表达，不能改变商业状态权威。
- 07（implement_next_natural_expression）：唯一runtime／Prompt表达维护人；基于06冻结baseline，保留04条款、05模块、08guard、09失败／回执语义；App改动协调03。
- 专职 Tester：test_next_experience；依赖安装、所有执行验证和证据。
- 记忆既有权威若出现回归，由主会话指定唯一维护人再修；原有独立缺陷超出本票范围时单独报告，不能塞进 10。

## 版本与证据

集成分支：`ceres2/next-experience-20261006`，干净公开基线 `64ca7b6b9a7aa113aa42d54270604913f6c19d58`。各票独立工作树与分支，完成前同步 integration；不 reset／stash／丢弃已有工作。主会话放行后合入，未授权 push 或清理未核实工作树。

证据总目录：[work/next-experience](../work/next-experience/README.md)。当前仅有上述 TDD 局部受控证据；未有整票技术放行、真实模型、真实页面或本人验收通过。最终 10 负责同候选复验，发现缺陷回到所属票。

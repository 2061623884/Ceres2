# TASK 03：一次 Kev 与用户选择跳转

状态：待验收

阶段：受控技术完成；外部验收待完成

技术放行：已放行

放行范围：仅受控技术依赖。主会话条件批准，Tester于2026-10-06 09:16 UTC确认最终52public／10DOM／build/typecheck源码合入一致。真实provider／浏览器／本人验收仍待验证。

最近更新：2026-10-06 09:16 UTC。最终候选`7634efd`无冲突合入`13c2cab`，含单次Kev／guide及Mercury准入、复合明确返回、race／ACK保护及明确重试UI。Tester确认与最终52项公开测试、10个受控DOM旅程及runtime/frontend build/typecheck相同：API216／source-harness248文件、三份记录无缺失或变化。主会话条件已满足，03受控技术依赖放行、待验收；05／09前置已满足。全量继承回归、独立Standards／Spec、真实provider／真实浏览器及本人验收分别待完成。

最终证据：[52公开](../work/next-experience/10/runs/next03-release-public/record.json)、[runtime](../work/next-experience/10/checks/next03-release-runtime/record.json)、[10DOM＋frontend](../work/next-experience/10/checks/next03-release-ui/record.json)、[合入一致性](../work/next-experience/10/next03-integration-equality.json)。生成dist需要Tester重建后执行，不纳入产品源等价证明。

检查点证据：[实现与合同](../work/next-experience/03/implementation.md)、[16 项](../work/next-experience/10/runs/next03-green-04/record.json)、[55 项](../work/next-experience/10/runs/next03-mercury-regression-built/record.json)、[App DOM](../work/next-experience/10/checks/next03-dom-04/record.json)、[8 项旧 DOM](../work/next-experience/10/checks/next03-legacy-dom-02/record.json)。

工作树：`Ceres-workspace/worktrees/next-03`；分支：`ceres2/next-03-navigation`；初始规划基线：`6a4489650b81715aa0beea49eefcf015e91290fd`，实施源码另以 Tester 原始记录对应，不能仅用 HEAD 代替 dirty 候选。

证据：[RED record](../work/next-experience/10/runs/next03-red-01/record.json)、[RED 原始输出](../work/next-experience/10/runs/next03-red-01/output.log)。

证据限制：初次记录只覆盖 tracked 源哈希；专职 Tester 后续 launcher 已加入 untracked 源／测试与前后版本一致性核对。当前技术依赖仅在受控范围放行；真实模型、真实页面与本人验收仍未验证。

负责人：implement_next_role_navigation；TASK03 实现负责人；角色 UI 与单次 Kev 唯一维护人。 状态由主会话维护；测试执行仅专职 Tester。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 最新 Ceres 页面视觉下，所有新自由文字一次 Kev 判断职责，并在同次判断中为可可职责内请求给四类标签；Mercury 保留自身售后能力；职责不匹配由用户选择跳页，并具正确 opening、手动入口和失败恢复。

**阻塞：** 无，可开始。

**验收条件：**
- [ ] 每条新自由文字一次职责判断；探索／采购修改／事实问答／闲聊四标签仅用于可可职责内请求，在同一次 Kev 调用中产生。Mercury 保留 LangGraph／政策／售后能力，不套用可可分类、不新造售后枚举、不增加第二次 Kev；Kev 不排工具、抽参数、判完整性或授权。
- [ ] 同请求重传、工具循环、SSE 重连／恢复、接受转接不再路由；有效结构化动作不调用 Kev。
- [ ] 缺信息、无结果和服务失败留当前角色；职责不匹配才建议切换，不暗中跑另一角色。
- [ ] 自动提示每 opening 最多一次，在展示 ACK 后消耗；拒绝／切换不重置，刷新保留，仅显式关闭重开重置。
- [ ] 明确返回请求不再次索要导航确认；手动入口只续接有效意图；Kev 失败可见且保留手动入口。
- [ ] 交接主要原始请求，必要商品／订单标识仅用于定位；目的角色重查，切换不构成交易授权。
- [ ] 最新视觉保留 C2 比较／采购／订单／售后／人工／停止／恢复及版本保护，键盘与错误状态可用。

**迁移／数据：** 只复用 Ceres 视觉与角色行为，适配 C2 会话、版本、事件和回执，不照搬进程内 opening 字典或旧请求体。使用现有商品／订单验证导航，不要求新增饮品供给。必要 opening 元数据优先从持久现有记录表达。

**必要证据：** 公开 API／SSE 角色旅程和真实页面接受／拒绝／返回／刷新／关闭重开／故障；逐 turn 真实 Kev 原输出与调用计数；复杂多目标不遗漏与闲聊不建采购任务。输出唯一 Kev 协议与页面适配合同供 05／09 复用。

## 下一步与证据

为05提供四值capability及完整原文消费合同，为09提供同一请求身份和最小交接；两票不得再路由或用导航替代业务授权。03继续唯一维护App。全量继承回归与外部门槛另行验证。

执行证据目录：`work/next-experience/03/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；以上仅是已列受控用例的局部证据，其他门槛未验证。完成实现只能记待验收，不能代替本人验收。

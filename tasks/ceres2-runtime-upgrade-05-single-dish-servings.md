# Ceres2 Runtime 05：单菜人数与采购修订

状态：**待验收**。
负责人：**implement_clean_dish_servings（共享导购入口唯一维护者）**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过（主会话 2026-10-05 18:26 UTC 受控技术 release；97/97 两次、实际 App DOM 两次、typecheck/build、两轴审查闭合）**。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户选择一道菜、指定或修改人数，看到食材需求、整包数量和余量，选择基础调料/改选后重新确认加购。

## 阻塞关系

[04 明确选购与双入口确认](ceres2-runtime-upgrade-04-explicit-cart-confirmation.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [ ] 恢复 V1 单菜与 V2 人数完整旅程；保留默认基准不是用户指定人数、pantry 默认不选、未选不代表家中已有、预算协商不等于加购。
- [ ] 需求/包装/清单/余量 UI、最小菜谱与多规格 seed、需要的字段迁移和公共行为测试一票交付。
- [ ] 验证人数修改、规格选择不丢失、约束/排除/金额、采购修订、加购前后分离与旧确认失效；不在本票实现多菜或供给全局优化。

- [ ] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [ ] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [ ] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开导购/方案修订/确认/购物车接口与单菜清单页面，观察需求、包装、余量及真实加购结果。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

主会话已确认本票受控技术 release；共享源维护权转交 TASK06。TASK08 后续审查修复清单单列于 HANDOFF.md，不混入本票冻结证据。真实 qwen3.8-27b、真实浏览器和用户本人验收仍独立待完成。

## 证据

- 新公共测试：`backend/tests/test_dish_public.py`。实际 Pi SDK + 本地受控 HTTP provider + 隔离业务库；基准 2、明确 3/5 人、6/10 枚规格、调料未知量、旧确认失效、先逐行加购后修订均走公开 HTTP/SSE。
- Tester 原始证据：`work/ceres2-runtime-upgrade/05/test-runs/`（逐片 RED→GREEN，不继承历史）。
- 最小菜谱：`data/fixtures/recipes.json`，选择性静态来源 SHA 与选择方法：`work/clean-rebuild/05/recipe-provenance.json`。运行时不依赖 staging/archive。
- 复用 `GuideTask.plan_json/conditions_json` 存储 dish/people/source/SKU/selection 及需求事实；无需新增 schema 或迁移。重复升级与 hold 的公共测试验证保全；确认/ledger 仍复用 TASK04 同一事务。
- UI DOM harness：`work/clean-rebuild/05/ui_dish.mjs`，使用保留 App。DOM 模拟不是实际浏览器证据。
- 所有真实模型仅允许 qwen3.8-27b；安全配置缺失，真实模型未验证。实际浏览器和用户本人验收未完成。

- 审查修复与来源边界：`work/clean-rebuild/05/review-closures.md`；冻结源码候选：`work/clean-rebuild/05/FINAL-CANDIDATE.json`；下一票接口交接：`work/clean-rebuild/05/HANDOFF.md`。

- 最终 Tester 双轮：`final-dish-01` 97 passed / 128.48s，`final-dish-02` 97 passed / 128.63s；`final-dish-source-comparison.json` 证明 4 份快照的 scoped source 一致，fingerprint `24e7be7e8fb43596b1b3205c0b534f05fb10b61dce14f88fe73a132df50632aa`。未声称全工作树一致；并行 08/10 独立变动列于同文件。
- 最终 `final-dish-dom-01/02`、`final-dish-typecheck`、`final-dish-build` 均通过；DOM 仅模拟 transport，不替代真实浏览器。

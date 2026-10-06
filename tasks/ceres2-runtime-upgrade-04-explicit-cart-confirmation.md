# Ceres2 Runtime 04：明确选购与双入口确认

状态：**待验收**。
负责人：**TASK04 purchase owner（主会话分配）**；所有测试命令仅由专职 Tester 执行，Standards/Spec 两轴独立只读审查。
技术验收：**通过**（2026-10-05 17:55 UTC 主会话受控技术验收；真实 provider／真实页面及本人验收未完成）。
用户本人验收：**待验收／未完成**。

2026-10-05 15:42 UTC 已获干净重建及持续实施授权；历史通过不继承。
母任务：[Ceres2 升级](ceres2-upgrade.md)；[规格](../docs/plans/ceres2-proactive-upgrade-spec.md)；[批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md)。

## 范围与交付

用户明确选定一个直接商品形成版本化清单，经按钮或“就按这个加购”对唯一当前展示方案确认，得到真实购物车结果；重复/旧确认不能再写。

## 阻塞关系

[03 长期任务与可响应运行](ceres2-runtime-upgrade-03-persistent-responsive-runs.md)。

用户已授权持续实施；主会话按依赖安排唯一实现负责人和共享接口责任人。前置尚未在新工程验证时不得继承旧工程技术就绪。

## 验收条件

- [x] 打通 Pi 提案→确定性方案服务→清单 UI→共同确认事务；保留货架及逐行明确加购能力。需要的方案/回执字段迁移、最小商品/车 seed 与测试随票。
- [x] 预算/排除、供给/配送再验、SKU/件数、已购 ledger 及事实回执完整贯穿；关联新目标先建议后选定，含糊 ACK 先澄清。
- [x] 修改方案让旧确认失效；停止先到阻止提交，提交先成功如实展示，不自动删车；同 key 同正文重放、异正文冲突。
- [x] 验证 HTTP/SSE、按钮与文本等效、版本/owner/竞争/失败原子性、无授权不写和实际车数量。

- [x] 本票所需最小隔离 seed/fixture、业务/API、UI 和行为验证一并交付；涉及新状态时提供增量迁移，不需要 schema 变更时记录沿用理由，不创建无需求框架。
- [x] 空库/合成旧库、重复升级、旧业务事实保全与安全回退按本票实际数据范围验证；不用活动数据库或原项目数据补 fixture，不恢复无确认写入口。
- [x] 记录公共行为红/绿与必要回归、新增 V2 场景两次独立自动行为验证及两轴审查/有效修复复验；离线、真实模型、真实页面、用户本人验收分别标明，不继承历史通过。

## 测试接缝与演示

公开清单/确认/购物车 HTTP/SSE；补充 ConfirmationService/CartService 业务提交 unit-of-work 故障与竞争注入。

演示结果以“范围与交付”中的完整用户旅程和验收条件为准。使用真实 Pi SDK/真实 LangGraph 的适用集成路径；受控模型 fixture 只证明确定性行为，真实 provider 兼容与模型效果另行验证。固定源码及未提交变动、依赖、数据/schema/index、模型/Prompt 和时钟；记录真实输出/退出码。没有测试权限或凭据时如实记未验证，不能用 mock 或进度消息替代完成证据。

## 下一步

主会话已完成本票受控技术验收，05 单菜与 08 比较接续；唯一 guide/runtime/worker/App 维护权转交 05，08 与 10 通过 05 协调共享补丁。真实 qwen3.8-27b、真实浏览器页面及本人验收保留到 16，当前不冒充已完成。

## 证据

当前新工程证据：

- [受控发布清单](../work/clean-rebuild/04-purchase/RELEASE.json)；[05／08 接续交接](../work/clean-rebuild/04-purchase/HANDOFF-P05-P08.md)。
- [实现与事务交接](../work/clean-rebuild/04-purchase/README.md)；[最终候选源码与消费依赖指纹](../work/clean-rebuild/04-purchase/FINAL-CANDIDATE.json)。
- [独立 Standards／Spec 审查及修复关闭](../work/clean-rebuild/04-purchase/review-closures.md)。Spec 两个展示授权问题均先补红测再修复，未沿用此前绿色结论。
- [阶段本票公共测试绿色（34 例；后补竞争覆盖进入最终基线）](../work/ceres2-runtime-upgrade/04/test-runs/green-displayed-plan/evidence.json)；其后按钮／文本竞争补测绿色。[完整基线双轮 88／88](../work/ceres2-runtime-upgrade/04/test-runs/final-purchase-source-comparison.json) 已通过；[丢失成功响应 UI 后继验证](../work/ceres2-runtime-upgrade/04/test-runs/lost-response-successor-evidence.json) 与消费的 09 删除 fence 后继单独留证，不改写基线适用版本。
- [实际保留 App 的完整采购 DOM](../work/ceres2-runtime-upgrade/04/test-runs/rendered-authority-purchase/evidence.json)、[后台刷新不得静默升级已展示授权 DOM](../work/ceres2-runtime-upgrade/04/test-runs/rendered-authority-refresh/evidence.json)、[typecheck](../work/ceres2-runtime-upgrade/04/test-runs/rendered-authority-typecheck/evidence.json)、[build](../work/ceres2-runtime-upgrade/04/test-runs/rendered-authority-build/evidence.json)。DOM 不是实际浏览器验收。
- 首轮 RED、双入口与修订 RED、逐行／hold RED、展示引用 RED、后台刷新展示 RED 均保存在 `work/ceres2-runtime-upgrade/04/test-runs/`，含命令、输出、源码、时间及退出码。

历史内容仅供参考：[归档原票](../../archive/ceres2-before-clean-20261005/tasks/ceres2-runtime-upgrade-04-explicit-cart-confirmation.md)。旧测试结果、未提交源码和运行状态不得作为本票通过证明。

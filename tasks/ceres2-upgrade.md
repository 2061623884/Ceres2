# Ceres2 干净重建与 16 项持续实施

状态：**待验收**（01–15 受控技术范围已释放；16 同版受控完整生命周期集成与最终两轴审查已通过；整体最终验收仍受外部门槛阻塞）。
受控技术范围：**01–15 已释放；16 受控集成／最终审查通过**。不宣称全部 16 票最终验收。真实 qwen provider／真实浏览器仍未验证并受外部门槛阻塞；用户本人验收：**0／16，全部待验收**。

## 当前授权与边界

2026-10-05 15:42 UTC 用户授权完整保全现树后干净重建并持续实施：新 Git、无 remote；保留前端页面；后端与 runtime 从空目录组织，必要源码按票选择性迁移并记录来源；静态 catalog／Offer／recipes 已按对应切片选择性引入或通过可重复 seed 导入。不导入旧会话、购物车、订单、checkpoint、索引或凭据。不推送，不改原 GitHub 或 Windows 项目。

Python 业务权威＋Node/TypeScript 实际 Pi SDK 售前＋Python LangGraph 售后。参考与归档只能供阅读，禁止运行时导入、外部路径依赖或指向它们的符号链接。

## 正式票据与批准依赖

1. [Ceres2 Runtime 01：Pi 商品查询首切片](ceres2-runtime-upgrade-01-pi-product-query.md)。状态：待验收；受控技术验收：通过（21 场景两次稳定通过、两轴审查关闭）；真实 provider／页面：待 16；用户本人：待验收；前置：无。
2. [Ceres2 Runtime 02：LangGraph 售后查询首切片](ceres2-runtime-upgrade-02-langgraph-aftersales-query.md)。状态：待验收；受控技术验收：通过（14 场景两次稳定通过、两轴审查关闭）；真实 provider／页面：待 16；用户本人：待验收；前置：无。
3. [Ceres2 Runtime 03：长期任务与可响应运行](ceres2-runtime-upgrade-03-persistent-responsive-runs.md)。状态：待验收；受控技术验收：通过（45 场景两次同版通过、两轴关闭；17:11 UTC 主会话确认）；真实 provider／页面：待 16；用户本人：待验收；前置：01。
4. [Ceres2 Runtime 04：明确选购与双入口确认](ceres2-runtime-upgrade-04-explicit-cart-confirmation.md)。状态：待验收；受控技术验收：通过（17:55 UTC 主会话确认）；真实 provider／页面：待 16；用户本人：待验收；前置：03。
5. [Ceres2 Runtime 05：单菜人数与采购修订](ceres2-runtime-upgrade-05-single-dish-servings.md)。状态：待验收；受控技术验收：通过（18:26 UTC 主会话确认）；真实 provider／页面：待 16；用户本人：待验收；前置：04。
6. [Ceres2 Runtime 06：多菜合并与来源展示](ceres2-runtime-upgrade-06-multi-dish-demand.md)。状态：待验收；受控技术验收：通过（19:11 UTC 主会话确认）；真实 provider／页面：待 16；用户本人：待验收；前置：05。
7. [Ceres2 Runtime 07：供给适配与部分采购](ceres2-runtime-upgrade-07-supply-partial-purchase.md)。状态：待验收；受控技术验收：通过（150 场景两次同版验证；19:42 UTC 主会话确认）；真实 provider／页面：待 16；用户本人：待验收；前置：06。
8. [Ceres2 Runtime 08：品类筛选与真实比较](ceres2-runtime-upgrade-08-category-comparison.md)。状态：待验收；受控技术验收：通过（18:33 UTC 主会话确认）；真实 provider／页面：待 16；用户本人：待验收；前置：04。
9. [Ceres2 Runtime 09：聊天显式记忆与共享边界](ceres2-runtime-upgrade-09-explicit-role-memory.md)。状态：待验收；受控技术验收：通过（17:53 UTC 主会话确认）；真实 provider／页面：待 16；用户本人：待验收；前置：03、02。
10. [Ceres2 Runtime 10：可恢复提取与 Dream](ceres2-runtime-upgrade-10-recoverable-memory-dream.md)。状态：待验收；受控技术验收：通过（18:43 UTC 主会话确认）；真实 provider／页面：待 16；用户本人：待验收；前置：09。
11. [Ceres2 Runtime 11：历史提醒与重新采购](ceres2-runtime-upgrade-11-historical-repurchase.md)。状态：待验收；受控技术验收：通过（182 场景两次同版验证；主会话已释放）；真实 provider／页面：待 16；用户本人：待验收；前置：07、09。
12. [Ceres2 Runtime 12：持久模拟结算订单](ceres2-runtime-upgrade-12-persistent-simulated-orders.md)。状态：待验收；受控技术验收：通过（12 场景两次稳定通过、两轴审查关闭）；真实页面：待 16；用户本人：待验收；前置：无。
13. [Ceres2 Runtime 13：同用户订单与售后贯通](ceres2-runtime-upgrade-13-canonical-order-aftersales.md)。状态：待验收；受控技术验收：通过（主会话合并新工程验证与两轴结论）；真实页面：待 16；用户本人：待验收；前置：02、12。
14. [Ceres2 Runtime 14：具体确认与售后回执](ceres2-runtime-upgrade-14-confirmed-aftersales-receipts.md)。状态：待验收；受控技术验收：通过（59 场景两次同版通过、两轴关闭；17:19 UTC 主会话确认）；真实 provider／页面：待 16；用户本人：待验收；前置：13。
15. [Ceres2 Runtime 15：精简异步人工工单](ceres2-runtime-upgrade-15-async-human-cases.md)。状态：待验收；受控技术验收：通过（主会话合并新工程验证与两轴结论）；真实页面：待 16；用户本人：待验收；前置：02。
16. [Ceres2 Runtime 16：同版完整生命周期验收](ceres2-runtime-upgrade-16-integrated-verification.md)。状态：待验收；受控集成／最终两轴审查：通过（294 项两次同版验证、45 项补充检查）；最终要求：真实 qwen／浏览器未验证，外部门槛阻塞；用户本人：待验收；前置：08、10、11、14、15。

## 当前责任边界

- 主会话负责排期、双轴审查、验收和本地提交；独立新工程基线为 `49ce5111bcf296a567e8fbfad2422621ffe334db`，各票发布清单记录后续实际源码版本。
- 当前 16：`implement_clean_final_integration`，负责同版完整生命周期旅程、集成缺口和精确范围修复协调；01–15 的实现负责人和受控技术证据分别保存在正式 TASK。
- 共享基础：`design_clean_shared_contracts`，保留身份、配置、数据库／迁移、catalog／Offer／静态 seed、main、模型登记和 Python 依赖的唯一维护责任；变更按实际集成请求协调。
- 唯一测试执行：`test_clean_ceres_slices`；实现者不执行测试、构建或安装。冻结范围、双轮验证、适用 DOM／typecheck／build 与审查结果分别登记，不复用不匹配的旧源码 hash。
- 新工程可独立安装、初始化和启动，前端与新业务 API／runtime 已形成受控集成；没有运行时 archive/reference 依赖。
- 数据来源：65 个静态商品、65 个模拟 Offer、所需静态菜谱及 33 个已恢复校验的原图按来源选择性集成；无旧运行状态或凭据迁入。

## 当前后续与最终验证准备

01–15 的受控技术前置已由主会话释放；16 由 `implement_clean_final_integration` 完成了同版受控完整生命周期旅程验证，294 项两次验证、45 项补充检查及最终两轴审查已通过。当前执行证据见 [TASK16](ceres2-runtime-upgrade-16-integrated-verification.md) 与 [交付说明](../work/clean-rebuild/16/DELIVERY.md)。最终生命周期集成缺口、证据入口与真实 provider／真实页面／本人验收门槛见 [TASK16 验证准备图](../work/clean-rebuild/16/verification-map.md)。该文档只是准备，不是 16 的执行证据或验收；单票通过不能替代同版端到端集成验证。

当前外部门槛仍分开保留：实际 qwen provider 所需安全配置尚未就绪；真实浏览器路径受已确认环境限制；本人验收由用户实际体验后确认。受控 SDK／HTTP fixture 或 DOM 验证不能替代这三层。

## 集成提交与源码版本

01–15 的受控技术释放基于各自新工程固定源码、独立验证和审查，不继承归档通过。16 已按同一完整版本验证跨票生命周期：320 个源码文件，集合 SHA-256 `b711e091dd35bd646062946a76c1f57b4e514f6a243eb1a9efe917874b63b6ba`。精确范围修复及其复验不能默认为原始发布快照未变。

共享 main／模型登记已引用当前多个业务模块。本地提交须由主会话在相互依赖的实现、修复和验证就绪后显式选择可独立运行的完整范围，不能遗漏被导入的模块或混入尚未验证的活动改动。实现者不自行提交；无推送。当前受控源码已冻结并通过上述验证；本地交付版本以本分支 Git 提交为准；外部门槛未完成，不宣称整体最终验收。

## 执行与验收

当前受控实现及同版集成已完成，剩余为真实 qwen provider、真实浏览器和用户本人验收门槛，本地提交不替代这些验收。依赖 DAG 与批准 16 项目标不变，不继承旧 02／12 的通过。各票纵向交付数据、业务、API、UI 与测试，不先铺通用平台。测试命令仅 Tester 执行；固定同版两次独立自动行为验证、独立两轴审查和有效修复复验；真实 SDK/框架、受控 provider、真实模型、真实页面和用户本人验收分别记录。

公开 HTTP/SSE 与持久可见业务结果为主接缝，Python 业务提交边界补事务故障／竞争注入。每次运行最多 5 工具轮／15 秒探索保护，可早完成或等待；保护终止不冒充成功、不自动无限续跑。

## 当前文档与历史

[PROJECT](../PROJECT.md) · [PRD](../prd.md) · [规格](../docs/plans/ceres2-proactive-upgrade-spec.md) · [批准拆分](../docs/plans/ceres2-ticket-breakdown-proposal.md) · [迁移与新验收](../work/clean-rebuild/README.md) · [只读参考](../../reference/README.md) · [归档原主任务](../../archive/ceres2-before-clean-20261005/tasks/ceres2-upgrade.md)。旧九票只在归档，不在当前 tasks 目录。

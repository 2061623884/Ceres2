# Ceres2 local-cloud integration

- 状态：进行中（T01/T02/T03/T04/T06/T07及T08-A技术合入；九票技术源码已合入；T09冻结81b02f9验证/审查中，浏览器BLOCKED）
- 主责任：主会话；集成分支唯一写入者为 Merger
- Spec：[规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- Workspace：[恢复说明](../CERES2-WORKSPACE.md)
- Baseline：`37c98400e7152b89e4a58f02fff3bceaa73b0eac`
- Incoming：`6734c7fe79e670df2dae12b065dcc49c0b10a307`，只读 frozen tag `ceres2-incoming-20261007-frozen`
- Local start：`b118dbea3852026c6a04c790b1e27df67c3c9c18`
- Common ancestor：`4bed9c891261e382122d424825b649989ea92c92`

## 当前状态与下一步（唯一实时摘要）

- T01/T02/T03/T04/T06/T07：分片技术门槛、对应两轴和固定postmerge已完成并合入；不等于真实模型、实际浏览器或用户本人验收。
- T05：`4278eea`技术源码与两轴/DOM/HTTP门槛已无冲突合入`a871400`；frontend/独立harness源码等价。实际浏览器仍因环境权限/连通性BLOCKED，未进入UI，不能用DOM/HTTP代替。最终同版与用户验收开放。
- T08-A：`cb412db` 合入 `a60b6b5`，固定CLI-only postmerge11例通过。T08-B `c1a99cf`256例与两轴通过，已合入最终组合`81b02f9`；阶段技术门槛关闭，T09最终同版验证进行中。
- T09：固定组合`81b02f956298361cf9044ee289c0821a8275fab8`已交Tester及两轴；正在执行backend full、Pi typecheck/build、frontend strict TypeScript/build、相关DOM/wire/跨域合同和baseline到最终候选的两轴审查。实际浏览器BLOCKED、真实provider/本人验收NOT RUN逐项保留。
- 当前canonical产品为T05/T08-B最终组合`81b02f9`；其后仅记录文档，不得修改受测产品。具体HEAD以Git读取为准，不用分支名代替固定来源。
- 下一步由唯一Merger等待T09终态与审查修复，保持受测产品冻结；support-only后继单独验证绑定，产品发现由唯一owner修复后重冻重验。

## 任务入口与依赖

- [T01 Hybrid 政策与有界预取复用](ceres2-local-cloud-integration-01-policy-hybrid-deadline.md)：技术已合入
- [T02 Canonical 商品召回与当前 Offer](ceres2-local-cloud-integration-02-canonical-shopping.md)：技术已合入
- [T03 同 Pi 原生完成与混合引用](ceres2-local-cloud-integration-03-native-finish-mixed-refs.md)：技术已合入
- [T04 可选审校过程消息与 SSE](ceres2-local-cloud-integration-04-reviewed-interim-sse.md)：技术已合入
- [T05 本地界面适配新入口与协议](ceres2-local-cloud-integration-05-integrated-ui.md)：技术已合入；浏览器BLOCKED
- [T06 显式 GraphRAG 与规范菜谱事实](ceres2-local-cloud-integration-06-explicit-graphrag.md)：A/B技术已合入
- [T07 售后数量照片与工单证据范围](ceres2-local-cloud-integration-07-aftersales-ticket-evidence.md)：核心/Mercury技术已合入
- [T08 统一评测事件与运行版本](ceres2-local-cloud-integration-08-evaluation-provenance.md)：A/B技术已合入，最终同版验证中
- [T09 同版回归两轴审查与交接](ceres2-local-cloud-integration-09-integrated-verification.md)：冻结81b02f9最终验证/审查中

原业务依赖保留：T01→T02/T03，T03→T04，T02/T04/T07→T05，T02/T04→T06，T05/T06/T07→T08，T08→T09。工程实施已批准拆同票阶段：T06-A backend先行、B等runtime；T08-A导出先行、B等T06交回runtime。阶段先行不提前完成整票验收。历史分配/恢复过程见[时序记录](../logs/ceres2-local-cloud-integration-20261007-history.md)，不再作为实时指令。

## 当前唯一所有权

- Merger：`resume_integration_merger`。独占canonical、TASK/spec/恢复说明/交接/发布allowlist；不实现产品或运行验证。
- Tester：`resume_integration_tester`。独占安装、测试、lint、typecheck、build、受控服务/浏览器执行。Standards/Spec分别独立只读；最终审查按固定pin。
- T05：`prepare_integrated_frontend`，frontend全目录及独立DOM/HTTP用例。不得写Pi/backend共享文件。
- T08-B：`prepare_evaluation_integration`，Pi/runtime/Prompt、evaluation、guide_run_service，以及主会话追加分配的knowledge_service观测和api/guide.py早期失败证据保留。后两者只在明确需求范围，不能改返回/权限/deadline。navigation_service未需要写入；DB/model/migration/schema/conftest未转交。
- 已完成的T01/T02/T03/T04/T06/T07产品文件冻结；新问题由主会话分配唯一修复owner。共享DB/model/migration仍不得并写，需明确逐文件交接。
- 浏览器fixture源由独立support owner维护；已固定源码选择性纳入 `work/local-cloud-integration/browser-support`，Tester验证最终路径，不能含DB、日志或嵌套仓库。
- 旧bootstrap/workers名称只存在历史记录，不是活跃句柄，不要唤醒重复Merger/Tester。实施者向当前Merger和主协调交付。

## 关键合同和边界

Python是身份/事实/授权/确认/事务唯一权威，Node真实Pi管售前、Python真实LangGraph管售后；所有商品金额/库存/交易/退款/履约均模拟。原main、原53项dirty、`.env`、运行DB/session/checkpoint/index与holdout不读取/覆盖/迁入；不shell push/main merge/部署/真实provider调用。

实际基线Guide30秒，已批准改为本次处理15秒/5轮；直接Guide包含同步授权，独立导航预检和用户确认等待是另一请求边界，replay/reconnect不能重新计时。知识锁/启动/IO和全部实际调用消费同一绝对deadline与已有取消检查；普通产品HTTP自身建立一次预算。独立offline graph build使用显式有限正数预算，不冒充Guide调用。

T01静态五来源曾由Merger前置迁入，随后T02接管fixture；真实snapshot绑定实际来源/实现/索引版本。商品召回仍校验canonical条件和当前Offer。T06真实本地BGE公开开发集是检索证据，不代表真实图LLM、业务整轮时延或holdout质量。

技术门槛可以在明确保留外部浏览器阻塞的情况下继续；不得把“已合入/已发布/DOM通过”等同于“实际浏览器通过/整体验收”。T02 helper命名留一个非阻断P3，最终集中审查决定是否修复；若修复需统一调用方并重验。

## 已核实来源与发布

Git来源计数：baseline→incoming340路径；local-start→incoming224路径，其中backend/runtime/frontend/data fixtures63路径，进一步app/src/fixtures53路径。此53不是原工作树53dirty。[来源清单](../work/local-cloud-integration/incoming-changed-paths.txt)、[63路径](../work/local-cloud-integration/incoming-code-and-fixture-paths.txt)、[baseline对比](../work/local-cloud-integration/baseline-incoming-changed-paths.txt)。

最后正式读回映射：local `a835bd411f96285f15d67a75dd0c0abfdb1d1640` → remote `7eaeda0cc1e27b96baaf235a1fede1ad47261a79`，tree `66387dff204483a016931cfbb75cbe42f00f4100`，[回执](../work/local-cloud-integration/t06b-t08a-integration-publication-receipt.json)。后继canonical变更尚未发布；下一正式payload从此远端基线生成。

T05独立WIP `58db7fef475bab34e4c5b53bc3a1e4ba6408dfbb` 对应local `a9c9c5`，不是canonical或最终版本。[WIP回执](../work/local-cloud-integration/t05-wip-publication-receipt.json)。后续本地T05候选与备份区分，不凭旧receipt声称新source已上传。

逐票的原始RED/GREEN、修复审查、源码等价与postmerge证据在各票链接，数字不跨pin相加。最终交接准备稿见[README](../README.md)和[本轮交接](../docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)；最终pin与门槛尚未填写就保持PENDING，不继承旧558/backend或旧live结果。

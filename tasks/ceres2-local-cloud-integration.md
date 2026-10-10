# Ceres2 local-cloud integration

- 状态：待验收（九票技术实现/受控验证/两轴闭环完成；浏览器BLOCKED、真实provider/本人验收未完成）
- 主责任：主会话；集成分支唯一写入者为 Merger
- Spec：[规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- Workspace：[恢复说明](../CERES2-WORKSPACE.md)
- Baseline：`37c98400e7152b89e4a58f02fff3bceaa73b0eac`
- Incoming：`6734c7fe79e670df2dae12b065dcc49c0b10a307`，只读 frozen tag `ceres2-incoming-20261007-frozen`
- Local start：`b118dbea3852026c6a04c790b1e27df67c3c9c18`
- Common ancestor：`4bed9c891261e382122d424825b649989ea92c92`

## 当前状态与下一步（唯一实时摘要）

- T01—T09技术实现及阶段/最终审查修复已完成，最终产品固定 `f963017587b3eab30965ffcd3aab90fcc3852f3e`。backend/runtime/frontend/data与受测修复`3a9fede`零差异；后继文档/证据提交不改变产品。
- 唯一backend全量在`81b02f9`：746 passed /5 skipped；5个skip由同pin生产锁知识环境的官方库24例与真实BGE4例补证。最终狭窄修复`3a9fede`183受影响例、合入`f963017`4例与build单独通过。不得相加或说最终pin再次全量。
- Pi typecheck/build、frontend strictTS/build、相关DOM、实际Pi/LangGraph受控HTTP与21请求模拟journey通过。完整baseline两轴及产品/支持工具修复delta闭环，无未关闭技术审查发现。
- 实际Chromium/官方CUA仍BLOCKED：IPC权限与跨执行环境host拒连，未进入UI。真实provider/真实图LLM质量、用户本人验收NOT RUN；不把DOM/HTTP或发布当作这些门槛通过。
- 支持工具仅按固定源码选择性纳入；cleanupP2在`8e6be36`修复，最终仓库路径4例验证通过。没有嵌套Git、DB、索引、模型、原始日志或凭据入库。
- 下一步：主会话读回最终独立分支SHA/tree并提供发布回执；用户按[本地交接](../docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)在独立worktree补真实浏览器/获准provider/本人验收，不动原main或53项dirty。各票保持“待验收”，不虚报整体已验收。

完整来源、门槛、skip映射和两轴链接：[最终技术报告](../work/local-cloud-integration/t09/FINAL-VERIFICATION.md)、[源码映射](../work/local-cloud-integration/t09/final-source-map.json)、[验证历史](../work/local-cloud-integration/t09/verification-history.json)。

## 任务入口与依赖

- [T01 Hybrid 政策与有界预取复用](ceres2-local-cloud-integration-01-policy-hybrid-deadline.md)：技术完成，剩余验收按最终报告
- [T02 Canonical 商品召回与当前 Offer](ceres2-local-cloud-integration-02-canonical-shopping.md)：技术完成，剩余验收按最终报告
- [T03 同 Pi 原生完成与混合引用](ceres2-local-cloud-integration-03-native-finish-mixed-refs.md)：技术完成，剩余验收按最终报告
- [T04 可选审校过程消息与 SSE](ceres2-local-cloud-integration-04-reviewed-interim-sse.md)：技术完成，剩余验收按最终报告
- [T05 本地界面适配新入口与协议](ceres2-local-cloud-integration-05-integrated-ui.md)：技术完成，剩余验收按最终报告
- [T06 显式 GraphRAG 与规范菜谱事实](ceres2-local-cloud-integration-06-explicit-graphrag.md)：技术完成，剩余验收按最终报告
- [T07 售后数量照片与工单证据范围](ceres2-local-cloud-integration-07-aftersales-ticket-evidence.md)：技术完成，剩余验收按最终报告
- [T08 统一评测事件与运行版本](ceres2-local-cloud-integration-08-evaluation-provenance.md)：技术完成，剩余验收按最终报告
- [T09 同版回归两轴审查与交接](ceres2-local-cloud-integration-09-integrated-verification.md)：技术完成，剩余验收按最终报告

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

技术门槛可以在明确保留外部浏览器阻塞的情况下继续；不得把“已合入/已发布/DOM通过”等同于“实际浏览器通过/整体验收”。T02先前非阻断helper命名P3，已在最终集中修复`3a9fede`准确重命名并受影响复验，P3关闭。

## 已核实来源与发布

Git来源计数：baseline→incoming340路径；local-start→incoming224路径，其中backend/runtime/frontend/data fixtures63路径，进一步app/src/fixtures53路径。此53不是原工作树53dirty。[来源清单](../work/local-cloud-integration/incoming-changed-paths.txt)、[63路径](../work/local-cloud-integration/incoming-code-and-fixture-paths.txt)、[baseline对比](../work/local-cloud-integration/baseline-incoming-changed-paths.txt)。

最新已读回候选checkpoint：local `4e728c7fa9ede8d3ddaec593b4f2f5c01a4811a5` → remote `f268d48cbdeea512f866404be6413a77a1ae9c7b`，tree `388b6dbe136748d20f0c8b5051e3c7d10c94489c`，[回执](../work/local-cloud-integration/complete-candidate-checkpoint-publication-receipt.json)。它保存修复前候选，不是最终已验收发布。后继最终产品/文档待主会话发布读回，最终完整SHA/tree以随交付提供的最终回执为准，不用旧checkpoint冒充。

T05独立WIP `58db7fef475bab34e4c5b53bc3a1e4ba6408dfbb` 对应local `a9c9c5`，不是canonical或最终版本。[WIP回执](../work/local-cloud-integration/t05-wip-publication-receipt.json)。后续本地T05候选与备份区分，不凭旧receipt声称新source已上传。

逐票的原始RED/GREEN、修复审查、源码等价与postmerge证据在各票链接，数字不跨pin相加。最终交接准备稿见[README](../README.md)和[本轮交接](../docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)；最终技术门槛已按精确pin填写，浏览器/真实/本人项仍未验；不继承旧558/backend或旧live结果。

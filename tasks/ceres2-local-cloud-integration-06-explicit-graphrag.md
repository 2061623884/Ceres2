# T06：显式 GraphRAG 与规范菜谱事实

- 状态：进行中（A已技术合入；T04已放行，B阶段接管Pi/runtime）
- 负责人：knowledge/runtime owner (T04→T06 交接)；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T02 Canonical 商品召回与当前 Offer](ceres2-local-cloud-integration-02-canonical-shopping.md)；[T04 可选审校过程消息与 SSE](ceres2-local-cloud-integration-04-reviewed-interim-sse.md)

## What to build / 合同

官方 GraphRAG 显式工具与 deterministic recipe_facts 共存；基准用量/必需食材来自规范事实；未知调料数量保持未知；模型选择/规范关系区分，GraphRAG 调用也官方 hostname thinking disabled、受剩余预算约束。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] 显式图查询 vs 普通 recipe_facts；规范用量和 unknown；缺索引/图失败；当前商品证据、官方/非官方 transport；真实 GraphRAG 和 BGE 只有 Tester 授权环境实际执行才记通过。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

T02 已技术放行，按下述后端阶段执行；Pi/runtime 阶段仍等待 T04。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。


## 工程依赖细化：同票两阶段

主会话批准 T06-A 在 T02 技术放行后先实施/验证，不新增任务票、不跳过整票验收。绑定 prepare_recipe_graph_integration 为 backend-only owner，基线取 canonical `d9cbb180380515d5d10d0b76fc1bbba299db7385` 或其后 docs-only 后继。

- A 阶段独占：backend/app/knowledge/ 下 graph/providers/CLI/worker 及其实际调用需要的 core 变更、backend/app/services/knowledge_service.py、backend/app/services/dish_service.py、独立新增 T06 测试。独立知识 requirements/lock 如确需修改，由此 owner 提需求、Tester 执行锁定/安装；业务 requirements/lock 不在范围。
- T01 已完成且当前无人写 knowledge 文件，故此接管不与 T04 并写。保留完整 hybrid/policy source/version/deadline 合同；不能照搬 incoming 无界锁/30秒 fallback。现有 Pi 已调用 DishService(self.catalog)，后端菜谱检索从实际 catalog.deadline/should_stop 继承请求预算，不改变确定性 recipe facts 或提前隐式执行图查询。
- A 阶段可从公开 CLI/服务合同验证显式 Local/Global 图查询及 provider wire、canonical facts/模型选择来源分离、缺索引/错误/取消与期限、当前商品证据。只有 Tester 实际运行的依赖/图路径才算验证，不以 stub 宣称真实 GraphRAG/BGE通过。
- A 阶段禁止修改 runtime/ 全目录、pi_product_runtime.py、pi_product_turn_service.py、Guide schema/API、Prompt/experience、conftest.py、DB/model/migration、frontend、fixture 和已由其他 owner 持有的文件。若真实 caller 需要共享接口改动，先交接，不并发改 hunk。
- B 阶段必须等 T04 放行并明确转交 Pi/runtime 后，才能注册工具、整合 recipe/graph refs、Prompt与最终消息/事件。A 阶段不单独释放 T05/T08，也不使 T06 整票完成。A 的提交/文件清单交接后做同版组合验证与两轴审查。

### A 阶段实际发现追加所有权（2026-10-07）

主会话另行授权本 owner 修改 `backend/app/knowledge/bge.py`：锁定 huggingface-hub 1.33 对部分本地快照的完整性判断使真实 BGE 验证在编码前失败。仅为固定 revision 的六个所需文件加入明确 `allow_patterns`，保留 local_files_only、token=False、trust_remote_code=False，不下载重复模型格式。此改动必须改变 implementation 指纹；Tester 重建实际 hybrid 索引并验证旧指纹拒绝，不放松来源校验。


## T06-A 技术合入，B 阶段仍开放

A 阶段 `14b6ad1` 无冲突合入 `3069728`，产品目录与交付 pin 零差异；production 与两轴最终清除的 `26028b3` 相同，后继仅加 opt-in BGE helper。原 CLI deadline、异常原因和未调用 public override 的 P2 已修复并复审关闭。

Tester 各固定 pin：`2ad494c` 官方库受控41例，`26028b3` CLI诊断增量7例；`14b6ad1` 实际固定本地 BGE helper 4例，包括18个公开开发检索例、stale指纹拒绝，另有默认线程 cold/warm 检查1例。默认首次查询9.428s/后续0.085s是局部知识检索，不是LLM整轮时延。不同pin/范围不得求和冒充同版全量。固定 detached `3069728` A postmerge47例/6.63s通过，无源码/harness漂移；A技术门槛已关闭。

[证据摘要](../work/local-cloud-integration/t06a/verification-summary.json)、[源码等价](../work/local-cloud-integration/t06a/source-equivalence.json)。真实embedding验证不替代真实LLM、图模型质量、Pi接线、前端或用户本人验收。T06-B仍等待T04正式交接runtime。

最终测试-only审查与source binding已保存；fresh索引副本植入旧源码hash证明stale拒绝，不声称旧历史索引实际成功。[固定postmerge](../work/local-cloud-integration/t06a/postmerge-minimum.json)、[最终绑定](../work/local-cloud-integration/t06a/final-source-binding.json)。

T04已在canonical `e0f57cd` 通过37例共存postmerge与runtime build；T06-B正式接管runtime/Prompt/Pi协议与独立tests。frontend归T05，不并写；shared conftest/DB/schema变更仍须逐文件协调。B候选完成后同版验证、两轴审查及整票验收仍必须独立完成。

# T01：Hybrid 政策与有界预取复用

- 状态：待开始
- 负责人：design_policy_retrieval_bridge（runtime-policy owner）；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：无（可开始）

## What to build / 合同

保留 Coco/Momo 入口和 policy_scope；source version/name 与实际 fixture、索引版本一致；成功/空复用及失败补查；排锁和 worker I/O 全部消费本轮确认的 15 秒总预算。首票包含知识模块实际需要的基础依赖与合同，不提前铺未调用抽象。

## 验收

- [ ] 以上端到端业务合同完整实现，保留来源与安全边界。
- [ ] 现有 judge policy public/reuse/safety：prefetch 命中/空/异常、同范围复用、版本变化、多范围早期 refs；受控 worker 锁占用/慢读/取消不越 deadline。
- [ ] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [ ] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [ ] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

尚未实现；等待主会话分配工作树及唯一文件所有权。本票是可独立演示/验证的业务切片，不允许只搬文件并宣称完成。Tester 和两轴审查证据由主会话在收到后登记；历史来源报告不能代替本票结果。

## 已确认的来源合同细化

source_snapshot 返回 source_name/source_version/source_revision/index_revision；fixture SHA 与 canonical index manifest hash 进入身份，manifest 的五份静态语料文件哈希及模型/tokenizer/relevance 版本必须匹配实际实现。search_policies 使用 snapshot、共享绝对 monotonic deadline、should_stop；证据从索引命中文档读取而非另读新文本。worker 验证 expected index_revision，响应后复核 fixture，失效不铸 ref。缺索引/依赖或版本失配明确失败，无词面兜底；成功空结果可有合法 ref。Pi 以整个 snapshot 加原 query/category/scope/request 校验复用和最终引用。现有独立 catalog/API 调用可保留缺省 budget，Pi/Mercury run 必须传入共享 deadline。错误码 KNOWLEDGE_UNAVAILABLE/STALE/TIMEOUT/CANCELLED 区分原因；仅实际持锁且拥有查询者可以关闭其 worker。

本票拥有 Pi source/reuse 接线。Mercury tools/orders 文件由 T07 owner 持有，相关 deadline 接线需求交其串行写入。

实际基线 Guide API 为 30 秒（start_run/stream_turn），Mercury 为 15 秒。T01 独占 api/guide.py，公开 RED/GREEN 落实 Guide 30→15，异步/直接/预检/恢复沿同一 deadline；这是本轮行为修复，旧 30 秒时延结果不可作同条件对照。

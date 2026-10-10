# T01：Hybrid 政策与有界预取复用

- 状态：待验收（技术实现与受控门槛完成；实际浏览器/真实provider/用户本人验收未完成）
- 负责人：design_policy_retrieval_bridge（runtime-policy owner）；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：无（可开始）

## 最终当前结论（2026-10-07）

本票技术实现已进入最终产品 `f963017587b3eab30965ffcd3aab90fcc3852f3e`，受控验证/两轴修复闭环见[最终报告](../work/local-cloud-integration/t09/FINAL-VERIFICATION.md)。全量746通过/5跳过属于`81b02f9`；同版知识环境补齐跳过项，最终狭窄修复183例及合入4例另行绑定，不声称最终pin重新全量。实际浏览器BLOCKED、真实provider/用户本人验收NOT RUN，不能把技术完成等同于整体验收。

以下阶段记录按各自固定pin保留，旧“待实现/待交接”等描述属于历史过程，不推翻本节当前结论。

## What to build / 合同

保留 Coco/Momo 入口和 policy_scope；source version/name 与实际 fixture、索引版本一致；成功/空复用及失败补查；排锁和 worker I/O 全部消费本轮确认的 15 秒总预算。首票包含知识模块实际需要的基础依赖与合同，不提前铺未调用抽象。

## 验收

- [x] 以上端到端业务合同完整实现，保留来源与安全边界。
- [x] 现有 judge policy public/reuse/safety：prefetch 命中/空/异常、同范围复用、版本变化、多范围早期 refs；受控 worker 锁占用/慢读/取消不越 deadline。
- [x] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [x] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [x] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

本票受控技术门槛已通过并合入，见下文技术交付。固定 canonical ccf272b postmerge 最小检查18 passed，另有 runtime build 与 Node guard 2 passed，无源码/harness 漂移；真实 BGE 与最终整体验收仍开放。

## 已确认的来源合同细化

source_snapshot 返回 source_name/source_version/source_revision/index_revision；fixture SHA 与 canonical index manifest hash 进入身份，manifest 的五份静态语料文件哈希及模型/tokenizer/relevance 版本必须匹配实际实现。search_policies 使用 snapshot、共享绝对 monotonic deadline、should_stop；证据从索引命中文档读取而非另读新文本。worker 验证 expected index_revision，响应后复核 fixture，失效不铸 ref。缺索引/依赖或版本失配明确失败，无词面兜底；成功空结果可有合法 ref。Pi 以整个 snapshot 加原 query/category/scope/request 校验复用和最终引用。现有独立 catalog/API 调用可保留缺省 budget，Pi/Mercury run 必须传入共享 deadline。错误码 KNOWLEDGE_UNAVAILABLE/STALE/TIMEOUT/CANCELLED 区分原因；仅实际持锁且拥有查询者可以关闭其 worker。

本票拥有 Pi source/reuse 接线。Mercury tools/orders 文件由 T07 owner 持有，相关 deadline 接线需求交其串行写入。

实际基线 Guide API 为 30 秒（start_run/stream_turn），Mercury 为 15 秒。T01 独占 api/guide.py，公开 RED/GREEN 落实 Guide 30→15，异步/直接/预检/恢复沿同一 deadline；这是本轮行为修复，旧 30 秒时延结果不可作同条件对照。

## 技术交付

产品 `6ba93b2b66a004fdfae1d7106d5f29a0512ddfd6` 无冲突合入 `3ecf15e8fbdb9099a30e3c16793f70251a8dfa3c`；backend/runtime/frontend/data 与受测 pin 零路径差异。Tester 同 pin 165 affected、runtime typecheck/build、实际 Node guard 2 passed，无漂移；两轴 correction review clear。[验证](../work/local-cloud-integration/t01/verification.md)。T02/T03 可接管依赖；T07 Mercury 接线由其 owner 后补，不使本票互等。真实本地 BGE 权重/质量未验证，最终集成和用户验收不继承这些受控结果。

直接 Guide15秒包含同步授权；单独导航预检/用户确认是独立边界，既有run replay/reconnect不得重新计时。

- [ ] 剩余实际浏览器、获准的真实provider与用户本人验收按最终报告独立完成；不由受控结果自动勾选。

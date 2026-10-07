# 03：同范围复用与安全补查

- 状态：待验收（2026-10-07：云端专项与核心两轴审查已释放；04 同版全量和外部门槛仍开放）
- 拆分：已批准；功能依赖保持 01 → 02 → 03 → 04
- 执行授权：2026-10-07 用户已授权从 GitHub 基线重新 implement-spec／TDD／Agent Team 实施、可追溯提交及分支推送；前置功能与专职 Tester 门槛保留。
- 负责人：03 唯一实现者接手工作树 `../worktrees/03-query-reuse`、分支 `ceres2/judge-prefetch-03-query-reuse-20261007`；专职 Tester 执行所有验证命令，Standards／Spec 独立只读审查。共享文件按 [执行决定](../docs/REBUILD-DECISIONS.md#4-写入所有权与可并行支持项) 交接。
- 上级：[总 TASK](ceres2-judge-prefetch.md)；依据：[规格](../docs/plans/ceres2-judge-prefetch-spec.md)。本票不得继承旧版通过成绩。

## 2026-10-07 当前执行差异

- [执行决定与固定服务端契约](../docs/REBUILD-DECISIONS.md) 对本票生效：最新实施授权取代原草案“未授权”文字，原业务、安全与 fixture 要求继续有效。
- 前端实现与前端文件修改由用户本地负责；下列 typed UI／DOM／真实浏览器验收项保留为本地交接，云端负责其公开 typed action／HTTP／SSE 契约与受控行为。未验页面不得勾选通过。
- 前票云端契约与受控证据交付后可推进依赖；整体端到端验收仍待同版前端证据，不因负责人拆分而自动完成。
- 测试 seam 已由原规格批准，无需重新访谈；所有执行命令由 Tester 负责，功能修改使用独立 worktree、单一文件所有者。

## What to build

预检索后 Pi 原样查询同一范围时，执行侧返回本请求已有证据，不重复实际检索。新增政策子问题、条件变化、证据不足或此前失败仍可补查；可复用空结果只说明该范围无匹配。补查后原范围内仍适用的早期引用继续有效，多范围回答完整且来源可追溯。权限、请求、版本、范围、取消和回执保护在确定性服务生效，不依赖 prompt-only 或全局 rag_done。

## Blocked by

[02 政策预检索与同 Pi 回答](ceres2-judge-prefetch-02-policy-evidence.md)：需要实际注入、证据注册及错误状态，不以假想缓存独立建设。交付阻塞 [04 同版集成与调用对照](ceres2-judge-prefetch-04-candidate-evidence.md)。2026-10-07 前票云端门槛已完成并经两轴复审，详见 02 最终同版证据；外部验收仍开放。

## 数据与 fixture

隔离两个 owner 与多个 session／request；同一个请求重复“退货政策”，另一查询“配送进度规则”，变更类别或条件；成功、空、部分、首次错误随后补查；来源 V1／V2、有效早期 ref／最后 ref／伪造 ref／跨请求 ref。增加同批重复，实际调度存在并发时加并发 fixture；模型上下文裁剪后再次使用证据、停止／恢复、请求重放、已确认加购或售后回执分别验证。

## 测试与验收

- [ ] 预取后同请求同范围调用仅有一次成功的实际检索；执行侧复用而非仅靠提示避免调用，同批／适用并发不穿透重复查库。
- [ ] 范围由可信身份、请求、实际查询／类别／有效条件及知识版本判定；规范化不误合并不同子问题，无跨轮／跨请求缓存平台。
- [ ] 新子问题、条件变更、部分证据不足及先前失败能够补查；无匹配与错误不同，失败不锁死工具，也无无界或隐藏重试。
- [ ] 多范围结果保留各自有效引用，早期适用证据不会被“仅最后 ref 有效”淘汰；版本失效、伪造、跨 owner／request 的引用被拒绝，不能捏造全面覆盖。
- [ ] 模型上下文丢失材料时可重新取得已有证据内容而非死指针；返回证据对应真实调用时才使用配对 tool result。
- [ ] 完整原文、购物条件及政策子问题继续被处理；重放／刷新／停止恢复不重跑已完成业务，不把来源或导航权限变成写入授权。
- [ ] 观测分别呈现实际检索、复用、补查、工具调用、Pi 轮数；报告不声称检索去重必然省 LLM 轮次或费用；全部业务由本票闭合。

## Ownership／交接

本票接收 02 的证据／引用契约及共享入口的单一修改权，独占复用守卫、范围身份与版本处理、多引用结果和对应 fixture。只按实际请求生命周期最小落实，不新增通用缓存管理器或无依据数据迁移。给 04 交付完整候选、行为用例、调用计数契约与已知限制；04 不负责补本票功能。

## 2026-10-07 中间源码保全

首个 03 WIP 已发布核实：本地 `2cdc88f9400ccf5fe8a86cb55892601fa8bf4065` 对应远端 `d8ac3ab627cf56560b13be6e2a7e436865bd02c5`，精确 tree 均为 `12bf09d9865fe2320b1113d215997aaab240fdd0`，独立分支 `ceres2/judge-prefetch-reuse-wip-20261007`；[映射](../work/judge-prefetch/publication-query-reuse-wip.json)。六项相关受控用例通过且 247 个 source hash／harness 无漂移，仅证明该时点精确重复复用、完整证据返回、独立 reuse 事件和早期／过期来源引用行为；多引用、最终安全回归与独立审查仍待完成。不合入已释放集成，不表示 03 验收或 04 依赖释放。

## 2026-10-07 最终云端专项交付

- 产品／测试提交 `35a30fab775764cfcbc01ee84599fb450b6411bd` 已合并为 `d6a40886926bf203b53c52db27d2177b1b3dcb80`；248 个 source hash 和最终 harness 与五项修复后门槛完全一致，提交／合并／独立 04 worktree 均未改变；[冻结证据](../work/judge-prefetch-rebuild/03-query-reuse-final-source.json)。
- [Tester 报告](../work/judge-prefetch-rebuild/03-query-reuse-verification.md)：**152** 项受控专项通过，含重叠的 **34** 个复用／安全用例；依赖、Pi typecheck/build 与独立 guard proof 通过。没有另跑完整 03 backend；同版全量统一在 04 执行一次。旧 151 项和 33 项属于会计修复前候选，保留为历史。
- 独立[核心 Standards 复审](../work/judge-prefetch-rebuild/reviews/standards-core-final-rereview.md)无新问题；[核心 Spec 复审](../work/judge-prefetch-rebuild/reviews/spec-core-final-rereview.md)闭合 256-event 尾部丢失完整计数 P2。
- 已交付可信请求内精确 query/category/来源版本复用、成功与空结果完整材料恢复、失败仍可补查、所有显式单／多 ref 校验、早期有效引用与多范围宿主事实。没有跨请求缓存平台、模糊 query 合并、并发架构或增加预算。
- 标准 result／receipt 的 runtime_summary 与有界 runtime_events 分离，固定计数为 policy_lookups、policy_lookup_outcomes、policy_tool_lookups、policy_reuses、tool_starts、primary_pi_turns，另保留实际 policy_judgment 与 events_truncated。tool-origin 是所有实际工具来源查询，不能一律称额外补查；SDK starts／turns 不是 HTTP、成功执行、tokens 或费用。硬错误可无 summary，缺值必须未知。
- 04 接收同版核心并完成唯一全量验证；未完成的比较 runner／文档、真实 provider、用户前端／浏览器与本人验收不由本票代替。

## 下一步与证据

从 02 集成提交 `7ea06a343f95043cc5c1948ef74fc139e0de2280` 的同一源码及后续交付文档接手。继承 current-request policy_scope、真实 evidence registry／attempts、query/category/source version、lookup outcome/coverage、规则判断／实际 lookup 观测；保留错误 attempt 无 ref 与所有晚到 freshness/cancel/deadline 守卫。这些 02 继承限制已在上述 03 精确候选中按本票契约解除。专职 Tester 已沿公开行为验证实际计数与读回；04 继续同版全量及其独立交付边界。

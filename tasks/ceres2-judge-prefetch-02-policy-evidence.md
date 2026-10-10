# 02：政策预检索与同 Pi 回答

- 状态：待验收（2026-10-07：云端技术门槛已释放；真实 provider、用户本地前端／浏览器与本人验收仍开放）
- 拆分：已批准；功能依赖保持 01 → 02 → 03 → 04
- 执行授权：2026-10-07 用户已授权从 GitHub 基线重新 implement-spec／TDD／Agent Team 实施、可追溯提交及分支推送；前置功能与专职 Tester 门槛保留。
- 负责人：02 唯一实现者接手工作树 `../worktrees/02-policy-evidence`、分支 `ceres2/judge-prefetch-02-policy-evidence-20261007`；专职 Tester 执行所有验证命令，Standards／Spec 独立只读审查。共享文件按 [执行决定](../docs/REBUILD-DECISIONS.md#4-写入所有权与可并行支持项) 交接。
- 上级：[总 TASK](ceres2-judge-prefetch.md)；依据：[规格](../docs/plans/ceres2-judge-prefetch-spec.md)。本票不得继承旧版通过成绩。

## 2026-10-07 当前执行差异

- [执行决定与固定服务端契约](../docs/REBUILD-DECISIONS.md) 对本票生效：最新实施授权取代原草案“未授权”文字，原业务、安全与 fixture 要求继续有效。
- 前端实现与前端文件修改由用户本地负责；下列 typed UI／DOM／真实浏览器验收项保留为本地交接，云端负责其公开 typed action／HTTP／SSE 契约与受控行为。未验页面不得勾选通过。
- 前票云端契约与受控证据交付后可推进依赖；整体端到端验收仍待同版前端证据，不因负责人拆分而自动完成。
- 测试 seam 已由原规格批准，无需重新访谈；所有执行命令由 Tester 负责，功能修改使用独立 worktree、单一文件所有者。

## What to build

留在可可的完整文字经过内部政策判断；yes 预查既有静态四条政策，再将原文、实际证据、条件、来源版本及状态提供给同一个 Pi。no／不确定／超时／错误进入普通 Pi 并保留工具。无匹配明确未知，检索异常单独记录，部分证据不冒充全面覆盖。纯政策无须订单；混合购物＋政策完整处理，两部分各有真实事实引用；不新增 EvidenceAnswerer 或提前执行购物／售后写入。

工程提案：yes 后以完整原始文字作为 query、category 不指定，直接使用既有检索；不添加参数抽取 judge。实际参数随证据交给 Pi，后续更明确的子问题可补查。政策判断／预取与 Pi 建议共享从进入可可处理起算的既有运行阶段 deadline，不逐阶段重置；入口 Kev 保持独立超时，但从请求接纳起的端到端测量必须包含它。基线 UI 的独立 /routes 不包含在后续 Pi deadline 内；直接 Guide 准入在 authorize_text 前建 deadline，可能包含内部判断，须分别记录实际边界。阶段转换前检查取消与剩余时间，运行截止不再由 fallback 启动 Pi。

## Blocked by

[01 可可入口与按钮返回](ceres2-judge-prefetch-01-role-entry.md)：需要其可可准入与安全首次上下文，避免预取被旧能力裁剪丢失。交付阻塞 [03 同范围复用与安全补查](ceres2-judge-prefetch-03-query-reuse.md)。2026-10-07 前票云端技术门槛已交付，详见 01 最终验证与两轴复审；用户本地外部验收仍开放。

## 数据与 fixture

沿用现有四条静态政策的 ID、原文及版本，购物使用隔离的低糖饮品及数量条件。固定“退货条件”“选低糖饮品并问退货条件”“你好”“火星定制条款”；政策判断 yes/no/uncertain/timeout/error；检索命中、空、异常与仅覆盖其中一个子问题。捕获实际发给 Pi 的消息和工具目录；预取不是伪造模型 tool call。

## 测试与验收

- [ ] 从公开可可文字到 SSE／UI 完成纯政策和购物＋政策旅程，完整原文及条件进入同一 Pi，结果不遗漏任一子请求；混合 fixture 核对实际预取 query 等于完整原文且未擅填 category。
- [ ] yes 才执行预检索；no／uncertain／timeout／error 保留普通 Pi 政策能力，无隐藏重试或额外分类器；局部超时只有整轮仍有效才继续，取消／截止不再启动后续模型或发布旧结果。Momo 与 typed 按钮不增加政策 Kev。
- [ ] Pi 实际模型输入可见证据正文、查询范围、来源与版本，不是宿主 raw state 自证注入；来源文本不能改变系统指令或业务权限。
- [ ] 预取取得真实 policy_ref 并登记 Python 当前请求证据注册表，同一引用及正文进入模型上下文，在本请求中可合法生成政策结果；事实展示保留限制、未知、模拟和未提交含义。无订单也能查询，不能凭政策宣称具体订单符合资格。
- [ ] 无匹配／部分／异常可观察且不同；异常不当空集，缺证据不编造政策，已有政策工具可用于补查；原文购物部分继续完整处理。
- [ ] 不提前登记购物意图或消耗授权；重复确认／恢复不产生第二次业务写入；相关旧共享政策与购物确认回归通过。
- [ ] 每个小判断的结果、耗时、失败原因和规则版本可查；不可得用量标未知。本票完整实现云端所属行为与全部失败路径，不把业务补齐留给 04；UI 由用户本地负责，按本票固定契约交接并保留待验收项。

## Ownership／交接

接收 01 的初始上下文契约后，本票独占可可政策判断、预取、上下文注入、证据注册、Prompt 及配套 fixture 的最小共享改动。检索仍复用现有来源，不重写库存筛选。向 03 交付真实证据与引用生命周期、失败分类及可用调用计数；如导航回归需修复，由主会话协调 01 负责人而非并行改同一入口。

## 2026-10-07 中间源码保全

政策 yes 预取与 no／uncertain／timeout／error 回退的中间版本已独立保存：本地 `4b3533cc7abdf4f4d3d776dfbce923fa2e3faf7b` 对应远端 `b8922a8eaf08fadc973ff75adc3abc5ede346f0d`，精确 tree 均为 `ad0a82d362c2f74fff87b4f87a24988bbc732d18`，分支 `ceres2/judge-prefetch-policy-wip-20261007`；[核实映射](../work/judge-prefetch/publication-policy-wip.json)。快照时 34 项相关受控测试通过且 245 个 source hash 无漂移，但检索错误／空／部分结果、完整混合呈现、晚到取消／deadline 守卫和最终审查仍未完成。该 WIP 不合入已释放集成，不表示 02 验收或 03 依赖释放；实现已继续。

后续同一 WIP 分支已 fast-forward 保存到远端 `b4ab956a2c4ddf823c4d9f354436ae9fbf8ddd38`，对应本地 `79d34be1037a5fd910fd49bdb735afbea99b17b0`，精确 tree 均为 `200b6b5c901660625233f3ff351604aee4fae923`；[第二快照映射](../work/judge-prefetch/publication-policy-wip-02.json)。该时点 19 项相关测试通过，覆盖 lookup／mixed projection 与晚到发布事务回滚；仍待 fresh-text 准备修正、最终安全／混合回归和独立审查，02 状态不升级，也不释放 03。

## 2026-10-07 最终云端交付

- 已发布核实：远端 `e434e1b5419dfadec9db65dea13b63974a9d701e` 对应本地交付 `0559d9ed17e65cb4f6f8dfab80b83152e6fe280e`，精确 tree 均为 `18b51049c0d847eed04fac3ec26ba36c4afe16fa`；[发布映射](../work/judge-prefetch/publication-policy-evidence-final.json)。
- 产品／测试提交 `0aaffb39549db2704c6c0c414e3819277023e7a6`，集成 merge `7ea06a343f95043cc5c1948ef74fc139e0de2280`。246 个源码文件及修复后的 harness hash 与五项最终门槛前后完全一致，提交／合并未改变；[源码映射](../work/judge-prefetch-rebuild/02-policy-evidence-final-source.json)。
- [Tester 报告](../work/judge-prefetch-rebuild/02-policy-evidence-verification.md)：完整 backend **524 passed**，其中重叠的政策专项 **44 passed**；另有两项 guard proof、Pi typecheck/build 和依赖检查通过。全套实际启动的 577 个 Node PID 均有 guard 加载记录，其中 541 个 Pi worker；旧 191 项预修复成绩保留为历史，不替代最终版本。
- 独立 [Standards 复审](../work/judge-prefetch-rebuild/reviews/standards-02-rereview.md)无新问题；[Spec 复审](../work/judge-prefetch-rebuild/reviews/spec-02-rereview.md)已闭合阻塞查询返回后的当前请求检查 P2。原发现／失败及红绿轨迹保留，不删除。
- 已交付完整原文且 category 为 None 的真实预取、当前请求真实 policy_ref 和来源／版本、同一 Pi 低信任输入、全部判断 fallback、空／部分／异常区别、合法 completed/waiting 主结果与政策／职责边界并存，以及当前请求／取消／deadline 和事务回滚保护。失败 attempt 无 policy_ref；宿主只能投影真实发生且未被同范围成功覆盖的失败，不能由模型宣称制造失败。
- 03 接收 policy_scope、policy_results、policy_attempts 与实际 query/category/source_version/outcome/coverage、policy_judgment／policy_lookup 观测契约。当前每次工具查询仍实际执行，引用仍限最后有效 ref；请求内去重／早期有效引用／多范围输出属于 03，不能从 02 通过推导已完成。前端与真实效果门槛继续开放。

## 下一步与证据

02 已从 01 同版集成接手并完成上述云端门槛。03 从当前已核实 source map 的集成提交接手；验证接缝继续使用公开 HTTP/SSE、模型实际输入、检索计数及权威业务读回。

01 移交的 waiting + policy + role boundary 及 general/history/memory 组合缺口已由本票同版公开 fixture 闭合；普通解释历史与宿主政策消息的来源分类分别保留。这不表示 03 多范围引用已完成。

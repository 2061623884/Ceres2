# 04：同版集成与调用对照

- 状态：待验收（2026-10-07：受控核心 558 backend、独立比较支持 22 项及核心／支持两轴审查已交付；真实对照、前端／浏览器和本人验收仍开放）
- 拆分：已批准；功能依赖保持 01 → 02 → 03 → 04
- 执行授权：2026-10-07 用户已授权从 GitHub 基线重新 implement-spec／TDD／Agent Team 实施、可追溯提交及分支推送；前置功能与专职 Tester 门槛保留。
- 负责人：集成者维护最终候选与文档；专职 Tester 使用独立工作树 `../worktrees/04-core-verification`、分支 `ceres2/judge-prefetch-04-core-20261007`；专职 Tester 执行所有验证命令，Standards／Spec 独立只读审查。共享文件按 [执行决定](../docs/REBUILD-DECISIONS.md#4-写入所有权与可并行支持项) 交接。
- 上级：[总 TASK](ceres2-judge-prefetch.md)；依据：[规格](../docs/plans/ceres2-judge-prefetch-spec.md)。本票不得继承旧版通过成绩。

## 2026-10-07 当前执行差异

- [执行决定与固定服务端契约](../docs/REBUILD-DECISIONS.md) 对本票生效：最新实施授权取代原草案“未授权”文字，原业务、安全与 fixture 要求继续有效。
- 前端实现与前端文件修改由用户本地负责；下列 typed UI／DOM／真实浏览器验收项保留为本地交接，云端负责其公开 typed action／HTTP／SSE 契约与受控行为。未验页面不得勾选通过。
- 前票云端契约与受控证据交付后可推进依赖；整体端到端验收仍待同版前端证据，不因负责人拆分而自动完成。
- 测试 seam 已由原规格批准，无需重新访谈；所有执行命令由 Tester 负责，功能修改使用独立 worktree、单一文件所有者。

## What to build

把 01–03 已完整交付的角色与政策旅程固定为一个候选，从公开入口、真实 Pi SDK 到业务读回验证，并保留用户本地 UI／浏览器的同版交接验收；用真实调用对照既有路径，说明正确性、轮数、时延与用量的实际变化。此票交付可信的综合验收与演示结果，不新增或兜底补齐前票业务。

## Blocked by

[03 同范围复用与安全补查](ceres2-judge-prefetch-03-query-reuse.md)，传递依赖 01／02 的完整业务交付。真实 provider／浏览器门槛需要安全配置与可用环境；缺失时对应层级阻塞，不换 mock 宣称实测。2026-10-07 实施与受控验证授权已具备；真实付费采样仍须核实既有配置与有限实验额度。

## 数据与 fixture

固定旧对照与新候选源码、未提交源码摘要、政策版本、商品／Offer、用例、Prompt、模型及配置。完整覆盖纯政策命中、混合请求、普通购物／聊天、切换确认、Momo 直达和按钮返回、判断故障、检索空／部分／异常、同范围复用及新问题补查。保留两 owner、请求重放、旧导航、已确认业务回执、失效 refs、停止／恢复的安全用例；生产数据与凭据不进入 fixture 或报告。

## 测试与验收

- [ ] 所有集成结果来自同一新候选；每次修复后重新冻结并重跑受影响及必要集成验证，不能拼接旧成功窗口。旧 0c752a2 的 426／37 不算新结果。
- [ ] 新角色／政策完整旅程及采购数量、约束、预算、确认加购、订单售后、人工责任、记忆／历史方案、停止恢复、结果先行流式回归通过；每项有具体外部行为与业务读回证据。
- [ ] 受控 provider／DOM、真实模型、真实浏览器、本人验收分别列状态，固定用户当前已批准的实际模型／provider 做配对验证，不指定或切换模型；未测项明确未知或阻塞。
- [ ] 实测前冻结有限用例、每例重复次数、调用顺序和整次实验时间或费用上限，并核实所需额度已获授权；未批准的数字或额度不自行补齐，到上限停止并保留未完成项。样本不足明确不支持稳定 P95 或可靠收益结论。
- [ ] 统一从请求接纳起算端到端时间，分别记录入口判断／政策判断／预取／Pi 阶段和各自真实截止边界，验证取消及剩余时间检查；入口独立超时与政策／Pi 共享运行预算分开报告，不把旧 Pi 时限说成已有端到端上限。不能把预取耗时排除在总延迟外或重置阶段预算。
- [ ] 真实样本逐例记录入口／政策判断、HTTP 请求、实际检索、复用与补查、Pi 轮数、首字／最终耗时、tokens／可得费用和失败原因；汇总 P50/P95 注明样本量与局限。没有 usage 或价格不填零。
- [ ] 旧路径与新完整路径在固定可比条件下比较；区分检索去重和少一次主模型选择轮，额外 judge 与上下文开销计入。不预设费用／延迟一定改善，不把质量退化换成性能通过。
- [ ] 独立 Standards／Spec 两轴审查完成并闭合有效发现；业务缺陷归还原票修复。报告保留失败、未测及用户决定事项，不宣称旧阶段其他外部验收自动完成。

## Ownership／交接

主会话冻结和维护候选，专职 Tester 独占执行全部测试／lint／typecheck／build 与实测，独立审查者只读。本票维护集成 fixture、版本清单和证据报告；共享 fixture 修改与所属业务票交接，禁止多个实现者同时写共享入口。无新业务功能所有权。

## 2026-10-07 有界传输支持项

- 已集成局部支持提交 `4944f7ea5ec02f1443685e6665154347ba9540d8`，集成 merge `37f3ad88bdb7f1bf84aa83e0c78a9a67b6e2d3ea`。其产品源码与 Tester 冻结六文件及完整受控 source map 一致。 已发布远端 `d5aba692d2c5bc6756ac35b513b2904c08a6758b`，与本地里程碑 `820aa8c88c64abb0036dd55ba30cc43d8e858d7a` 的 tree `d75cefe23e8682a299b4ddb4ecc9db8761704650` 完全一致；[发布映射](../work/judge-prefetch/publication-thinking-five-paths.json)。
- [专职 Tester 报告](../work/judge-prefetch-rebuild/thinking-transport-verification.md)：五条实际请求路径（Momo、提取、Dream、结果表达及表达 validator）在官方主机发送关闭 thinking 字段；非官方主机及相似后缀保持字段不存在。18/18 专项／既有 provider 用例、12/12 相关回归、Pi typecheck/build 通过；各 RED 失败保留。
- 上述五路径提交未修改 `worker.ts`。后续 01 已串行接入主 Pi 及其 validator，修复提交 `9f2eff1265c373736cc5f8683c8ccaa680959c30`／集成提交 `46f3fcf47d544e0c0ecead0abc13cb23d63a38b8` 的最终 149 专项和 480 完整 backend 套件重新验证七条路径，Pi typecheck/build 通过；[同版报告](../work/judge-prefetch-rebuild/01-role-entry-verification.md)。01 两轴审查已闭合，但不表示 04 业务集成、真实模型或用户前端验收完成。
- 此支持项不释放 04 的 03 前置依赖，也不代表 01–04 完成；模型、原输出额度与前端未改。

## 2026-10-07 最终核心冻结与范围拆分

核心冻结提交 `d6a40886926bf203b53c52db27d2177b1b3dcb80`，tree `2fad3a1c8e74593dc19ee929211be0d35a323938`。独立 04 worktree 的全部 248 个源码文件及已验证 guard/harness 与最终 03 scoped 候选完全一致；03 的 152 项专项不是最终全量成绩。本票在该冻结核心上只运行一次完整 backend，现已 **558 passed**，738.36 秒 pytest／756.438 秒 capture；没有选择／排除。另有依赖精确核对、Pi typecheck/build 及 3 项 guard／isolation 通过；该 3 项中 backend isolation 与全量重叠，不能把所有阶段数字相加。

[最终核心报告](../work/judge-prefetch-rebuild/04-core-verification.md)、[source/harness/build 审计](../work/judge-prefetch-rebuild/04-core-final-source.json)与[五次 capture 摘要](../work/judge-prefetch-rebuild/04-core-verification-history.json)固定精确范围。248 个源码文件及受测 harness 前后一致；全套 617 个 Node PID（581 个 Pi worker）均加载 guard，没有意外 block。五个 dist artifact 的 hash 首次在全量运行中记录、终态相同，不冒称为运行前 artifact hash。

当时尚未接受的比较 runner／测试草稿未进入此 worktree，防止 harness fingerprint 漂移。其后若只加入独立支持脚本／文档且不改变 app 或 harness runtime，另留精确 per-artifact hash 与受影响测试；不得宣称后来改变的支持代码早已在本次核心全量中执行，也不盲目重复未变 backend。最终支持项已按下节独立测试／审查闭合；真实采样／浏览器／本人验收保持开放。

## 核心文档／证据审查闭合

[Standards](../work/judge-prefetch-rebuild/reviews/standards-core-documentation.md)与[Spec](../work/judge-prefetch-rebuild/reviews/spec-core-docs-final.md)独立核对文档提交 `a1ef364813c327585716ba2628914ee53b2f7895`，均无核心文档／证据阻塞。其 pins 保留全部 248 源码与四个受测 harness hash、五次原始 capture/output 哈希及子进程审计的交叉核对；未接受 comparison 草稿明确排除。后继仅登记本节审查结果和报告链接，不改变核心技术内容。

核心可独立发布可追踪 checkpoint；comparison 后续已按下节独立 artifact 测试／审查闭合，不能追溯称它进入早先核心全量。真实 provider／浏览器及本人验收继续开放，04 整体仍待验收。

## 独立比较支持与最终受控交付

- 核心已核实发布为远端 `88310f00836d29362e33384ffd959e9939e31a42`，对应本地 `56f0e6f1d4e1e42d4e574f09df55fde0dce8615f`，精确 tree 均为 `c916518853289f246e64b1ccdac609f9599f42d7`；[映射](../work/judge-prefetch/publication-core-final.json)。当前支持是该核心之后的独立提交，不改变 248 个核心源码或受测 harness runtime。
- [手动比较说明](../work/judge-prefetch-rebuild/LIVE-COMPARE.md)及 runner／test 形成精确支持范围。[Tester 报告](../work/judge-prefetch-rebuild/04-comparison-support-verification.md)记录 **22 passed**，其中 upper/lower 配置的真实当前 app／Pi SDK loopback 两项是重叠子集，另行 affected 2 不能再相加；全部为假 key／本地 provider，非旧新真实模型对照。
- Runner `ec4deeba2a98c2f028f7316b733d42507cc449466b5517688291465fd15cd8e5`、test `96a2027125a3facd302dda44ed1917bc110ef7a72c1cc0d565d483b4d62f6fa9` 与最终两次 capture 前后相同；[精确 source/build/guard 证据](../work/judge-prefetch-rebuild/04-comparison-support-final-source.json)保留原受测文档 hash。最终文档 `bcaa110e4bb2a92e6be08643a6c453f96a8a35e30e882f8149f7574f9ff2ca51` 在测试后完成，已获独立 [Standards](../work/judge-prefetch-rebuild/reviews/standards-comparison-support-final.md)／[Spec](../work/judge-prefetch-rebuild/reviews/spec-comparison-support-final.md)审阅，不能回填成受测字节。
- [27 次历史 capture](../work/judge-prefetch-rebuild/04-comparison-support-history.json)保留 RED、fixture／descriptor／大小写 alias 修复及被替代 21 项成绩。没有为了加入支持重跑未变核心，也不把支持测试冒充核心全量的一部分。
- Preview 默认不触碰配置、网络、子进程或输出。真实执行仅由用户明确手动触发，必须固定两源／build／模型、有限 case/repeat/order 与整体时间上限；无金额默认额度，不支持只凭费用上限运行。保留 MemoryWorker／远端已接收请求的费用风险；HTTP、tokens、成本、质量与渲染时延未知。旧／新为 bundled comparison，不归因全额收益于预取。

## 下一步与证据

前三票已完成云端专项与核心审查，受控核心、独立支持和两轴审查已完成，继续用户本地前端／真实浏览器及获授权的有限真实比较；执行前仍须固定模型／数据／build 版本与明确限额。当前 01–03 同版受控核心全量及独立支持／文档审查已完成；真实模型比较与其他外部层未执行，不标记 04 整体已验收。

## 有界传输支持项（可提前准备，非新增业务票）

官方 `api.deepseek.com` 显式关闭 thinking；仅选择本地补丁的相关传输语义，不选模型或提高额度。支持项可在独立 worktree 提前准备非冲突文件，`runtime/pi/src/worker.ts` 由 01 当前所有者串行接入。支持项独立 red／green 与完整 wire 验证分别留证，字段缺失与 null 必须区分。此项不改变 04 对 03 的功能阻塞，不以传输通过替代 Prompt／政策／浏览器验收。完整范围见执行决定第 4–5 节。

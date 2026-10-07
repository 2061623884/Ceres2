# 可可角色判断与政策预检索：总 TASK

- 状态：待验收（受控核心 558 backend、独立支持 22 项及核心／文档／支持两轴审查已交付；真实模型对照、用户前端／浏览器与本人验收开放）
- 拆分：已批准；功能依赖保持 01 → 02 → 03 → 04
- 执行授权：2026-10-07 用户已批准从真实 GitHub 基线重新 implement-spec／TDD／Agent Team 实施、可追溯提交与分支推送。前端由用户本地处理；详见 [执行决定](../docs/REBUILD-DECISIONS.md)。
- 负责人：主会话维护状态、权限与集成候选；各票唯一实现者按交接绑定，专职 Tester 独占验证，集成者独占提交／合并。
- 规格：[可可角色判断与政策预检索](../docs/plans/ceres2-judge-prefetch-spec.md)
- 范围：替换混合 11 分类；Coco-only 角色入口；Momo 直达与按钮返回；安全首次上下文；政策判断、预检索与同 Pi 注入；同请求范围复用与补查；同版证据与真实调用比较。
- 规划历史：真实基线、四票规划与固定参考清单已发布为远端 `61172a49a850b41673bf5f988eaa0b9140f8772c`，对应本地 `2c705d09746d293c3d47b02edb42cffb7b47cb9b`，精确 tree 均为 `5e35abaeca156a8a139a079ded4af286e7fb5da8`；[发布映射](../work/judge-prefetch/publication-planning.json)。[新基线验证](../work/judge-prefetch-rebuild/baseline-verification.md)通过有限烟测，不代表 01 功能通过。真实模型、用户本地前端／浏览器与本人验收未执行；旧成绩不继承。

## 2026-10-07 当前执行差异

- [执行决定与固定服务端契约](../docs/REBUILD-DECISIONS.md) 对本票生效：最新实施授权取代原草案“未授权”文字，原业务、安全与 fixture 要求继续有效。
- 前端实现与前端文件修改由用户本地负责；下列 typed UI／DOM／真实浏览器验收项保留为本地交接，云端负责其公开 typed action／HTTP／SSE 契约与受控行为。未验页面不得勾选通过。
- 前票云端契约与受控证据交付后可推进依赖；整体端到端验收仍待同版前端证据，不因负责人拆分而自动完成。
- 测试 seam 已由原规格批准，无需重新访谈；所有执行命令由 Tester 负责，功能修改使用独立 worktree、单一文件所有者。

## 建议纵向切片与功能依赖

1. [01 可可入口与按钮返回](ceres2-judge-prefetch-01-role-entry.md)：可演示确认切换、Momo 无 Kev、按钮返回及带相关上下文的可可继续；功能阻塞无，规划提交与文件所有权确认后可执行。
2. [02 政策预检索与同 Pi 回答](ceres2-judge-prefetch-02-policy-evidence.md)：依赖 01 提供的新可可准入及首次上下文；可演示纯政策／混合需求及各失败路径。
3. [03 同范围复用与安全补查](ceres2-judge-prefetch-03-query-reuse.md)：依赖 02 的真实证据链；可演示原样查询无重复实际检索、新子问题补查与合法多范围引用。
4. [04 同版集成与调用对照](ceres2-judge-prefetch-04-candidate-evidence.md)：依赖 03（传递包含 01／02）；同候选确认完整业务及真实调用／时延／用量，不承接前三票漏掉的业务。

功能顺序为 01 → 02 → 03 → 04。每票保留原纵向业务范围；云端负责公开契约、运行时、业务读回与受控测试，用户本地负责前端实现与页面验收。原 UI 条目保留待交接，不由云端测试冒充通过。01–04 功能不并行抢跑；官方 DeepSeek thinking 有界支持项可按执行决定在独立 worktree 修改非冲突文件，worker.ts 必须交 01 当前所有者串行接入。独立只读审查可并行，不因此并行写共享文件。

## 写入所有权与交接

- 01 唯一维护导航／角色准入／typed 动作及初始 Pi 上下文契约；交付后将后续所需的最小共享修改权显式交给 02。
- 02 唯一维护可可政策判断、预取、模型上下文注入、证据注册及相应 fixture；03 在其交付上独占修改复用／补查／引用契约。涉及 01 导航行为的修正回到 01 责任范围协调。
- 04 维护集成 fixture、版本清单与报告，专职 Tester 唯一执行测试／lint／typecheck／build；业务缺陷回所属票修复，再重新冻结与复验，不能静默把功能延期到 04。
- 共享入口、schema、Prompt、fixture 和索引的实际文件由主会话先列单一写入负责人，再交接；不得在同一文件上开并行实现者。总 TASK／PROJECT 由主会话协调。

## 2026-10-07 源码保全快照

01 当前源码已独立保存为 WIP：本地 `ec625a27db5418f0851a5da946c384531534309c` 对应远端 `f323d15751c141e0ded4763a3881bbda6355eae3`，精确 tree 均为 `b9a6d62a8c51e3299a76c35359dc6132d8931587`。目标分支为 `ceres2/judge-prefetch-role-entry-wip-20261007`，与集成分支分开；[发布映射](../work/judge-prefetch/publication-role-entry-wip.json)保留核实回执。

这只是该时点可恢复的源码快照，不是通过证明。其两个审查发现随后已修复；最终云端结论见下节。WIP 与后续功能里程碑保持不同分支／提交映射。

## 2026-10-07 01 云端技术交付

01 云端里程碑已发布为远端 `19822b146637fbf9cbba75dcf499984d393a4605`，对应本地 `4b576321317d6755cb2ef5845ceca6f89ba3e2b5`，精确 tree 均为 `cfb1028c1330537bc703bfff27591e109e61ea13`；[发布映射](../work/judge-prefetch/publication-role-entry-final.json)。

01 修复提交 `9f2eff1265c373736cc5f8683c8ccaa680959c30` 已合并为 `46f3fcf47d544e0c0ecead0abc13cb23d63a38b8`。244 个产品／测试源码文件与最终完整 backend **480 passed**、重叠专项 **149 passed**、Pi typecheck/build 和依赖检查的所有前后 manifest 完全一致；[Tester 报告](../work/judge-prefetch-rebuild/01-role-entry-verification.md)及[源码映射](../work/judge-prefetch-rebuild/01-role-entry-final-source.json)。独立 [Standards](../work/judge-prefetch-rebuild/reviews/standards-01-rereview.md)／[Spec](../work/judge-prefetch-rebuild/reviews/spec-01-rereview.md)原发现已闭合。

01 保持“待验收”，云端技术依赖已释放给 02；前端、真实 provider／浏览器及本人验收仍开放。02 已获准逐行为 TDD，工作树为 `../worktrees/02-policy-evidence`，共享产品文件在显式交接后只由 02 维护；集成者继续独占 TASK／PROJECT 和合并／提交，Tester 继续独占所有安装／验证。03–04 仍等待各自功能前置，不以局部通过提前验收。

## 2026-10-07 02 云端技术交付

02 已核实发布为远端 `e434e1b5419dfadec9db65dea13b63974a9d701e`，对应本地 `0559d9ed17e65cb4f6f8dfab80b83152e6fe280e`，精确 tree 均为 `18b51049c0d847eed04fac3ec26ba36c4afe16fa`；[发布映射](../work/judge-prefetch/publication-policy-evidence-final.json)。这是后续集成发布基底，不以独立 policy WIP 分支代替。

02 最终产品提交 `0aaffb39549db2704c6c0c414e3819277023e7a6` 已合并为 `7ea06a343f95043cc5c1948ef74fc139e0de2280`。同一 246 文件 source map 通过完整 backend **524**、重叠专项 **44**、另行 guard proof、Pi typecheck/build 与依赖检查；[Tester 报告](../work/judge-prefetch-rebuild/02-policy-evidence-verification.md)、[源码与提交映射](../work/judge-prefetch-rebuild/02-policy-evidence-final-source.json)。两轴复审闭合当前发现，等待本地前端／真实 provider／浏览器及本人验收，不称整体已验收。

03 已获准接手真实证据及引用生命周期并逐行为 TDD，工作树 `../worktrees/03-query-reuse`；每次工具查询仍实际检索、仅最后 ref 有效的旧限制由 03 修改。02 交付不包含去重或多范围引用；04 仍等待 03，旁路比较脚本准备不释放其业务依赖。

## 2026-10-07 03 云端专项与 04 核心冻结

03 核心已核实发布为远端 `70a9f8c68ff99de7eb9b062dc1262d287e48b26e`，对应本地 `1170a2eec96454edcf46b18c1fd735ac67ddb2ca`，精确 tree 均为 `a022f3abe73b00943a420c3ad3e1da19c38546ca`；[映射](../work/judge-prefetch/publication-query-reuse-core.json)。这是后续集成发布基底，04 冻结运行不随文档提交移动。

03 产品提交 `35a30fab775764cfcbc01ee84599fb450b6411bd` 已合并为 `d6a40886926bf203b53c52db27d2177b1b3dcb80`。248 个 source hash 与稳定 harness 通过修复后 **152 项专项**（含重叠的 34 复用／安全用例）、依赖、Pi build/typecheck 与 guard proof；[报告](../work/judge-prefetch-rebuild/03-query-reuse-verification.md)和[源码映射](../work/judge-prefetch-rebuild/03-query-reuse-final-source.json)。核心两轴复审闭合 bounded-event accounting P2，独立 runtime_summary 不把丢失字段或尾部事件当完整计数。

04 使用独立 `../worktrees/04-core-verification`，固定上述 merge／tree `2fad3a1c8e74593dc19ee929211be0d35a323938` 已完成一次最终全量 **558 passed**；没有重复完整 03 backend。依赖、Pi build/typecheck 与 3 项 guard／isolation 通过，详见[最终核心报告](../work/judge-prefetch-rebuild/04-core-verification.md)及[source/harness/build 审计](../work/judge-prefetch-rebuild/04-core-final-source.json)。未接受比较 runner 草稿排除，后来支持-only 产物按独立精确 hash／测试范围记录。真实模型、前端／浏览器及本人验收不提前释放。

## 当前局部支持证据

官方 DeepSeek 五条辅助请求路径的有界支持已集成，详见 [04 支持项记录](ceres2-judge-prefetch-04-candidate-evidence.md#2026-10-07-有界传输支持项)及[Tester 报告](../work/judge-prefetch-rebuild/thinking-transport-verification.md)。主 Pi／validator 两条路径随后已由 01 串行接入，并在最终同版专项／完整套件重新验证全部七路径；04 的业务依赖没有释放。当前只报告有边界的受控结果，不宣称完整功能、独立审查或真实 provider 通过。

## 验证隔离更正（2026-10-07）

[Tester 更正说明](../work/judge-prefetch-rebuild/node-guard-correction.md)记录：旧 runner 仅设置 NODE_OPTIONS，但生产 Pi 子进程的明确环境白名单会移除它，因此旧“全部 Node 子进程均受强制 loopback／dotenv 守卫”的表述过强。旧测试数量、源码 hash、合成凭据与 loopback fixture 事实保留，不追溯改称旧守卫已生效。现已只在测试 harness 的 PATH 放置强制加载 guard 的 Node launcher，生产权限未扩大；[新鲜四项证明与失败探针](../work/judge-prefetch-rebuild/node-guard-verification.json)包含实际 worker PID 关联。02 当前及以后工作树的受控验证必须使用该修复，最终全阶段门槛重新冻结后运行。

隔离修复／交接文档 checkpoint 已发布并核实：远端 `99bdcc03de6cd26a70f31d2a16cc77b94e12d0f9` 对应本地 `d9981f3ad0a46b684144e9f3769090a0c24e5994`，精确 tree 均为 `47af6713701ebf40f7d6a6e7be390db48f42e041`；[发布映射](../work/judge-prefetch/publication-node-guard-docs.json)。244 个已释放 01 产品／测试源码未变，02 最终发布使用此集成 checkpoint 为远端基底，随后已推进到上节 02 发布；不使用独立 WIP 分支代替集成或验收。

[核心文档 Standards](../work/judge-prefetch-rebuild/reviews/standards-core-documentation.md)及[Spec](../work/judge-prefetch-rebuild/reviews/spec-core-docs-final.md)已对 `a1ef364813c327585716ba2628914ee53b2f7895` 独立审查，无核心文档／证据阻塞；后继只登记结果／链接。Comparison 草稿仍排除，保持独立支持审查和外部验收边界。

## 最终受控云端交付

核心已发布核实为 `88310f00836d29362e33384ffd959e9939e31a42`（本地 `56f0e6f1d4e1e42d4e574f09df55fde0dce8615f`／同 tree `c916518853289f246e64b1ccdac609f9599f42d7`）；[映射](../work/judge-prefetch/publication-core-final.json)。独立比较支持随后通过 **22 项**，含重叠 actual-app/Pi upper/lower loopback 两项；[报告](../work/judge-prefetch-rebuild/04-comparison-support-verification.md)和[操作说明](../work/judge-prefetch-rebuild/LIVE-COMPARE.md)。核心 558 与支持 22 各自固定源码与受测范围，不拼成未执行过的单一全套数字。

核心及支持的 Standards／Spec 均无阻塞；最终说明文档在测试后单独审核，原 capture hash／失败和旧 21 项窗口原样保留。真实 provider 效果／费用、用户前端／浏览器、记忆 Dream 观察及本人验收仍开放，不称整体已验收。

## 总体验收与证据

各票全部验收项、同候选安全回归、独立 Standards／Spec 审查及真实调用对照分别记录。受控测试、真实模型、真实浏览器、本人验收分层；未满足者保留待验收或阻塞。性能无未经确认的阈值，未知用量不填零。旧阶段未闭合证据仍由[原总 TASK](ceres2-next-experience.md)维护，不借本任务宣称解决。

## 阻塞／下一步

04 冻结核心、独立 comparison 支持与文档审查已完成；下一步只按[交接](../docs/JUDGE-PREFETCH-HANDOFF.md)补获授权真实比较及用户本地前端／浏览器／本人验收，不自动启动付费调用或推 main。官方 DeepSeek thinking 是 04 记录的有界传输支持项，可提前准备但不释放 04 功能验收。真实 provider 采样须先核实配置及有限额度；前端由用户本地接手。各里程碑在本地 commit、授权分支发布、远端完整 SHA 读取与精确 tree 一致性核实后发布；GitHub connector 生成不同提交 SHA 时保留本地／远端 SHA 的持久映射回执，01–03 云端专项／核心结论如上；04 全量、支持／文档与外部门槛需各自同版证据。

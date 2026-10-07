# 01：可可入口与按钮返回

- 状态：待验收（2026-10-07：云端技术门槛已释放；用户本地前端／浏览器、真实 provider 与本人验收仍开放）
- 拆分：已批准；功能依赖保持 01 → 02 → 03 → 04
- 执行授权：2026-10-07 用户已授权从 GitHub 基线重新 implement-spec／TDD／Agent Team 实施、可追溯提交及分支推送；前置功能与专职 Tester 门槛保留。
- 负责人：01 独立实现者，工作树 `../worktrees/01-role-entry`，分支 `ceres2/judge-prefetch-01-role-entry-20261007`；专职 Tester 执行所有验证命令，集成者维护 TASK／PROJECT、提交和合并，Standards／Spec 独立只读审查。共享文件按 [执行决定](../docs/REBUILD-DECISIONS.md#4-写入所有权与可并行支持项) 交接。
- 上级：[总 TASK](ceres2-judge-prefetch.md)；依据：[规格](../docs/plans/ceres2-judge-prefetch-spec.md)。本票不得继承旧版通过成绩。

## 2026-10-07 当前执行差异

- [执行决定与固定服务端契约](../docs/REBUILD-DECISIONS.md) 对本票生效：最新实施授权取代原草案“未授权”文字，原业务、安全与 fixture 要求继续有效。
- 前端实现与前端文件修改由用户本地负责；下列 typed UI／DOM／真实浏览器验收项保留为本地交接，云端负责其公开 typed action／HTTP／SSE 契约与受控行为。未验页面不得勾选通过。
- 前票云端契约与受控证据交付后可推进依赖；整体端到端验收仍待同版前端证据，不因负责人拆分而自动完成。
- 测试 seam 已由原规格批准，无需重新访谈；所有执行命令由 Tester 负责，功能修改使用独立 worktree、单一文件所有者。

## What to build

用户在可可发送新文字，只做一次是否转墨墨的入口判断。需要转交时等待明确切换选择；拒绝不切页。no 及 uncertain／timeout／error 留可可把完整原文送给 Pi，后者说明售后边界并提供入口，不替墨墨写业务。墨墨文字直接交 LangGraph；返回可可只用结构化按钮，移除全部纯／复合返回标签与自动文字返回行为。新可可首次理解保留相关任务、活动问题、待澄清和有效引用，不新增四能力分类器或用虚假标签／null 裁剪替代。

工程提案：首次使用稳定的可可角色级基础 Prompt／工具集合，保留相关任务和问题引用；首次 Prompt、工具与上下文消费者一起迁移，再由既有 guide_request 控制后续相关性。没有第二个能力分类器；首次输入或工具数量可能增加，不能预称降本。

## Blocked by

功能依赖：无；2026-10-07 实施授权已具备，规划提交与所有权确认后可开始。交付阻塞 [02 政策预检索与同 Pi 回答](ceres2-judge-prefetch-02-policy-evidence.md)。

## 数据与 fixture

使用隔离 owner A／B、可可 opening 与墨墨 case；购买任务含饮品分类问题、待澄清数量及既有候选引用。入口 provider 固定 yes/no/uncertain/timeout/error 五组；新请求、相同请求重放、同 ID 不同原文、旧 11 类回执与未完成导航、关闭重开、已确认加购回执分别保留。文字含纯“回可可”、复合“回去买水”、引述／条件式返回及“就第二个”。不引入旧活动数据库。

## 测试与验收

- [ ] 公开 HTTP/SSE＋typed UI 观察每个新可可文字一次入口判断，Momo、按钮和重放零新增 Kev；不再输出四能力或返回分类。
- [ ] yes 经用户确认才切换并续接有效原文；拒绝／过期／跨 owner／opening／版本不偷偷切页；页面选择不授权写入。
- [ ] no 及入口故障均继续同一可可 Pi，真实结果／原因可区分；具体售后只说明职责和入口，没有售后写入。
- [ ] Momo 自然语言及复合返回不触发导航／购物执行，按钮仅返回；已处理文字、已确认数据不重放到写操作。
- [ ] 首次模型实际上下文保留与当前请求相关的任务、问题、待澄清及 refs；原文各子句不丢，“第二个”不误选，不新增强制上游四分类。
- [ ] 旧完成回执可安全回放既有结果；不可兼容的旧未完成导航明确失效，不恢复已撤除自动返回；其处理有公开行为 fixture。
- [ ] 既有购买确认、退款确认、人工责任和停止保护的相关回归通过；证据记录实际源码／fixture 版本与未验证层级。

## Ownership／交接

本票独占云端导航、角色准入、初始上下文、typed 返回动作的服务端契约及对应 fixture 的写入；如需修改共享 schema／Prompt 也由本票一位指定维护者处理。向 02 交付新可可入口、首次上下文与重放契约及证据；不能只删枚举而把消费者裁剪修复留到后票。

## 2026-10-07 WIP 与当前审查门槛

可恢复源码已提交为本地 `ec625a27db5418f0851a5da946c384531534309c`，在独立 WIP 分支发布为远端 `f323d15751c141e0ded4763a3881bbda6355eae3`，两者精确 tree 均为 `b9a6d62a8c51e3299a76c35359dc6132d8931587`；[核实映射](../work/judge-prefetch/publication-role-entry-wip.json)。该快照不表示验收或 02 依赖释放。

该 WIP 时点的两个独立审查发现均已修复并复审闭合：脱敏且可关联的 Kev 原因诊断，以及混合请求中可组合的售后职责说明／显式入口。下面的最终云端证据覆盖修复版本；WIP 本身仍不作为通过证明。

## 2026-10-07 云端交付与依赖释放

- 修复提交：`9f2eff1265c373736cc5f8683c8ccaa680959c30`；集成提交：`46f3fcf47d544e0c0ecead0abc13cb23d63a38b8`。244 个产品／测试文件与最终四项门槛的运行前后 source map 完全一致，提交和合并未改变它们；[冻结清单与提交映射](../work/judge-prefetch-rebuild/01-role-entry-final-source.json)。
- [Tester 报告](../work/judge-prefetch-rebuild/01-role-entry-verification.md)：同版完整 backend **480 passed**，其重叠专项子集 **149 passed**，Pi typecheck/build、62 个 Python 锁定包及 Pi 依赖检查通过。不能把 149 与 480 相加。红测、失败 GREEN 与修复历史保留在[执行摘要](../work/judge-prefetch-rebuild/01-role-entry-verification-history.json)。
- [Standards 复审](../work/judge-prefetch-rebuild/reviews/standards-01-rereview.md)与[Spec 复审](../work/judge-prefetch-rebuild/reviews/spec-01-rereview.md)均闭合原 P2，无新增 01 阻塞发现。
- 云端公开契约包括 Coco-only yes/no/uncertain 判断与真实故障诊断、Momo 零 Kev、显式纯导航按钮、旧回执保护、完整首次任务／问题／引用上下文；混合 completed 或 waiting 结果可附加宿主售后边界与显式入口，既有合法购物／政策事实不被替换。
- 02 明确接收既有政策附加门槛缺口：waiting/general 等尚未支持的主结果可能丢失 policy_ref 对应证据，须覆盖 waiting + policy + role boundary。01 修复的是职责边界可组合性，不宣称修完所有混合政策呈现；详见 Spec 复审。
- 本票向 02 交付云端准入与首次上下文。02 可接手最小共享 runtime／Prompt／证据与 fixture 文件；导航本身不并行修改。原 typed UI／DOM／浏览器条目仍待用户本地验收，真实 provider 和本人验收未完成，不宣称整体已验收。

## 下一步与证据

规划里程碑已于 2026-10-07 发布并核实：[提交映射](../work/judge-prefetch/publication-planning.json)。01 从本地 `2c705d09746d293c3d47b02edb42cffb7b47cb9b` 开始，逐行为红 → 绿由 Tester 独立执行；云端结论以本节上方最终同版证据为准。既有烟测属于[新基线验证](../work/judge-prefetch-rebuild/baseline-verification.md)，不替代本票新行为与安全回归。依据来源及旧测试导航见规格 Further Notes。

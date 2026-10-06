# TASK 02：两角色无订单政策问答

状态：待验收

阶段：受控技术完成；外部验收待完成

技术放行：已放行

放行范围：仅受控技术依赖；主会话 2026-10-06 08:40 UTC 明确批准。真实模型、真实浏览器和本人验收仍待验证，不等于已验收。

最近更新：2026-10-06 08:41 UTC。61 项受控范围回归及 Pi build/typecheck 已由 Tester 报告通过。主会话批准受控集成，分支 tip `73cfaf6`（实现 `e7d35dc`）已通过 merge commit `698a688` 合入；随后独立 deadline fixture 修正形成组合候选 `5937c70`。组合候选政策＋修正 deadline 回归已由 Tester 确认 7/7，通过 runtime typecheck/build，源码运行前后一致。作者已确认 MercuryChat.tsx 与 App.tsx 的现有输入不要求先选订单，受控 DOM `next02-dom-01` 已通过两角色无订单输入、客户端请求、来源／条件展示及无业务写入保护；真实浏览器、真实模型和本人验收未完成。主会话已基于这些受控证据批准技术依赖放行；外部门槛保留。

UI 证据：[受控 DOM record](../work/next-experience/10/checks/next02-dom-01/record.json)、[DOM 原始输出](../work/next-experience/10/checks/next02-dom-01/output.log)；页面证据补充 `abda40e` 随分支 `6368fbf` 通过 merge `918781d` 合入，保留已有集成 TASK 更新。

组合证据：[7 项公开回归](../work/next-experience/10/runs/composed02-policy-deadline/record.json)、`work/next-experience/10/checks/composed02-runtime/`。

范围证据：[49 项回归](../work/next-experience/10/runs/next02-regression-01/record.json)、[12 项回归](../work/next-experience/10/runs/next02-regression-02/record.json)、[政策来源与适用版本](../work/next-experience/02/policy-baseline.md)、[集成记录](../work/next-experience/integration.md)。

工作树：`Ceres-workspace/worktrees/next-02`；分支：`ceres2/next-02-policy`；初始规划基线：`6a4489650b81715aa0beea49eefcf015e91290fd`，实施源码另以 Tester 原始记录对应，不能仅用 HEAD 代替 dirty 候选。

证据：[RED record](../work/next-experience/10/runs/next02-red-01/record.json)、[RED 原始输出](../work/next-experience/10/runs/next02-red-01/output.log)。 [首个 GREEN record](../work/next-experience/10/runs/next02-green-01/record.json)、[GREEN 原始输出](../work/next-experience/10/runs/next02-green-01/output.log)。

证据限制：初次记录只覆盖 tracked 源哈希；专职 Tester 后续 launcher 已加入 untracked 源／测试与前后版本一致性核对。当前技术依赖仅在受控范围放行；真实模型、真实页面与本人验收仍未验证。

负责人：implement_next_policy_help；对应切片实现负责人，由主会话派工登记。 状态由主会话维护；测试执行仅专职 Tester。

范围依据：[已批准规格](../docs/plans/ceres2-next-experience-spec.md)；[总 TASK](ceres2-next-experience.md)。

**交付：** 用户在导购或售后页面，不选订单也能问同一一般政策，得到来源与条件；问具体订单时进入已有查询／资格边界。

**阻塞：** 无，可开始。

**验收条件：**
- [ ] 两角色无订单可答相同适用规则，来源、条件和未知项清楚。
- [ ] 一般政策不冒充具体订单资格、退款批准或提交授权；不因未选订单强制先选订单或切角色。
- [ ] 具体资格依现有权威订单事实判断，整单退款／整行退货规则不变。
- [ ] 政策缺失／服务失败明确呈现，不编造条款；页面保留后续入口。
- [ ] 不增加配送问答或配送验收，不删除既有事实校验。

**迁移／数据：** 先核对并复用现有政策服务／事实来源；只补两角色读取接缝和缺少的可追溯一般政策数据。不新增无必要向量库。固定正常、条件不满足、未知、未选订单四类政策 fixture，不导入旧演示订单。

**必要证据：** 同问题两角色公开 API＋页面问答，来源与条件对照、无业务写入断言；一般政策与具体资格分离的受控／真实模型证据。向 05 提供冻结政策基线，向 09 提供资格边界。

## 下一步与证据

维持已放行政策合同与来源基线供 05／09 使用；05 尚需 01／03、09 尚需 03。继续跟踪真实模型、真实浏览器及本人验收，不启动未满足依赖的下游。

执行证据目录：`work/next-experience/02/`。受控测试、真实模型、真实 UI、自然语言审阅与本人验收分别记账；以上仅是已列受控用例的局部证据，其他门槛未验证。完成实现只能记待验收，不能代替本人验收。

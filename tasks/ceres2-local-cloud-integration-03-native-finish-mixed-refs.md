# T03：同 Pi 原生完成与混合引用

- 状态：待验收（技术实现与受控门槛完成；实际浏览器/真实provider/用户本人验收未完成）
- 负责人：runtime owner (T01→T03 交接)；主会话绑定实际 worker/worktree 后方可写入
- 规格：[本轮规格](../docs/plans/ceres2-local-cloud-integration-spec.md)
- 总任务：[集成 TASK](ceres2-local-cloud-integration.md)
- Blocked by：[T01 Hybrid 政策与有界预取复用](ceres2-local-cloud-integration-01-policy-hybrid-deadline.md)

## 最终当前结论（2026-10-07）

本票技术实现已进入最终产品 `f963017587b3eab30965ffcd3aab90fcc3852f3e`，受控验证/两轴修复闭环见[最终报告](../work/local-cloud-integration/t09/FINAL-VERIFICATION.md)。全量746通过/5跳过属于`81b02f9`；同版知识环境补齐跳过项，最终狭窄修复183例及合入4例另行绑定，不声称最终pin重新全量。实际浏览器BLOCKED、真实provider/用户本人验收NOT RUN，不能把技术完成等同于整体验收。

以下阶段记录按各自固定pin保留，旧“待实现/待交接”等描述属于历史过程，不推翻本节当前结论。

## What to build / 合同

同 Pi guide_request→finish_response，兼容 policy_ref/policy_refs、购物/菜谱/general/role boundary/waiting 的合法组合；Python 逐引用校验；维持 cloud kind 工具限制、5 轮、15 秒、取消和事务回滚。

## 验收

- [x] 以上端到端业务合同完整实现，保留来源与安全边界。
- [x] 受控真实 Node JSONL 与 Guide HTTP/SSE：原生终止、混合 refs、非法/陈旧 refs、waiting+policy+role boundary、取消/超时与零业务副作用。
- [x] 实现者准备 RED/GREEN 用例，专职 Tester 执行并绑定精确 source/build；未经执行不报通过。
- [x] 共享入口/schema/DB/Prompt 改动逐文件由唯一 owner 处理；交付前合入最新集成 tip，处理冲突后重新请求受影响验证。
- [x] 不改变模型配置/额度，不读 holdout/原工作树数据，不做收费请求或 shell push。

## 当前阻塞、下一步、证据

恢复 pin `90d1ac3`，工作树干净；同 Pi native finish 与 recipe facts 已有早期分片证据，当前完整候选待 runtime owner 和 Tester 核对。 依赖 T01 已技术放行；当前候选仍需固定源码受影响验证及独立两轴审查。早期分片成绩不继承为本票整体通过。


## 实际集成依赖补充

T03 候选 `e315c38` 已借入 T02 shopping 提交的 patch-equivalent 副本（至 `a78b9b5`），Tester 在该固定候选完成50例受影响测试及 runtime typecheck/build；这不代表完整 T02 通过。T02 仍在修复商品品类边界，故 canonical 合入必须等待 T02 完整门槛，并由 T03 owner 接入最终 T02 候选处理潜在冲突，再请求必要的同版验证。两轴可先审查本票固定 delta；T04 在两者正式集成前仅可只读准备。


## 组合技术交付

T02 最终 `4efd809` 的66例验证与324个捕获源码文件等价核对已完成。T03 `09ed3a3` 修复 optional recipe facts 与非主引用两项 P2，独立两轴复审关闭；原始失败与报告保留。实际 T02 ancestry 合入 T03 得到 `8950b08`，122例/13文件受影响验证与 Pi typecheck/build 均通过、源码/harness 稳定。

组合 `8950b08` 无冲突合入 canonical `4fd13b3`。T02/T03 源码与受测 pin 相同；仅三份 Mercury 文件来自先前已通过门槛的 T07。固定 detached `4fd13b3` postmerge 独立锁离线安装/build及37例/45.43s通过，无源码/harness漂移。T04 已技术放行。独立真实 BGE/模型/前端/最终全量验收仍未完成。[验证摘要](../work/local-cloud-integration/t02-t03/verification-summary.json)、[源码关系](../work/local-cloud-integration/t02-t03/source-equivalence.json)。

- [ ] 剩余实际浏览器、获准的真实provider与用户本人验收按最终报告独立完成；不由受控结果自动勾选。

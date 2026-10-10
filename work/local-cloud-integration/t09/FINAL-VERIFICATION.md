# 最终技术验证与未验收边界

日期：2026-10-07。九票技术实现与已获准的受控验证完成；实际浏览器、真实provider与用户本人验收未完成。没有合并main或部署。

## 固定源码：不要把两个版本说成一次全量

- 全量基线：`81b02f956298361cf9044ee289c0821a8275fab8`。
- 狭窄产品修复：`3a9fedeae8f01053dba2abc2d6bc36daef125133`，仅修复裁剪事件列表的共享引用、准确重命名通用商品条件helper及新增回归。RED实际复现257条tail，修复后有目标GREEN。
- 最终产品合并：`f963017587b3eab30965ffcd3aab90fcc3852f3e`，合并无冲突，backend/runtime/frontend/data与受测修复pin零差异。
- 最终文档/证据发布可有后继commit，不能改变上述受测产品目录。完整tree和目录绑定见[源码映射](final-source-map.json)。

## 终态门槛

| 门槛 | 固定来源与结果 | 含义 |
|---|---|---|
| backend full | `81b02f9`：746 passed /5 skipped，1066.71s | 唯一整库全量运行，不称修复后再跑全量 |
| 5个skip补证 | 同`81b02f9`，独立严格production知识环境：官方库24 passed；实际BGE4 passed | 1个GraphRAG模块级skip对应5个官方case，含于24例组；4个BGE opt-in case另行实际执行，不算未测；计数不相加 |
| Pi | `81b02f9`独立lock install、typecheck、build通过 | 实际Node/受控provider门槛；最终狭窄修复不改TS，merge还单独build |
| Frontend | `81b02f9`独立lock install、strict TS、Vite build、完整相关DOM组通过 | DOM不是浏览器；最后产品修复不改frontend |
| 真实运行协议HTTP | `81b02f9`实际Pi/LangGraph受控HTTP smoke与21请求模拟业务journey通过 | 模型传输脚本化/loopback，非真实provider与UI |
| 最终修复 | `3a9fede`：183 affected passed，283.29s；目标tail另1 passed | 目标包含于受影响范围，不叠加计数 |
| 最终合入最小检查 | `f963017`：4 passed，7.11s；runtime own-lock build通过 | tail+非饮料确认；源码/harness稳定 |
| support修复 | 外部`8e6be36`；最终仓库路径`4cb670b`：4 passed，8.92s | exact-owned-PGID清理P2关闭；宽HTTP已用相同support执行 |

以上终态记录均报告source/harness稳定。专职Tester的[最终权威清单](T09_FINAL_VERIFICATION.json)保留19个终态gate、精确source/build绑定、skip映射与非阻断warning。运行命令、精确HEAD、原始记录SHA及失败/RED摘要见[验证历史](verification-history.json)。本报告不把重叠数字求和为“总测试数”。BGE真实权重/索引公开开发校准与官方GraphRAG受控传输均不代表真实图LLM质量、holdout或主Agent整轮性能。

## 两轴审查闭环

独立审查完整 `37c98400...81b02f9`，不是仅审最后T08。Spec未发现新产品问题；Standards发现tail共享引用P2、support清理P2和通用helper命名P3。产品`3a9fede`与support`8e6be36`的独立Standards/Spec修复delta均clear，相关RED/GREEN与最终路径绑定保留。无未关闭技术审查发现。

- [完整Spec](../reviews/whole-spec-81b02f9.md)、[完整Standards](../reviews/final-standards-81b02f9.md)
- [产品修复Spec](../reviews/final-delta-spec-3a9fede.md)、[产品修复Standards](../reviews/final-standards-3a9fede.md)
- [support修复Spec](../reviews/browser-cleanup-spec-8e6be36.md)、[support修复Standards](../reviews/browser-support-standards-8e6be36.md)

## 明确保留的验收

- BLOCKED：实际Chromium/官方CUA。Unix socket EPERM与跨执行环境unique host拒连；fixture自身健康，但未进入产品UI。没有浏览器布局、Cookie交互或用户浏览器通过声明。
- NOT RUN：真实provider、真实GraphRAG LLM质量、用户原数据/原数据库迁移、原`.env`、独立holdout、部署或main合并。
- NOT ACCEPTED：用户本人真实浏览器旅程和Memory/Dream既有生命周期验收；受控HTTP和DOM不能代替。

下一步只补本地剩余验收，按[Ubuntu交接](../../../docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)在独立worktree/新配置/新数据库/新索引启动。先验证本地安装，再实际浏览器走明确切换、商品详情/加购/结算、订单推进、售后数量/照片/确认/精确工单、停止/刷新/SSE恢复。真实provider产生费用及数据传输，仅用户亲自执行或另有明确授权后进行。验收前不覆盖原main和53项dirty。

非阻断warning：Vite两条future native-config提示、LanceDB11条deprecation；没有阻断测试问题。pre-Pi早期失败回归曾在实现后重建旧基线作retrospective RED，原始顺序已记录，不声称所有RED都发生在实现前。

# Ceres2 · 智能导购与受控售后

Ceres2 是商超购物 AI 原型：将购买目标与约束转成可检查、可修改、需明确确认的清单，并将模拟订单连接到独立售后。Python 是身份、当前商品事实、权限、确认和事务的唯一权威。

商品价格、库存、结算、支付、退款与配送全部模拟，不涉及真实资金或履约。

## 当前状态

2026-10-08，本机后续开发入口为[本轮 TASK](tasks/ceres2-local-followup.md)与[方案](docs/plans/ceres2-local-followup-spec.md)。工作树 `Ceres2-integration-20261008`、本地分支 `codex/ceres2-local-followup-20261008`，起点 `170fac0`。新增评测采集/评分/标注/失败归档/对照/报告工具，审查修复后三组同命令29项通过；40公开+20独立维护验收形成100计划，但实际模型执行为0。产品非evaluation源码未改；完整回归原始752通过/4环境失败，对应补验通过，不能改写全量全绿。交付入口见[本地交接](docs/LOCAL-CHANGES-HANDOFF.md)与[工具步骤](docs/LOCAL-FOLLOWUP-EVALUATION.md)。

本轮按implement-spec参考Ceres1固定72bb1b9的方法；下一步双轴审查/本地审阅，配置就绪后真实pilot，再依据失败推进对话/检索改进。用户最新要求不合并，最新AGENTS另禁止推送或修改原项目。请按[本机并行启动入口](work/local-cloud-integration/local-acceptance-20261008/ACCEPTANCE-PLAN.md#本机并行启动入口)使用规划backend `8015` / frontend `8446`，保留原listener。真实模型、完整图质量、Memory/Dream和本人验收尚未完成。本机先前的BGE smoke/seed/受控Firefox证据留在[原准备报告](work/local-cloud-integration/local-acceptance-20261008/LOCAL-ACCEPTANCE-RESULTS.md)，有独立适用版本。

下列保留云端交付时的能力与验证版本；其浏览器阻塞是当时的云端记录，不覆盖上面的本机 Firefox 证据。

2026-10-07，九票本地能力与云端入口集成的技术实现、受控验证和两轴修复已完成。最终产品固定 `f963017587b3eab30965ffcd3aab90fcc3852f3e`；尚未完成实际浏览器、真实provider和用户本人验收，不合并main或部署。

- 保留可可新文字一次角色判断、确认后切换、政策预取与请求内复用；墨墨独立售后，返回购物只用明确按钮。
- BM25/BGE/RRF用于候选召回；canonical条件、当前Offer/库存仍由Python验证。
- 同一真实Pi原生完成、合法混合引用、经审校的可选过程消息与稳定SSE恢复。
- 显式Local/Global GraphRAG与规范菜谱事实分离；图关系不证明营养/过敏安全，也不授权采购。
- 模拟商品详情、明确加购、订单顺序推进；售后问题包装数量、照片和精确工单证据范围。
- 运行观测区分入口判断、检索、复用、主Pi、审校、图调用和实际provider usage；未知保留未知，运行版本与导出时源码分开。

## 验证结论

- `81b02f9`：backend全量746 passed /5 skipped；同版独立知识环境官方库24例与真实BGE4例补证这5个skip。
- `3a9fede`：最终狭窄修复183受影响例通过；`f963017`：合入最小4例及runtime build通过。没有声称最终pin再次执行全量，重叠数字不相加。
- 同版Pi typecheck/build、frontend strictTS/build、相关DOM、实际Pi/LangGraph受控HTTP与21请求模拟旅程通过。完整两轴及最终修复delta闭环。
- 实际Chromium/CUA浏览器BLOCKED：IPC权限与跨执行环境host拒连，未进入UI；DOM/HTTP不能代替。真实provider、独立holdout质量和用户本人验收NOT RUN。

详见[最终技术报告](work/local-cloud-integration/t09/FINAL-VERIFICATION.md)、[Tester最终清单](work/local-cloud-integration/t09/T09_FINAL_VERIFICATION.json)和[源码/build映射](work/local-cloud-integration/t09/final-source-map.json)。

## 从哪里开始

1. [本机后续 TASK](tasks/ceres2-local-followup.md)与[方案](docs/plans/ceres2-local-followup-spec.md)：当前本地开发状态、范围与验收。
2. [九票总TASK](tasks/ceres2-local-cloud-integration.md)与[集成规格](docs/plans/ceres2-local-cloud-integration-spec.md)：上轮集成的合同与固定证据。
3. [Ubuntu本地交接](docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md)：独立worktree、依赖锁、固定BGE与新索引、配置、启动、迁移和剩余验收步骤。
4. [工作区恢复](CERES2-WORKSPACE.md)、[云端根入口备份](docs/recovery/cloud-workspace-entrypoints/README.md)。
5. [产品定义](prd.md)、[项目规划](PROJECT.md)、[术语](GLOSSARY.md)、[参考项目](docs/REFERENCES.md)。旧阶段规划不覆盖本轮已批准规格。

## Ubuntu与运行边界

从最终发布回执核对完整SHA/tree，在新的独立worktree使用根目录`.venv`和`.venv-graphrag`、两份Python锁与两份npm锁。必须重新构建Pi/frontend和配套索引；原`.env`、数据库、checkpoint、索引及53项dirty全部留原处，不覆盖main。

发布时的通用安装步骤见[Ubuntu交接](docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md#5-独立依赖模型与索引)；当前本机依赖/索引已准备，启动使用上面的本机 `8015/8446` 入口，保留现有服务。启动后端会启动MemoryWorker；页面与图构建可能调用真实模型，按本轮方案落实配置和执行范围。

Guide预算从基线30秒改为本次处理15秒、最多5轮；直接请求包含同步授权。独立导航预检和用户确认等待不是同一个跨请求预算。独立build-graph使用显式有限正数`--timeout-seconds`，不承诺该时长够用。

不更换用户批准的模型/provider/temperature/输出额度。只有规范化hostname精确为`api.deepseek.com`才发送thinking disabled。缺模型/索引或检索错误不降级伪装成空结果。

## 源码与发布来源

来源：cloud `37c98400e7152b89e4a58f02fff3bceaa73b0eac` 与冻结incoming `6734c7fe79e670df2dae12b065dcc49c0b10a307`。正式独立分支为`ceres2/local-cloud-integration-20261007`。

已发布并读回核实的代码交付／checkout目标：[remote `90c8eab89397ee85454ce9b909206ffed7552e3e`](https://github.com/2061623884/Ceres2/tree/90c8eab89397ee85454ce9b909206ffed7552e3e) ↔ local `2135db13f8ac8f0aa5c38bd87f5059131f18252e`，精确tree `9872cda48df31d8af3178a26f836812fa7e4d6b0`；[最终代码发布回执](work/local-cloud-integration/final-integration-publication-receipt.json)。产品来源仍为 `f963017587b3eab30965ffcd3aab90fcc3852f3e`，本次文档后继不改变产品或测试适用版本。旧修复前候选 `f268d48` 的[历史回执](work/local-cloud-integration/complete-candidate-checkpoint-publication-receipt.json)保留溯源，不作为启动目标。

远端CI：statuses `[]`、Actions运行数 `0`、仓库无workflow，结论为未配置（not configured），不是CI通过。

目录职责：backend管Python业务/LangGraph/知识/evaluation，runtime/pi管真实Node Pi，frontend管React与HTTP/SSE，data/fixtures只含静态模拟来源，work/local-cloud-integration保存可复现支持与固定证据。[完整项目树](docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md#2-项目树与职责)。

## 历史记录

[四票历史](tasks/ceres2-judge-prefetch.md)、[十票历史](tasks/ceres2-next-experience.md)、[基础阶段](tasks/ceres2-upgrade.md)、[本轮过程记录](logs/ceres2-local-cloud-integration-20261007-history.md)保留原来源和证据。旧558 backend、41/41 live、旧30秒对照及旧main发布均不继承为本轮通过。

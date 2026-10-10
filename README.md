# Ceres2 · 智能导购与受控售后

Ceres2 是商超购物 AI 原型：将购买目标与约束转成可检查、可修改、需明确确认的清单，并将模拟订单连接到独立售后。Python 是身份、当前商品事实、权限、确认和事务的唯一权威。

> **2026-10-07 本机 Cursor 接管**：交接快照见 [本机交接文档](docs/CURSOR-HANDOFF-20261007.md)。官方 DeepSeek 请求已关闭 thinking，受控传输通过；真实原句回归仍无候选，记忆未满 10 条，24 小时观察尚未开始。任务最新状态由 TASK10 维护。

> 2026-10-06 本轮：下一阶段体验更新（10 票）。受控技术验证通过，真实模型、浏览器与用户验收仍开放。先看下方更新摘要，再读[接手与剩余验收](docs/NEXT-EXPERIENCE-HANDOFF.md)和[当前十票总 TASK](tasks/ceres2-next-experience.md)。

商品价格、库存、结算、支付、退款与配送全部模拟，不涉及真实资金或履约。

## 当前状态

2026-10-09，用户已确认[to-spec规格](docs/plans/ceres2-kev-quality-followup-spec.md)、三个测试入口与[to-tickets十票图](docs/plans/ceres2-kev-quality-followup-tickets.md)，现按implement-spec执行；当前唯一状态入口为[04总TASK](tasks/ceres2-local-followup-04-real-evaluation-feedback.md)。本轮不合并、不推送、不改原工程或GPU1既有Kev。01真实导航/政策/浏览器技术门槛已通过；[补齐Kev的新100基线](work/local-followup/04/kev-followup-20261009/02-RESULTS.md)已完成，人工标签、产品修复与整体验收尚未完成。当前评测API为8017，隔离启动/配置边界见[冻结记录](work/local-followup/04/kev-followup-20261009/02-BASELINE-FREEZE.md)；不将下面前次8015/8446或缺Kev结论当作本轮环境。

### 前次真实评测与发布记录

2026-10-09，本机后续入口为[本轮 TASK](tasks/ceres2-local-followup.md)与[方案](docs/plans/ceres2-local-followup-spec.md)。工作树 `Ceres2-integration-20261008`、分支 `codex/ceres2-local-followup-20261008`、起点 `170fac0`。评测工具29项通过后，按用户授权复用amax原模型配置完成100次真实尝试：机器业务66通过/30失败/4未知，核心三次全通过11/20，运行15秒100/100；详见[真实任务报告](work/local-followup/04/real-model-20261008/REAL-TASK-EVALUATION.md)。真实官方Graph、90次提取、合成Dream与独立Firefox商品订单旅程见[组件报告](work/local-followup/04/real-model-20261008/REAL-COMPONENT-VERIFICATION.md)。产品非evaluation源码仍未改；旧全量752通过/4环境失败及补验保留原版本。交接见[本地文档](docs/LOCAL-CHANGES-HANDOFF.md)。

本轮按implement-spec参考Ceres1固定72bb1b9；真实执行HEAD为00b397、使用739评测源码。实测后driver/harness窄修最终源码cbca，4008组合35项与最终签名5项按版本分别留证，两轴复审已完成；没有重新采样/评分原100，不能合并测试计数。最新用户授权真实执行后常规推送该交付分支，不合并、不过写原工程。后续按[04剩余任务](tasks/ceres2-local-followup-04-real-evaluation-feedback.md#后续实施顺序与可观察交付)处理商品漏匹配、澄清/plan、Kev缺配及真实Guide图任务；自然度、完整Guide浏览器及本人验收未完成。原配置通过隔离进程限定注入的实际启动方式见[工具说明](docs/LOCAL-FOLLOWUP-EVALUATION.md#按本次授权复用amax配置)，仍使用8015/8446且保留原listener。先前本机BGE/受控Firefox证据在[原准备报告](work/local-cloud-integration/local-acceptance-20261008/LOCAL-ACCEPTANCE-RESULTS.md)，不和新实测混为一版。

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

发布时的通用安装步骤见[Ubuntu交接](docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md#5-独立依赖模型与索引)；当前本机依赖/索引已准备。Kev轮使用已运行的隔离API`8017`及[启动器](work/local-followup/04/kev-followup-20261009/serve_baseline.py)；`8015/8446`是前次入口记录，既有服务保留。启动后端会启动MemoryWorker；页面与图构建可能调用真实模型，按本轮方案落实配置和执行范围。

Guide预算从基线30秒改为本次处理15秒、最多5轮；直接请求包含同步授权。独立导航预检和用户确认等待不是同一个跨请求预算。独立build-graph使用显式有限正数`--timeout-seconds`，不承诺该时长够用。

不更换用户批准的模型/provider/temperature/输出额度。只有规范化hostname精确为`api.deepseek.com`才发送thinking disabled。缺模型/索引或检索错误不降级伪装成空结果。

## 源码与发布来源

来源：cloud `37c98400e7152b89e4a58f02fff3bceaa73b0eac` 与冻结incoming `6734c7fe79e670df2dae12b065dcc49c0b10a307`。正式独立分支为`ceres2/local-cloud-integration-20261007`。

已发布并读回核实的代码交付／checkout目标：[remote `90c8eab89397ee85454ce9b909206ffed7552e3e`](https://github.com/2061623884/Ceres2/tree/90c8eab89397ee85454ce9b909206ffed7552e3e) ↔ local `2135db13f8ac8f0aa5c38bd87f5059131f18252e`，精确tree `9872cda48df31d8af3178a26f836812fa7e4d6b0`；[最终代码发布回执](work/local-cloud-integration/final-integration-publication-receipt.json)。产品来源仍为 `f963017587b3eab30965ffcd3aab90fcc3852f3e`，本次文档后继不改变产品或测试适用版本。旧修复前候选 `f268d48` 的[历史回执](work/local-cloud-integration/complete-candidate-checkpoint-publication-receipt.json)保留溯源，不作为启动目标。

远端CI：statuses `[]`、Actions运行数 `0`、仓库无workflow，结论为未配置（not configured），不是CI通过。

目录职责：backend管Python业务/LangGraph/知识/evaluation，runtime/pi管真实Node Pi，frontend管React与HTTP/SSE，data/fixtures只含静态模拟来源，work/local-cloud-integration保存可复现支持与固定证据。[完整项目树](docs/LOCAL-CLOUD-INTEGRATION-HANDOFF.md#2-项目树与职责)。

## 历史记录

[四票历史](tasks/ceres2-judge-prefetch.md)、[十票历史](tasks/ceres2-next-experience.md)、[基础阶段](tasks/ceres2-upgrade.md)、[本轮过程记录](logs/ceres2-local-cloud-integration-20261007-history.md)保留原来源和证据。旧558 backend、41/41 live、旧30秒对照及旧main发布均不继承为本轮通过。

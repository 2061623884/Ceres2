# 本地未提交内容清单与原因

范围：`Ceres2-integration-20261008`、`codex/ceres2-local-followup-20261008`。本轮源码、公开用例、规格、TASK及选定证据通过本地提交交付；下列内容由Git忽略，保留在本机。清单依据`git status --short --ignored`的路径元数据，不读取凭据或独立验收题正文。

本次用户另授权真实调用原amax模型配置和常规推送；限定字段由隔离进程读取，原`.env`不修改、整文件不迁入。新真实raw产物继续Git外保留，角色/质量缺口不因发布而关闭。

| 未提交路径或文件组 | 原因与保留方式 |
| --- | --- |
| `.env` | 本机独立配置，不能提交密钥；Tester只核对必需字段是否已配置，不输出值、不复制原工程配置 |
| `.venv/`、`.venv-graphrag/` | 本工作树单独安装的依赖；由已提交锁文件及安装证据重建 |
| `.cache/` | 固定BGE权重、下载/安装缓存等大体积本机产物；适用模型revision/hash见测试证据 |
| `frontend/node_modules/`、`runtime/pi/node_modules/` | 本工作树独立npm依赖，不借原工程；锁文件已提交 |
| `frontend/dist/`、`runtime/pi/dist/` | 本机构建产物；源码/锁文件/实际构建报告已提交 |
| `data/indexes/` | 新建检索索引；由本树静态数据与固定模型重复构建，manifest及内容hash在证据中 |
| `data/runtime/` | 新业务数据库、checkpoint和测试运行状态；不追踪Git，不导入旧库 |
| `backend/.pytest_cache/`；`backend/app/**/__pycache__/`、`backend/tests/__pycache__/`；`work/local-cloud-integration/browser-support/__pycache__/`、`work/local-cloud-integration/local-acceptance-20261008/__pycache__/` | 测试与解释器缓存，不属于实现交付 |
| `work/local-followup/tmp/` | 本轮隔离fixture/冻结源码/原始回归/临时服务及其运行数据；公开报告保留命令、适用版本与hash |
| `work/local-followup/tmp/independent-acceptance/acceptance-20.json`、`cases-60-bundle.json`、`batch-plan-100.json`、`score-plan-100.json`、`report-plan-100.json`、`score-plan-v2.json`、`report-plan-v2.json`、`score-plan-v3.json`、`report-plan-v3.json`、`score-plan-v4.json`、`report-plan-v4.json` | 独立Tester维护题正文和原轨迹，实施者不得读取；仅版本、hash、覆盖局限及计数通过`ACCEPTANCE-MANIFEST.md`交付。保留原版与更正版本，不能因位于tmp而删除 |
| `work/local-cloud-integration/local-acceptance-20261008/tmp/` | 先前本机准备的独立依赖/浏览器/测试中间产物，属于170版本证据，不继承为真实模型验收 |
| `work/local-followup/tmp/independent-acceptance/real-live-batch.json`、`real-live-score.json`、`real-live-report.json`及`real-live-pilot-score/report.json` | 本次100真实轨迹/逐题判分含隔离题面或对话，保留原始字节与hash，公开仅聚合/公开回归诊断；不得删除来覆盖失败 |
| `work/local-followup/04/real-model-20261008/raw/`、`tmp/`；`data/runtime/real-model-20261008/`及独立browser数据库；`data/indexes/graphrag/` | 新hybrid/Graph原输出、提取与合成Dream、浏览器截图/证书/日志及运行态。选定脚本/报告/hash清单提交，权重/DB/原始正文不提交 |
| `work/local-followup/01/*.log`、`02/*.log`、`05/*.log`；`work/local-cloud-integration/local-acceptance-20261008/*.log` | 原始测试、构建、安装、浏览器日志在本地保留；选定报告记录实际结果、命令与已取得hash。未留存的原命令/日志缺口在报告明确，不补造 |

独立验收文件组以其清单记录的实际文件名为准；本清单不泄露正文或把未执行计划当测试通过。所有交易数据仍为模拟。

原main和旧优化工作树的未提交现场不属于本轮提交范围，未为“清理”而改动；也不把原现场变化归因于本轮。最终交付回报另列完整SHA、起点SHA及远端读回结果。最新用户授权普通push本交付分支；未执行merge/rebase/cherry-pick/force push。

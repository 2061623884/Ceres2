# 本机真实模型、RAG 与 Memory 执行记录

本报告覆盖工作树 `Ceres2-integration-20261008`、HEAD `00b397443bd7258d2166c6445ac4ac066cefd21d`。运行时产品目录 `backend/`、`runtime/pi/`、`frontend/` 与 `data/fixtures/` 相对冻结产品源码 `739f13ead0c53ce9d82519efc30f51263e29ab45` 无差异。所有服务数据库、Graph/hybrid 索引和模型缓存均为本工作树独立产物；未读写原工程数据库、索引、session 或 checkpoint。

## 配置与隔离

只用 `dotenv_values(..., interpolate=False)` 读取 `/data/amax/Documents/projects/Agent/Agent产品/Ceres2/.env` 中当前 Settings 字段。没有输出、复制或散列 API key。主模型与 Memory extraction/Dream 均为 `deepseek-flash`，主 provider host 为 `api.deepseek.com`；非密钥配置 SHA-256 为 `f1bd1b5983a0a07206a4bb1f549130b4a8b8b49afcb7b0bef845634503f2cbec`。`KEV_BASE_URL` 缺失，Kev 请求数为 0；因此这批结果不证明真实 Kev 角色判定成功，也未用 mock 路由代替。

真实服务数据库为 `data/runtime/real-model-20261008/ceres2.sqlite3`，checkpoint 为同目录独立文件。静态 seed 为 73 个商品和 73 个 Offer。健康检查曾返回 200，数据库连通、`llm_configured=true`、`business_data_mode=demo`。正式 100-run 完成后 Memory 队列排空；服务经 SIGINT 正常退出 0，`8015` 无监听进程。Firefox 隔离旅程后第二个 API 服务也正常退出 0；`ss -ltnp` 未发现 `8015` 或 `8446` 监听进程。

Provider 前置调用命令为：

```text
.venv/bin/python work/local-followup/04/real-model-20261008/provider_job.py provider-preflight
```

退出码 0；DeepSeek Flash 返回成功，1 次 completion、11 provider tokens、约 679 ms。响应正文未保留。

## Fresh hybrid 与 GraphRAG

Hybrid 使用真实本地 BGE-small-zh-v1.5 CPU 推理，不使用旧索引或 mock：模型 `BAAI/bge-small-zh-v1.5`，固定 revision `7999e1d3359715c523056ef9478215996d62a620`，512 维。Hugging Face snapshot tree manifest SHA-256 为 `70ab3a152b39753ca0815774a822d5ca35d7716aafa40b6d0b8e23e6598fed71`；主要权重 blob SHA-256 为 `354763b9b1357bc9c44f62c6be2276321081ed2567773608c0d0785b61d5a026`。新 hybrid SQLite SHA-256 为 `0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`，输入 92 个检索文档（8 菜谱、73 商品、11 政策）。GraphRAG manifest SHA-256 为 `3aad90d9d498e614ddd30799275881c5fc53b9f45c1dbba5fc62eb067cdb3787`。

六条公开 smoke 查询使用实际 BGE、BM25 与 RRF。番茄炒蛋菜谱、炒饭用虾仁商品、未发货取消订单政策的目标分别在 sparse/dense/RRF/hits 中排名第一；生鲜质量政策目标在 hits 排名第二；两个无答案政策查询保留 RRF 候选但没有 `hits`。这只验证小型开发查询，不代表独立相关性评测通过。

官方 GraphRAG 3.2.0 构建命令由 `provider_job.py build-graph 900` 调用，900 秒为显式组件 timeout。一次构建约 86.3 秒，产出 44 entities、61 relationships、26 text units、11 communities、10 community reports，53 个 artifact hashes。11 次 DeepSeek completion 均成功，provider usage 合计 48,420 tokens；另外 9 次为本地 BGE embedding，tokenizer 计数 9,847，不是付费 LLM 调用。构建使用固定 demo fixture，不读取旧图库。

Graph Local 查询 `番茄炒蛋需要哪些食材与商品` 在 180 秒显式组件期限内约 18.0 秒完成，1 次 Graph completion、4,442 provider tokens，并运行本地 embedding。Global 查询 `这批家常菜共有哪几类食材，哪些菜用鸡蛋` 在同一 180 秒期限内约 18.704 秒完成，4 次 completion、24,098 provider tokens。两次查询均超过生产 Guide 的 15 秒工具预算，因此只证明组件功能成功，不证明生产 15 秒 deadline 通过；Guide 的 15 秒与 5 轮预算未调整。

Global 的模型选择记录为 2 个 entity IDs；宿主随后只从实际检索到的 community scope 投影 canonical facts。独立审计确认检索 scope 覆盖 8 菜谱、19 条必需食材/菜谱关系和基准用量、4 道含蛋菜、18 个 ingredient kind，以及猪肉的 `meat` 分类。审计输入为 `tmp/graph-global.stdout.json`，审计报告为 `tmp/graph-audit-v2.json`。初版审计忘记规范化 `recipe:` identity 前缀，产生的是测试脚本误报；修正版保留，不归为产品失败。原始模型/Graph 输出全部留在 ignored `tmp/`，本报告不复述其生成正文。

## 正式 100-run 与 Memory

正式 100-run 由独立验收 runner 通过当前真实 HTTP/SSE 服务执行，20-run pilot 后同批续跑 80。隔离数据库最终 Guide receipt 状态为：66 `completed`、24 `waiting_confirmation`、9 `failed`、1 `protected`。这只是运行状态统计，不等价于 66 个质量通过或 UI/自然度验收。运行事件聚合为 100 `accepted`、603 `answer.delta`、43 `message.interim`、24 `plan.ready`、532 `progress`、91 `turn.completed`、9 `error`；消息正文未读取或导出。

正式任务集的 capture、机器评分及尚未完成的人工质量标注由独立验收报告 [REAL-TASK-EVALUATION.md](REAL-TASK-EVALUATION.md) 记录；本段仅记录隔离运行时的 receipt/event/Memory 聚合，两个报告中的统计口径不同。

Memory 最终 DB 快照见 `tmp/memory-final-snapshot.json`，首 20 pilot owner/run 分组见 `tmp/memory-pilot-final-snapshot.json`。全批共有 90 个 `extract:completed` job，0 个 Memory 错误、pending 或 running job；代码只在模型响应通过结构化校验后标记 completed，因此这是 90 个有效提取响应。Job schema 不保存 usage/token 字段，Memory token 和费用不可观察。首 20 pilot 中 19 个 extraction job completed；其中仅 1 个 owner 有有效自动记忆，最大每 owner 1 条。完整 100 owner 组中最大有效自动记忆数也是 1，达到 Dream 门槛（每 owner 至少 10 条）的 owner 数为 0，真实用户自然触发 Dream 数为 0。

另在完全独立的 `data/runtime/real-model-20261008/memory-dream-smoke.sqlite3` 中，使用 10 条明确合成的自动记忆输入，通过同一个生产 `MemoryWorker` 和 `deepseek-flash` 触发 1 个真实 Dream job，状态 `dream:completed`。这是单次合成阈值/工作流 smoke，不是用户自然触发，不计入正式 100 run，也不代表 Dream 内容质量通过；usage 同样未持久化。脚本 `memory_dream_smoke.py` 不输出输入/模型正文或 owner ID。

## 真实浏览器商品与订单旅程

`firefox_built_ui_order_smoke.py` 在真实系统 Firefox 136.0、新 WebDriver profile 中访问当前 `frontend/dist`，并经隔离 API 到本工作树生产 FastAPI；独立 DB 预置 73 商品/73 Offer。用户可见操作完成商品详情 → 加购 → 模拟结算 → 订单 `submitted` → `shipped` → `delivered`，截图和浏览器 metadata 在 `tmp/browser-real-model-20261008/`。结束后隔离 DB 聚合为 1 个 delivered 模拟订单、购物车 0 项、Guide run 0、Memory job/record 0；此旅程未发 Guide/Memory 模型调用。实际 dist 文件逐项摘要见 `FRONTEND-DIST.sha256`，清单 SHA-256 `a7b507fdbd25e7720b5383bebbb84c8ba048844ecc56931e1a015abb1693c819`。

浏览器使用本地 TLS 终止代理，唯一放行 authority 是 `localhost:8446`；Firefox 遥测、外部测试域名、Google Fonts 和 Unsplash 请求均被代理阻断。证书为测试期自签证书且浏览器接受该证书，因此该浏览器结果证明当前构建版 UI 经本机 HTTPS loopback 运行，不证明公开 HTTP URL 或生产 TLS 配置。一个先前尝试经代理访问 `http://localhost:8446` 时 Firefox 报告 `isSecureContext=false`、`crypto.randomUUID` 不可用；改为同 authority 的本机 TLS 终止后通过。首次 harness 还曾将 dist 目录误判为文件，退出 `not_run`；已在测试脚本中修正。以上均为测试 harness/浏览器传输差异，未修改产品代码。

## 复现脚本与产物边界

本目录保留配置 presence 检查、受控 provider/Graph launcher、hybrid smoke、Graph 审计、Memory 聚合和独立 Dream/Firefox harness。关键源文件、公开 fixture、Pi 编译产物、索引与 BGE revision 逐文件摘要见 `SOURCE-HASHES.sha256`；该清单 SHA-256 为 `d44b7fd0b92c8d654319b3b35b3abe1d310f242cb9d7613f380500a2f5e56c17`。Graph/hybrid SQLite、业务/Memory 数据库、BGE 权重、证书、screenshots、provider raw output 与运行日志在 `.cache/`、`data/` 或 `tmp/` 忽略路径，不应纳入 Git。没有记录密钥、密钥 hash、用户消息正文、验收 case 正文或旧运行数据。

测试 harness 曾有三处本地问题并保留记录：首次浏览器启动脚本对已存在的独立 DB 打印了默认 runtime 路径；只读检查确认 seed 实际落在隔离 DB，随后改用显式路径启动器。首次 dist 探针把目录当文件而安全退出 `not_run`；修正后经 HTTP 代理访问 localhost，Firefox 报 `isSecureContext=false`，于是改由同一精确 loopback authority 的本地 TLS terminator 提供安全上下文。均未改产品源码；未使用的初始浏览器 DB 仍在 ignored `data/runtime/`。

关键命令/结果：

```text
cd backend && ../.venv-graphrag/bin/python -m app.knowledge.cli build-hybrid   # exit 0
PYTHONPATH=backend .venv/bin/python work/local-followup/04/real-model-20261008/provider_job.py build-graph 900   # exit 0
PYTHONPATH=backend .venv/bin/python work/local-followup/04/real-model-20261008/provider_job.py graph-local   # exit 0; 180s component deadline
PYTHONPATH=backend .venv/bin/python work/local-followup/04/real-model-20261008/provider_job.py graph-global   # exit 0; 180s component deadline
.venv/bin/python work/local-followup/04/real-model-20261008/hybrid_smoke.py   # exit 0 after tester-harness import-path correction
PYTHONPATH=backend .venv/bin/python work/local-followup/04/real-model-20261008/memory_dream_smoke.py   # exit 0; one real Dream response
work/local-cloud-integration/local-acceptance-20261008/tmp/browser-venv/bin/python work/local-followup/04/real-model-20261008/firefox_built_ui_order_smoke.py   # exit 0
```

Graph build 使用的早期 `provider_job.py` SHA-256 为 `0bc3fd5ba253a4bdb2a5f477f55e323333fd07eaeb537dc96e12f0b6a12fbbca`；它之后只调整了调用结果的安全聚合展示，没有改变模型请求配置或 Graph 产物。当前 harness 与关键源/索引摘要列在 `SOURCE-HASHES.sha256`。

本报告把离线 hybrid smoke、真实 Graph provider 调用、正式 100-run 公共 HTTP/SSE、合成 Dream 与受控可见浏览器旅程分开。是否通过正式评测集和独立人工自然度判断，以验收 runner 自己的 batch/score/report 为准；本报告不替代它们。

关键 ignored 输出文件名包括 `raw/hybrid-build.stdout.json`、`raw/hybrid-build.stderr.log`、`tmp/graph-build.stdout.json`、`tmp/graph-build.stderr.log`、`tmp/graph-local.stdout.json`、`tmp/graph-global.stdout.json`、`tmp/graph-audit-v2.json`、`tmp/hybrid-smoke-v2.json`、`tmp/memory-final-snapshot.json`、`tmp/memory-pilot-final-snapshot.json` 和 `tmp/browser-real-model-20261008/browser-result.json`。这些文件只用于复核结构化结果或原始组件输出，均未提交；原始模型/图文本、浏览器日志与运行态数据仍留在 ignored 路径。

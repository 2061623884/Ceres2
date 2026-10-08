# Ubuntu 本机执行结果

本报告记录本机准备与一次受控 Firefox 旅程。执行依据是 [本机验收清单](ACCEPTANCE-PLAN.md)；任务状态仍以[当前 TASK](../../../tasks/ceres2-local-cloud-integration.md)为准。源码固定在 `170fac0bc75fcc855897b073337ba218abeb5b7d`，tree `295499ee22cc30485d38eba82e96330a39d7d573`。云端的 746+5、183 项及其他 pin 结果不并入本机结论。

## 本机门槛结果

| 层 | 结果 | 证据范围 |
| --- | --- | --- |
| 独立 Python 环境 | 通过 | 业务 `.venv` 和知识 `.venv-graphrag` 均使用 Python 3.11.15；两份锁安装完成，`pip check` 通过 |
| Pi 与前端构建 | 通过 | 两处 `npm ci`、Pi typecheck/build、前端 strict typecheck/build 全部退出 0 |
| 本地知识检索 | 通过 smoke | 固定 BGE 权重本地推理；新 hybrid manifest、BM25/BGE/RRF 三路均有结果；只覆盖 3 个公开 demo query，不是独立相关性评测 |
| 新业务数据库 | 通过 seed | 只从本 worktree 静态 fixture 新建 catalog/Offer；没有 session、cart、order、owner 或 checkpoint 状态 |
| 浏览器旅程 | 通过 run 11 | Firefox 136、HTTPS、真实构建前端/FastAPI/Pi/LangGraph，模型和检索均由受控 loopback fixture 提供 |
| 后端完整 pytest | 未运行 | 本轮没有重跑云端全量或本地全量后端套件；云端历史结果仍只绑定原 pin |

没有创建本 worktree `.env`，没有读取旧 worktree 配置，没有调用真实/付费 provider、GraphRAG LLM、Memory 或 Dream 模型。GraphRAG 依赖已安装，但本机没有运行完整 Graph 构建。

## 环境与依赖

系统 `python3` 为 3.10.20；`uv` 0.10.11 管理的 Python 3.11.15 用于两个新 venv。机器已安装的 Python 列表没有 3.12，因此使用满足本任务最低要求的 3.11.15；这与云端 3.12 有环境差异。Pi 构建及最终子进程使用 `/home/amax/.nvm/versions/node/v22.19.0/bin/node`（22.19.0）；系统 Node 16.20.2 未用于最终 Pi worker。浏览器为 Firefox 136.0、geckodriver 0.37.1、Selenium 4.50.0。

环境均独立于其他 worktree：

- 业务 `.venv` 安装 `backend/requirements.lock`，锁 SHA-256：`f31281168ba07d87844247f8bcbae82a48537a6b7f6abcfd673bdda905c00f7e`；安装及 `pip check` 均退出 0，日志见 [business-pip-install.log](business-pip-install.log) 与 [business-pip-check.log](business-pip-check.log)。
- Pi `npm ci`、`npm run typecheck`、`npm run build` 均退出 0；lock `runtime/pi/package-lock.json` SHA-256：`2700a4b3ac0ea31611e6a9b2bcb58bb9fda53766474aa8b3382f7d5523aad9cd`。证据：[npm ci](pi-npm-ci.log)、[typecheck](pi-typecheck.log)、[build](pi-build.log)。
- 前端 `npm ci`、strict typecheck、build 均退出 0；lock `frontend/package-lock.json` SHA-256：`9b31e7427564ebb34499cf9adddb5eac2986a6913db66d24d868e644d496e7b7`。证据：[npm ci](frontend-npm-ci.log)、[typecheck](frontend-typecheck.log)、[build](frontend-build.log)。
- 知识 `.venv-graphrag` 按 `backend/knowledge-requirements.lock` 安装 144 个锁定 wheel；`pip check` 退出 0。主要版本：GraphRAG 3.2.0、PyTorch 2.14.1+cpu、Transformers 5.19.0、huggingface-hub 1.33.0、NumPy 2.4.6、PyArrow 25.0.1。锁 SHA-256：`3a82d620102bec1f9495be30ecc6705ba1109b4a20e9a48154e66de2a71df72e`；完整 freeze SHA-256：`80d20ef4cc670abc86ec72c6dcd02f5b96df9b9e7083befda609f96af8ed64a7`。证据：[wheelhouse install](knowledge-wheelhouse-install.log)、[pip check](graphrag-pip-check.log)、[freeze](knowledge-requirements.freeze.txt)。

### 安装与网络失败记录

没有修改任何依赖锁。首次知识依赖安装从配置代理下载，在约 34.5 分钟内仅收到约 65.8 MB（约 32 KB/s），我中断了该安装进程；期间未让另一个 installer 并写同一 venv。公开 `pyarrow==25.0.1` range 下载对照显示，直连 IPv4 5 MiB 用时 1.90 秒（约 2.76 MB/s），直连 IPv6 1.29 MiB 用时 45 秒（约 28.8 KB/s）。之后用 tester 脚本从官方 PyPI JSON 与官方 PyTorch CPU index 解析与锁完全一致的 wheel，以 IPv4 下载并逐个校验发布 SHA-256/文件大小；144 个 wheel、550,871,992 字节全部验证后再离线安装。完整清单位于 ignored wheelhouse，manifest 锁 hash 与上面的锁一致。原安装记录：[第一次安装](knowledge-uv-install.log)、[慢速重试](knowledge-uv-install-retry.log)、[首次 wheelhouse 脚本失败](wheelhouse-download.log)、[验证成功](wheelhouse-download-verified.log)。首次脚本失败是 tester downloader 对 PyTorch simple-index hash 字段命名的解析错误（`KeyError: sha256`）；修复仅在 tester harness，重跑后所有 wheel 校验通过。

Playwright wheel 下载到 48.2 MB 中的 27.0 MB 时速度约 79 KB/s，我取消该下载，没有拿它作为浏览器结论。改用已有系统 Firefox 与独立 geckodriver/Selenium 环境。BGE 的第一次 Hugging Face API 直连在 TLS 阶段因 SSL EOF 失败；诊断发现此主机到 Hugging Face/CDN 的直接路径受阻，而配置代理可访问官方 CDN。未改系统或产品代理配置，之后通过标准 Hugging Face 下载器、`token=False` 和固定 revision 下载成功。记录见 [直连失败](bge-download.log) 与[代理路径成功](bge-download-proxy.log)。

## BGE 与新 hybrid 索引

固定模型 `BAAI/bge-small-zh-v1.5`，revision `7999e1d3359715c523056ef9478215996d62a620`。仅下载六个公开文件，`token=False`，缓存位于本 worktree 的 `.cache/huggingface`；模型权重 `model.safetensors` 为 95,827,648 字节，SHA-256 `354763b9b1357bc9c44f62c6be2276321081ed2567773608c0d0785b61d5a026`。六个文件及完整摘要见 [bge-download-record.json](bge-download-record.json)。

在 `backend/` 工作目录用 `../.venv-graphrag/bin/python -m app.knowledge.cli build-hybrid` 构建新索引，退出 0。manifest revision 为 `fb981e66e2cd272a9a32a6da9db49512dd7a55142e3ccf59afbdc43ee1bb2c01`，索引语料为 73 product、8 recipe、11 policy；embedding 512 维、normalized CLS，tokenizer revision `zh-unigrams-bigrams-ascii-v2`，RRF `k=60`。生成数据库 `data/indexes/hybrid.sqlite3` SHA-256：`0139b71c9bc4a114c6a2763521fbf6e9381fa74b58e64151b94020b8ea567d23`。完整 manifest 与来源/实现 hash 在 [hybrid-build.log](hybrid-build.log)。

单进程 smoke 对公开开发用例 `番茄炒蛋`、`可口可乐`、`未发货取消订单` 执行真实 BGE、BM25 与 RRF 检索，三个 namespace 均有 dense 与 RRF 候选，使用同一新 manifest。Top 1 分别为 recipe `dish-fanqie-chao-dan`（dense 0.80987，RRF 0.032787）、product `demo:cn-coke-original-330ml-can`（dense 0.73260，RRF 0.032522）、policy `P-REF-01`（dense 0.75244，RRF 0.032787）。这些只证明索引与检索链能运行及排名可观察，不代表独立质量通过；policy 检索排名本身也不裁定条款适用性。逐 lane 结果见 [hybrid-dev-smoke.json](hybrid-dev-smoke.json)，脚本为 [hybrid_dev_smoke.py](hybrid_dev_smoke.py)。

## 新业务库静态 seed

交接允许本 worktree 新建静态 demo 数据库。我在 fixture 旅程完成后显式运行：

```bash
(cd backend && env -u OPENAI_API_KEY -u OPENAI_BASE_URL -u LLM_MODEL \
  -u MEMORY_EXTRACTION_MODEL -u MEMORY_DREAM_MODEL -u KEV_BASE_URL \
  -u HUMAN_OPERATOR_TOKEN \
  DATABASE_URL='sqlite:////data/amax/Documents/projects/Agent/Agent产品/Ceres2-integration-20261008/data/runtime/ceres2.sqlite3' \
  MERCURY_CHECKPOINT_PATH='/data/amax/Documents/projects/Agent/Agent产品/Ceres2-integration-20261008/data/runtime/mercury-checkpoints.sqlite3' \
  LLM_MODE=live BUSINESS_DATA_MODE=demo ../.venv/bin/python -m app.services.seed_service)
```

退出 0；没有启动 FastAPI 或 MemoryWorker。只读检查新库得到 `catalog_products=73`、`offers=73`、`stores=1`、`schema_migrations=12`，owners、sessions、messages、carts、orders、售后与记忆记录均为 0。新 DB 为 446,464 字节，SHA-256 `0182fb0b139608da0b6e16cc561c9e82f63080caf799b941919f0e07877db7e6`。seed 来源是本 worktree 的静态 `products.json`、`offers.json` 和 `product-images.json`，hash 分别为 `ce5c0856bf1e39b92ae52b6b81faa90ebf579221afb0908b5bf542a9205f2322`、`c2fabcefe264d3bf532a1a3a82e2d8eba1a1477bd11a66db59ce1528c84f7c9f`、`684dea15dd4f4e6ee8fbc60f399417a71ed09d28816ac821448f91760c280357`。检查使用只读 SQLite 连接。seed stdout/stderr 为空，退出结果记录在 [business-static-seed.log](business-static-seed.log)。seed 没有创建 checkpoint DB。

## Firefox run 11

完整结果与截图目录见 [browser-firefox-run-11.md](browser-firefox-run-11.md)。该轮在本 worktree 的真实 Firefox 136 HTTPS 页面中运行，脚本退出 0，fixture、浏览器、backend 进程组均报告清理完成。Pi 使用 Node 22.19.0；模型是脚本化 loopback HTTP provider，retrieval 是受控 `KnowledgeService.search` 端口；没有调用真实 provider 或 BGE/GraphRAG 搜索质量接口。worker 使用的 compiled Pi `dist/worker.js` SHA-256 `b3de5c2655878e88fbc9f5d8614aa33dba27e179413e4b8f3076ccf6dd1c7e97`，`App.tsx` 为 `65ee70dadef0535eb7ec232382c2448bdf5292353e334d7eea83cfaa4ba33fef`，`QuestionChoices.tsx` 为 `1ffc28a2fe00c9bd73af43f7709e12b35afe9b1a3112e124492ab25578cff315`，`product_question_service.py` 为 `b6a83c2e75b390c5d437f5ddf0c0b34fdc79e6d19932649a3c1c2cef3c9ccac3`，前端 dist 聚合 hash 为 `a7b507fdbd25e7720b5383bebbb84c8ba048844ecc56931e1a015abb1693c819`。完整浏览器 launcher 记录见 [browser-run-11.log](browser-run-11.log)。

一次旅程验证了商品详情、明确加购和模拟结算、订单快照/演示推进、售后数量与照片确认、人工作业照片查看、Coco→墨墨 yes 拒绝后纯角色按钮不重放、yes 接受、no/uncertain/error/timeout 保留原请求、混合商品与政策职责边界、typed category/product/quantity 生成计划但不写购物车，以及多条 interim、刷新后稳定 message ID 和 stop 终态。stop 时，本次新增气泡可见且本次 receipt/event 仍为 `running`、无终态；停止后持久化状态为 `stopped` / `turn.stopped`，history 没有追加消息。

浏览器唯一允许的 authority 是本轮随机 `ceres-fixture-…localhost:58057`。受控代理记录 257 个浏览器请求，238 个发往该 authority，19 个外部请求被拒；HTTPS CONNECT 也只允许该 authority。新 Firefox profile 信任本地生成的测试证书；同随机 hostname 在 HTTP 下 `isSecureContext=false`、`crypto.randomUUID` 不可用，在 HTTPS 下两者可用。因而本轮证明的是该适配器 HTTPS 路径，不证明交接中的默认 `http://localhost:8443` 路径。独立 Node guard 审计 44 行：11 个实际 Node 22.19.0 Pi/result-expression 子进程加载 guard，33 次 provider fetch 仅到 `127.0.0.1:36813`。浏览器代理与 Node/Python 子进程隔离分别留证。

仅 run 11 计为完整本机旅程。早期 run 4–10 的原始失败日志保留但不累加：包括 Selenium 对订单/初始问候的 selector 超时，过严 interim 文本计数，harness 的 `sid` 未初始化，以及 run 10 将可见 `<section aria-label="想看哪类饮品？">` 当成必有 `role=region` 的定位错误。run 11 依据实际可见 section label 修正了独立 WebDriver harness 后通过；没有为了测试修改产品语义/身份校验。首次通过前的所有浏览器尝试都未作为全旅程验收。

本轮浏览器结论不代表用户本人验收、真实模型质量、生产商家数据、所有浏览器支持或完整 GraphRAG。重复点击幂等未验证；主动网络断开后的 SSE 重连未验证，刷新恢复不替代它们。真实 provider / Kev、业务路由模型判断质量、Memory/Dream 生命周期、真实 GraphRAG Local/Global、政策适用性和完整后端 pytest 均未在本地运行。云端 HTTP/DOM 证据仍绑定各自源码 pin。

## 本机 frontend entry 端口 smoke

主会话增加了本机专用 [start-local-frontend.mjs](start-local-frontend.mjs)，只用 Node 22 启动当前 Vite 配置，把 frontend 绑定在 8446、`/api` 和 `/media` 代理目标静态设为 `127.0.0.1:8015`；最终脚本 SHA-256 为 `a5b7ced29b49ab592992b2d991a8c4c226cfda8d7c554603659d0fe1ca7a031d`。按[更新后的执行清单](ACCEPTANCE-PLAN.md)，产品 Vite 配置不变。

两组先前端口均被原 worktree 进程占用：8444/node PID `3414992` 与 8013/python PID `3633840`；8445/node PID `3589534` 与 8014/python PID `3633868`。这些仅做监听器预检，没有连接或终止。下一组 8446/8015 预检为空闲后，我以 `/home/amax/.nvm/versions/node/v22.19.0/bin/node` 运行最终入口，仅 GET `http://127.0.0.1:8446/`。响应 200、HTML 1054 字节且有 root mount；没有请求 `/api`、`/media` 或 backend 8015。入口进程 PID/PGID `1010288` 退出码 0，清理后 8446/8015 均无监听。去敏回执：[frontend-entry-smoke.json](frontend-entry-smoke.json)。这仅证明本机 Vite 入口可启动并返回前端 HTML，未证明其代理连通、新 backend/API、原 `localhost:8444` 用户旅程、真实模型或 MemoryWorker。run 11 的 controlled HTTPS browser 结果是另一条独立路径。

## 生成文件与清理

不应提交的 ignored 产物：`.venv/`、`.venv-graphrag/`、`.cache/huggingface/` 模型缓存、`data/indexes/hybrid.sqlite3`、`data/runtime/ceres2.sqlite3`、`work/local-cloud-integration/local-acceptance-20261008/tmp/` 下的约 551 MB wheelhouse、浏览器 venv/geckodriver、浏览器 profile、每轮截图与代理原始记录、合成 TLS 私钥和临时 fixture 数据库。未产生 `.env`、checkpoint DB、GraphRAG 图产物或旧项目数据副本。tester 报告、脚本、freeze 和 smoke JSON 是 worktree 未跟踪项；`*.log` 与 `tmp/` 产物由 `.gitignore` 忽略，在本机保留但不会随普通 add 提交。报告中的日志链接因此指向当前本机证据，提交时需保留这一区别。本轮没有 git add/commit/push。

Fixture 与 run 11 管理的进程组已停止；8015/8446 smoke 进程组也已退出。原项目的 8012 服务及 8013/8444、8014/8445 listener 仍保持原状，没有被连接或终止。所有后续真实模型与用户验收仍需独立配置和独立证据。

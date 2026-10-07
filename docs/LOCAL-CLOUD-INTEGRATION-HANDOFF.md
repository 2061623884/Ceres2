# Ceres2 九票集成：Ubuntu 本地交接

技术交接日期：2026-10-07；最终产品已固定，剩余真实验收见下文。本文件为新入口，旧 `HANDOFF-UBUNTU.md`、`NEXT-EXPERIENCE-HANDOFF.md`、`JUDGE-PREFETCH-HANDOFF.md` 保留其历史范围。状态以[九票总 TASK](../tasks/ceres2-local-cloud-integration.md)及各票为准；本文不是实际浏览器/真实provider/用户本人验收通过声明。

## 1. 固定来源与当前交付边界

- [cloud baseline 37c98400](https://github.com/2061623884/Ceres2/tree/37c98400e7152b89e4a58f02fff3bceaa73b0eac)
- [incoming 6734c7fe](https://github.com/2061623884/Ceres2/tree/6734c7fe79e670df2dae12b065dcc49c0b10a307)，冻结 tag `ceres2-incoming-20261007-frozen`
- [正式集成分支](https://github.com/2061623884/Ceres2/tree/ceres2/local-cloud-integration-20261007)
- 最近已读回候选checkpoint：[f268d48](https://github.com/2061623884/Ceres2/tree/f268d48cbdeea512f866404be6413a77a1ae9c7b)，remote `f268d48cbdeea512f866404be6413a77a1ae9c7b` ↔ local `4e728c7fa9ede8d3ddaec593b4f2f5c01a4811a5`，tree `388b6dbe136748d20f0c8b5051e3c7d10c94489c`，[回执](../work/local-cloud-integration/complete-candidate-checkpoint-publication-receipt.json)。该checkpoint保存最终修复前候选，不能替代随最终交付提供的新回执。
- [T05 WIP 58db7fe](https://github.com/2061623884/Ceres2/tree/58db7fef475bab34e4c5b53bc3a1e4ba6408dfbb) 是独立备份，不是正式候选或已验收版本，不应当作启动目标。

九票技术实现、运行采集、受控验证与两轴修复闭环完成。最终产品 `f963017587b3eab30965ffcd3aab90fcc3852f3e`；实际浏览器、真实provider与用户本人验收仍开放，不增加“总通过数”或把不同pin重叠测试相加。

最终技术交付登记：

- 最终产品merge：`f963017587b3eab30965ffcd3aab90fcc3852f3e`，与受测修复`3a9fede`产品目录相同。
- backend full：`81b02f9`746 passed /5 skipped，1066.71s；同pin严格知识环境官方库24例/真实BGE4例补齐skip。
- 修复验证：`3a9fede`183 affected；最终merge`f963017`4例与runtime build；不声称最后pin重跑全量。
- Pi typecheck/build、frontend strict TypeScript/build、相关DOM、受控真实Pi/LangGraph HTTP和21请求模拟业务journey：通过，源码/build/harness固定。
- baseline到完整候选两轴及最后产品/helper修复delta：clear，无未关闭技术问题。
- 实际浏览器：BLOCKED，未进入UI；真实provider、真实图LLM质量、用户本人/Memory-Dream验收：NOT RUN。
- 最终发布SHA/tree：主会话读回后随最终交付提供回执；本节固定产品来源不因发布文档commit不同而改变。前述旧里程碑不能代替最终回执。

[完整验证报告](../work/local-cloud-integration/t09/FINAL-VERIFICATION.md)、[源/build映射](../work/local-cloud-integration/t09/final-source-map.json)、[终态记录](../work/local-cloud-integration/t09/verification-history.json)。

## 2. 项目树与职责

下列是已存在的主要源码入口，省略同类文件；不是逐文件全量清单。本文件已纳入仓库，技术门槛与真实验收边界见第一节。生成目录另列，不能据树形图推断已经安装或验收。

```text
Ceres2/
├── AGENTS.md                         # 协作约定；本轮冲突范围以集成规格为准
├── CERES2-WORKSPACE.md                # 当前工作区恢复与协调入口
├── README.md / PROJECT.md / prd.md    # 启动入口、当前计划、产品边界
├── GLOSSARY.md / .env.example         # 术语、空凭据模板
├── backend/
│   ├── pyproject.toml / requirements.lock          # 业务 Python 声明及锁
│   ├── knowledge-requirements.txt / knowledge-requirements.lock # 独立知识依赖
│   ├── app/
│   │   ├── main.py / core/            # FastAPI lifespan、配置、DB、身份
│   │   ├── api/ / schemas/            # HTTP/SSE 与公开请求/响应合同
│   │   ├── models/ / migrations/      # Python 业务事实及追加式 schema 迁移
│   │   ├── services/                  # 导航、Pi 接缝、购物、记忆与 seed
│   │   ├── knowledge/                 # corpus、BGE、hybrid、GraphRAG、CLI/worker
│   │   ├── mercury/ / human/          # LangGraph 售后、人工工单与证据范围
│   │   └── evaluation/                # owner 限定运行导出与人工标注
│   └── tests/                         # 受控公开合同、迁移、wire、恢复测试
├── runtime/pi/
│   ├── package.json / package-lock.json / tsconfig.json
│   └── src/                           # 真 Pi SDK loop、Prompt、原生完成与审校
├── frontend/
│   ├── AGENTS.md / package.json / package-lock.json / vite.config.ts
│   └── src/                           # React 页面、components/、lib/ HTTP/SSE
├── data/
│   ├── fixtures/                      # products/offers/recipes/ingredients/policies 等 JSON
│   └── images/                        # 静态商品图片
├── evals/                             # 公开开发校准数据；不是 holdout 成绩
├── tasks/ceres2-local-cloud-integration*.md # 九票唯一状态与证据入口
├── docs/
│   ├── plans/ceres2-local-cloud-integration-spec.md # 本轮规格
│   ├── knowledge-policy-runtime.md    # 政策检索合同；历史验证段须结合 T06 读
│   ├── REFERENCES.md                  # 框架/参考项目来源及采用边界
│   └── adr/ / agents/ / recovery/     # 决策、协作规范与恢复材料
└── work/local-cloud-integration/      # 固定摘要、来源等价、两轴审查、发布回执
```

本地生成：`.env`、`.venv/`、`.venv-graphrag/`、`.cache/huggingface/`、`data/indexes/`、`data/runtime/`、两处 `node_modules/` 与 `dist/`。这些都不是可复制的运行成果；`.gitignore` 已精确加入 `.venv-graphrag/`；不要把独立知识环境作为源码提交。

## 3. 改了什么，保留了什么

保留 cloud Coco-only 文字入口判断、显式切换、政策预取及当前请求证据复用；故障保留诊断和原文，不冒充 no/empty。墨墨文字及纯按钮不新增 Kev。Python 保持身份、当前 Offer、库存、资格、确认和事务的唯一权威；价格、交易、退款和配送均为模拟。

选择性接入真实 BM25/BGE/RRF 检索，召回不替代 canonical 条件；同一 Pi 的 finish_response 支持合法混合引用；过程消息可为零条，必须审校并用稳定 ID/SSE 持久化。显式 Local/Global GraphRAG 与 deterministic recipe_facts 分开，模型挑选不冒充规范用量/安全证据。售后新增 quantity/photo 和精确 application→human_ticket 关联，历史关联缺失保持未知。UI 保留 incoming 的产品体验并适配新合同，最终结果以 T05 放行后为准。

Guide 从 cloud 基线 30 秒改为整次处理 15 秒、最多 5 轮工具。直接 Guide 包括同步授权，worker 排队/启动/IO 消耗同一个绝对 deadline；独立导航预检、用户等待和后续 HTTP 不属于同一个跨请求 15 秒承诺。重放与重连不重置旧 run。

模型/provider/temperature/输出额度仍取用户当前批准配置；模板里的 qwen 和历史 DeepSeek 成绩不是换模型指令。仅精确官方 hostname `api.deepseek.com` 添加 thinking disabled，第三方兼容地址不能按模型名推断适用。

## 4. 安全获取：独立 worktree，不动原 main

原本地 main 的 53 项 dirty 与本轮文件差异统计不是同一口径。全部保留原处，不 reset、不 stash、不清理、不覆盖、不合并 main；不读/迁入原 `.env`、数据库、checkpoint、session 或索引。

由本地负责人在原仓库执行以下 Git 步骤，只创建新的兄弟 worktree。先将 FINAL_REMOTE_SHA 替换为最终发布回执的完整远端 SHA；未有最终回执时不要把当前里程碑当最终版本。

```bash
git status --short
git fetch origin refs/heads/ceres2/local-cloud-integration-20261007
FINAL_REMOTE_SHA='REPLACE_WITH_VERIFIED_FINAL_REMOTE_SHA'
git worktree add --detach ../Ceres2-integration "$FINAL_REMOTE_SHA"
cd ../Ceres2-integration
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git status --short
```

目标目录须不存在；核对 tree 与回执，不能只看分支名。若 Git 对象未取到，停止核查来源，不改 main。不以 shell push 发布。本地使用 detach 足以体验；新工作需要独立分支时由负责人安排。

## 5. 独立依赖、模型与索引

以下为待执行的 Ubuntu Bash 指南，本次文档工作未运行安装、构建、模型或服务。协作中的执行只交专职 Tester；真实 provider 另需用户授权。Python 业务声明 >=3.11，知识环境按已核对的 Python 3.12 使用；Node 至少 22.19.0。记录实际版本和 lock hash，不更改 lock 绕过失败。

在新 worktree 根目录，逐步执行，失败即停：

```bash
python3.12 --version
node --version
npm --version
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock
.venv/bin/python -m pip check
python3.12 -m venv .venv-graphrag
.venv-graphrag/bin/python -m pip install -r backend/knowledge-requirements.lock --extra-index-url https://download.pytorch.org/whl/cpu
.venv-graphrag/bin/python -m pip check
(cd runtime/pi && npm ci && npm run typecheck && npm run build)
(cd frontend && npm ci && npm run build)
```

前端 build 不等于 strict TypeScript gate，后者由 Tester 按当前 T05/T09 清单另行执行。Pi dist 不随源码发布，必须本地构建。

BGE 固定为 `BAAI/bge-small-zh-v1.5`、revision `7999e1d3359715c523056ef9478215996d62a620`，512 维、CPU。运行时 local-only、无 token、不执行 remote code。新 worktree 必须有自己的模型缓存；不能拿旧索引或旧 `.venv` 顶替。以下是明确获准联网获取公开模型时的一次性准备命令，不是服务自动下载，也不是 provider 验证：

```bash
.venv-graphrag/bin/python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download('BAAI/bge-small-zh-v1.5',
    revision='7999e1d3359715c523056ef9478215996d62a620',
    cache_dir='.cache/huggingface', token=False,
    allow_patterns=['config.json', 'model.safetensors', 'tokenizer.json',
                    'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt'])
PY
(cd backend && ../.venv-graphrag/bin/python -m app.knowledge.cli build-hybrid)
```

必须重建 hybrid：默认读取新 worktree `data/fixtures`，写 `data/indexes/hybrid.sqlite3`，临时 SQLite 完成后原子替换。manifest 绑定五份语料、源码/模型/校准/参数，旧索引不视为兼容；缺失/陈旧/故障不是空匹配，无生产 keyword fallback。源文件或相关实现/模型改变后再重建。build-hybrid 不调用聊天 provider，但会占 CPU/磁盘；它不是 Guide 15 秒受限构建。

GraphRAG 是显式可选路径。需要图功能时在新工作区重新构建；缺图索引不能假装执行了图检索。图构建会发送静态资料给用户批准的聊天 provider，产生费用，先有明确授权。以下 120 秒只是有限预算示例，不承诺成功：

```bash
(cd backend && ../.venv-graphrag/bin/python -m app.knowledge.cli build-graph --timeout-seconds 120)
```

CLI 默认图目录 `data/indexes/graphrag`；支持 `--fixtures`、`--graph-root` 指定配套来源/新输出。build-graph 必须给有限正数 timeout，不接受 Guide `--deadline`；独立 graph 查询默认 15 秒，可用 `--method local` 或 `global`。失败/取消会使 manifest 无效；先看结果 JSON 的 error，不能仅凭退出或残留目录称成功。不要在原图目录试建；该操作会先撤销旧 manifest，部分输出也不构成有效索引。

## 6. 配置、seed 与页面启动

在新 worktree 根目录，仅 `.env` 不存在时：

```bash
cp -n .env.example .env
chmod 600 .env
```

用户在可信本地编辑器填写当前获准的 `OPENAI_BASE_URL`、`OPENAI_API_KEY`、`LLM_MODEL`；独立配置 `MEMORY_EXTRACTION_MODEL`、`MEMORY_DREAM_MODEL`，二者不自动回退到 LLM_MODEL。不要把凭据放命令行、截图、聊天、报告或 Git。检查 shell 环境是否覆盖 `.env`，不整体打印环境。`LLM_MODE=live`、`BUSINESS_DATA_MODE=demo`；本地新库使用模板 `DATABASE_URL=sqlite:///data/runtime/ceres2.sqlite3` 与 `MERCURY_CHECKPOINT_PATH=data/runtime/mercury-checkpoints.sqlite3`。相对路径以 worktree 根目录解析。

`KEV_BASE_URL` 要支持当前 `/v1/systemone` 角色 service 与政策 policy 的两种独立 yes/no/uncertain 判断，不是旧联合能力分类。缺失/故障保留真实诊断继续可可，政策判断失败不预取但仍保留 Pi 工具。`.env.example` 的旧注释不是本轮合同。需要人工工单体验时才由用户设置独立 `HUMAN_OPERATOR_TOKEN`。

新库显式 seed（不拷贝旧状态、不为“修复”反复清库）：

```bash
(cd backend && ../.venv/bin/python -m app.services.seed_service)
```

seed 建 schema、导入静态 catalog/Offer，不重置已有可变 Offer；不是会话恢复或索引构建。商品数量以当前 fixture/seed 实际核对，不能照抄旧 65/70。

后端启动会 init_db、恢复中断 run 并启动 MemoryWorker，可能触发真实模型调用。获得数据发送/费用授权后，由用户或明确获准执行者启动：

```bash
# 终端 A：新 worktree 根目录
(cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8012)
# 终端 B：同一新 worktree 根目录
(cd frontend && npm run dev -- --host 127.0.0.1 --port 8443)
```

浏览器打开 `http://localhost:8443`；Vite 代理 `/api`、`/media` 到 8012，健康接口为 `http://localhost:8012/health`。健康响应不证明模型、索引、Kev 或端到端可用。不改防火墙、不绑定局域网，不杀未知进程。

## 7. 追加式迁移与恢复

`init_db()` 在 seed 和 FastAPI lifespan 自动调用 `initialize_schema()`；不是 Alembic 项目，没有另编迁移命令。当前包含新增照片表、nullable application.human_ticket_id、nullable event recorded_at_ms 等；历史缺失时间/关联不补造。普通新 worktree/new DB 为推荐路径，原数据库完全不动。

若以后明确授权迁移既有数据，先确认无 active run，关闭该库所有写者，保存一致的业务库、checkpoint 及 WAL 状态备份与 source/config 版本，再在副本验证；不能只复制一个正在写的 SQLite 主文件。应用启动本身会改变 schema 和恢复状态，不能充当只读检查。失败后保留现场、停止继续写，不手工删迁移标记、不猜关联、不把新库覆盖旧库；恢复应使用成对验证的完整备份和匹配源码，不对升级后的库盲目回滚旧代码。本轮未访问或迁移用户旧库。

## 8. 已有证据、无需重复与剩余门槛

- 各票已完成的受控测试、两轴及 postmerge 摘要按各自精确 pin 使用。若源码/依赖/build/harness/fixture 未变，不为形式原样重跑旧单票；但不能因此跳过 T09 最终同版全量和跨票组合。变更或冲突处理后重验受影响合同。
- T06 实际本地 BGE 的公开开发检索、旧指纹拒绝已有固定证据；默认线程首次 9.428 秒、后续 0.085 秒只是局部知识检索样本，不是主 Pi/LLM 整轮延时，不证明 15 秒用户体验、线上吞吐、真实图质量或性能提升。不同 pin/线程/预算条件不能混成 benchmark。
- 官方 GraphRAG 库在受控 provider 下的执行与真实 BGE 不等于真实 GraphRAG LLM。此轮我们未执行真实 provider 调用。旧 41/41 live、558 backend、30 秒比较均为历史候选，不继承为集成通过。
- DOM/受控浏览器与真实用户浏览器不同。T05 的 exec Chromium 在单命令授权升级后仍因 Unix socket EPERM 无法启动；官方 CUA 可用 host 拒绝连接。fixture 内部 health-pulse 健康，但另一 exec 与 CUA 均无法连接。当前属已验证的外部环境阻塞，实际浏览器未进入 UI，不是产品用例失败。DOM/build 与 HTTP fixture检查不能冒充浏览器通过；该门槛保留待验。
- 本地新机器需验证自己的安装/构建/模型与新索引条件，不能直接继承云端环境可用性。真实 provider 下的角色/政策/购物混合、native finish/interim、图 Local/Global、照片工单、停止/刷新/SSE 恢复均需独立有界证据。
- 用户浏览器重点：明确切换与返回、商品详情/加购/模拟 checkout/订单推进、售后包装数量/照片/确认与精确工单范围、重复点击幂等、停止后不再发布、刷新重连不重复气泡/写入；最终由用户本人接受。
- Memory 的提取/读取/更正/删除/重启不复活，以及 Dream 的真实模型、阈值/冷却/时钟边界仍需独立证据。短聊天或 observed extraction 不证明 Dream 完成。保留原任务未关闭的生命周期门槛。

运行观测应分别报告入口判断、政策判断/检索/复用、主 Pi、审校、GraphRAG 和实际 provider usage。T08-B已实现并通过受控/最终修复验证；真实provider未执行，不能据此声称已取得真实usage/质量样本。导出时源码 hash 不冒充运行时版本；裁剪事件尾部不作总数，未知时间/usage/费用不填 0。导出含用户消息，分享前检查脱敏，不上传 DB/private-state 或原始 provider 日志。

## 9. 依据与参考来源

本指南静态核对了 `backend/app/core/config.py`、`core/database.py`、`migrations/__init__.py`、`main.py`、`services/seed_service.py`、`services/knowledge_service.py`、`knowledge/{cli,bge,hybrid,graph,providers}.py`、两份 Python 锁、两份 npm manifest/lock、`frontend/vite.config.ts` 和九票规格/TASK/发布回执。最终 source pin 变化后须重新核对涉及的命令。

真实依赖包括 [Pi](https://github.com/earendil-works/pi)（包锁 1.0.3）、[LangGraph](https://github.com/langchain-ai/langgraph)（业务锁 1.2.12、checkpoint-sqlite 3.1.1）、[Microsoft GraphRAG](https://github.com/microsoft/graphrag)（知识锁 3.2.0）及 [BGE](https://huggingface.co/BAAI/bge-small-zh-v1.5/tree/7999e1d3359715c523056ef9478215996d62a620)。版本以最终锁为准。

其他参考项目的固定快照、用途和许可边界见 [REFERENCES](REFERENCES.md)。其中旧“catalog 只有 SQL / 未有向量索引”和旧 live 状态属于历史描述，不能覆盖本轮 hybrid/GraphRAG；未把任何参考仓整仓复制进 runtime，也不依赖相邻 reference/archive，不声称集成外部 Mem0/Graphiti/Letta。

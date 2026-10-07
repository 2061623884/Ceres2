# 检索与 GraphRAG 环境预检

日期：2026-10-07（Asia/Shanghai）\
Worktree：`Ceres2-optimization-20261007`\
分支：`codex/ceres2-optimization-20261007`\
源码基线：`b118dbea3852026c6a04c790b1e27df67c3c9c18`

## 范围与结果

本报告记录专职 Tester 的独立环境安装与本地 embedding 预检。没有运行 GraphRAG 建图、检索查询、真实 LLM/provider 请求、产品测试、数据库导入或索引构建；没有读取 `.env` 或其他凭据。只做了环境包兼容检查、已安装 GraphRAG API 的签名读取，以及真实公开 BGE 模型的 CPU 编码 smoke。

结论：backend 锁依赖、GraphRAG 3.2.0 与 Transformers/CPU PyTorch 可在 Python 3.11.15 的隔离环境中安装并通过依赖兼容检查。`BAAI/bge-small-zh-v1.5` 的公开权重可下载到本 worktree 的忽略缓存目录，并成功产生归一化的 512 维中文向量。该结果只证明本机依赖、权重下载和推理链路可用，不证明 Ceres 检索质量、生产部署性能或 GraphRAG 流程已通过。

## 版本与输入来源

- Host 默认 `python3` 为 3.10.20，不符合 backend `requires-python >=3.11`，未用于安装。使用 uv 管理的 CPython 3.11.15，`uv --version` 为 0.10.11。
- backend 项目定义 SHA256：`backend/pyproject.toml` → `391314222545387d6fd4dd3ae7237052c2ae3cf15b773a46601c527b2e699d0c`。
- backend 锁文件 SHA256：`backend/requirements.lock` → `3efae6c0b2f3222ced5eccc0a562d49f703d563077533a4d1391fc19e59dd6e6`。
- 上述文件在预检开始时来自源码基线 `b118dbea3852026c6a04c790b1e27df67c3c9c18`；安装过程没有改写这些文件。
- GraphRAG 版本存在于 [PyPI `graphrag==3.2.0`](https://pypi.org/project/graphrag/3.2.0/)，其页面标注 Python `>=3.11,<3.14`。本环境使用 Python 3.11.15。
- BGE 模型卡为 [BAAI/bge-small-zh-v1.5](https://huggingface.co/BAAI/bge-small-zh-v1.5)。模型卡说明该模型为中文 512 维 embedding；短查询可在 query 前加“为这个句子生成表示以用于检索相关文章：”，passage 不加指令，并示范 CLS pooling 后 L2 normalize。此 smoke 使用这一公开方法。
- CPU-only PyTorch 安装采用 [uv 的 PyTorch CPU backend](https://docs.astral.sh/uv/guides/integration/pytorch/#using-uv-pip)。

## 环境与命令记录

所有包安装在 worktree 本地环境中，不借用主目录 `.venv`、旧项目环境或 `node_modules`。本轮未准备 Node 环境。

| 命令 | 结果 |
| --- | --- |
| `uv venv --python 3.11.15 .venv` | 首次调用创建成功；复核时重跑同一命令 exit 2，因为目标环境已存在，uv 明确要求 `--clear` 才会覆盖；未覆盖环境 |
| `uv venv --python 3.11.15 .venv-graphrag` | 首次调用创建成功；复核时重跑同一命令 exit 2，因为目标环境已存在，uv 明确要求 `--clear` 才会覆盖；未覆盖环境 |
| `uv pip sync --python .venv/bin/python backend/requirements.lock` | 安装完成，62 个锁定包；随后同命令复核 exit 0（`Resolved 62 packages in 41ms; Checked 62 packages in 1ms`） |
| `uv pip install --python .venv-graphrag/bin/python 'graphrag==3.2.0'` | exit 0；安装 GraphRAG 3.2.0 与共 137 个解析包 |
| `uv pip install --python .venv-graphrag/bin/python --torch-backend=cpu 'transformers[torch]'` | exit 0；安装 Transformers 5.19.0、torch 2.14.1+cpu、accelerate 1.15.0、safetensors 0.8.0 等 |
| `uv pip check --python .venv/bin/python` | exit 0；62 个包兼容 |
| `uv pip check --python .venv-graphrag/bin/python` | exit 0；144 个包兼容 |
| `.venv-graphrag/bin/python work/ceres2-optimization/testing/bge_local_smoke.py` | exit 0；真实权重下载及 CPU embedding smoke 通过，具体结果见下节 |

安装输出包含 hardlink 不可用时退回复制的性能提示，未导致安装失败。GraphRAG 的依赖体量明显高于 backend 锁（包括 LanceDB、PyArrow、spaCy、ONNX Runtime 等）；完整环境下载约数分钟。

环境版本核对命令：

```text
.venv-graphrag/bin/python -c "from importlib.metadata import version; import graphrag; print(...)"
exit: 0
graphrag=3.2.0
torch=2.14.1+cpu
transformers=5.19.0
huggingface-hub=1.33.0
graphrag_path=/data/amax/Documents/projects/Agent/Agent产品/Ceres2-optimization-20261007/.venv-graphrag/lib/python3.11/site-packages/graphrag/__init__.py
```

## BGE 本地 embedding smoke

运行脚本：[bge_local_smoke.py](bge_local_smoke.py)。脚本显式使用本 worktree `.cache/huggingface`，设置 `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` 并以 `token=False` 请求公开仓库；不会读取用户级 HF token、`.env` 或 provider 凭据。权重不进入 Git。

```text
command: .venv-graphrag/bin/python work/ceres2-optimization/testing/bge_local_smoke.py
exit: 0
model_id: BAAI/bge-small-zh-v1.5
revision: 7999e1d3359715c523056ef9478215996d62a620
device: cpu
weight_bytes: 95827648
weight_sha256: 354763b9b1357bc9c44f62c6be2276321081ed2567773608c0d0785b61d5a026
embedding_shape: [2, 512]
finite: true
l2_norms: [0.9999999403953552, 1.0]
torch: 2.14.1+cpu
transformers: 5.19.0
huggingface_hub: 1.33.0
implicit_hub_token_disabled: true
```

固定 revision 与权重摘要相符，单批两条中文输入得到 512 维、有限且归一化的向量。由此确认当前环境能做真实本地 BGE 推理。没有用此 smoke 评估候选排序质量，也没有测延迟或吞吐。

## GraphRAG API 与配置入口

只导入已安装 API 并读取签名，没有调用 build 或 search。探测命令 exit 0：

```text
.venv-graphrag/bin/python -c 'import inspect; from graphrag.api import build_index, basic_search, global_search, local_search; from graphrag.config.load_config import load_config; ...'
exit: 0
build_index(config, method=Standard, is_update_run=False, callbacks=None, additional_context=None, verbose=False, input_documents=None)
basic_search(config, text_units, response_type, query, callbacks=None, verbose=False)
global_search(config, entities, communities, community_reports, community_level, dynamic_community_selection, response_type, query, callbacks=None, verbose=False)
local_search(config, entities, communities, community_reports, text_units, relationships, covariates, community_level, response_type, query, callbacks=None, verbose=False)
load_config(root_dir, cli_overrides=None) -> GraphRagConfig
```

配置加载函数从 `graphrag.config.load_config` 导入。`from graphrag.config import load_config` 在该安装包中得到模块对象；不要把它当作函数调用。探索中曾把 `api.query` 模块误当可调用对象，首次 introspection exit 1；已通过检查安装文件及以上显式导入确认函数入口。GraphRAG API 文档也标记为仍在开发、未来可能不保持兼容，因此实现时需 pin 版本并沿当前签名接入。

## 尚未验证与后续边界

- GraphRAG BYOG workflow、BGE 自定义 embedding provider 配置与实际索引/查询尚未运行；需先确定 schema、模型 provider adapter 和具体 smoke 行为。
- 没有执行真实 LLM/provider smoke；当前 Ceres2 `.env` 未读取，模型服务 ID/在线 provider 配置可用性尚未检查。可确认的是本地 BGE model ID、依赖与权重配置均可用。
- 没有创建 SQLite 数据库、GraphRAG 输出或索引。
- 还未装 Jieba/执行 sparse、RRF 或 Ceres 数据查询 smoke。
- 初检时 `.venv-graphrag/` 尚未被忽略，我已告知主会话；主会话随后在 `.gitignore` 增加忽略规则。最终 `git check-ignore -v .venv .venv-graphrag .cache/huggingface` exit 0，三者均被忽略。我没有改共享 Git exclude 或产品代码。

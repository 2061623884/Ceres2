# 独立优化 worktree 的运行与验收

分支 `codex/ceres2-optimization-20261007`，基线 `b118dbea3852026c6a04c790b1e27df67c3c9c18`，暂不合并。唯一当前状态见 [TASK](../tasks/ceres2-optimization.md)，范围见 [规格](plans/ceres2-optimization-spec.md)，取舍见 [ADR 0004](adr/0004-demo-knowledge-retrieval.md)。原 TASK10 的通过记录不能作为本轮验收。

## 数据与依赖

当前静态定义是 8 道菜、71 个 demo SKU/Offer、18 个采购食材、11 条模拟政策。只增加一款虾仁并修正薯片的鲜土豆采购关联、鸡蛋非乳制品的分类；原数据来源、commit、文件哈希与修正见 `data/fixtures/knowledge-provenance.json`。带确认和来源的重复导入不会重置已变动的业务 Offer。

后端依赖保持 `backend/requirements.lock`，真实 Pi 使用 `runtime/pi/package-lock.json`，前端使用自己的 lock。GraphRAG 3.2.0 / Transformers 5.19.0 / CPU Torch 2.14.1+cpu 在独立环境，完整锁版本见 [knowledge-requirements.lock](../backend/knowledge-requirements.lock)。Linux / Python 3.11 的示例：

```bash
uv venv --python 3.11 .venv
uv pip sync --python .venv/bin/python backend/requirements.lock
uv venv --python 3.11 .venv-graphrag
uv pip sync --python .venv-graphrag/bin/python backend/knowledge-requirements.lock --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match
```

安装/测试/typecheck/build/server 验证只由专职 Tester 执行。本次实际安装与独立环境证据见 [preflight](../work/ceres2-optimization/testing/preflight-2026-10-07.md)。上述完整 lock 同步的重新安装证据若未列出，不把已安装环境检查说成该命令已验证。

本地 BGE 型号 `BAAI/bge-small-zh-v1.5`，revision `7999e1d3359715c523056ef9478215996d62a620`。权重放本 worktree `.cache/huggingface`；建库只从本地读取。首次下载可按 [实际 BGE smoke 脚本](../work/ceres2-optimization/testing/bge_local_smoke.py)执行，后续不得悄悄变更 revision。CPU 推理 normalized CLS、512 维、最长 512 token，query/document 都不加 instruction。GraphRAG 首次并发初始化实际失败后已加互斥并重测，不采用虚拟向量。

模型配置沿原 `OPENAI_BASE_URL` / `OPENAI_API_KEY` / `LLM_MODEL`，使用用户已批准的 `deepseek-flash`；官方 DeepSeek thinking 关闭。配置通过当前 worktree `.env` 或进程环境提供，凭据不进入 fixture、索引 manifest 或 Git。GraphRAG Chat JSON mode 在客户端校验 schema，不宣称 DeepSeek 原生提供 Chat JSON Schema 保证。

## 建库与查询

从新工作树导入静态定义，然后构建独立派生检索库：

```bash
cd backend
../.venv/bin/python -m app.services.seed_service
../.venv-graphrag/bin/python -m app.knowledge.cli build-hybrid
../.venv-graphrag/bin/python -m app.knowledge.cli hybrid --namespace product --query '炒饭用的虾仁'
../.venv-graphrag/bin/python -m app.knowledge.cli build-graph
../.venv-graphrag/bin/python -m app.knowledge.cli graph --method local --query '番茄炒蛋需要哪些食材与商品'
../.venv-graphrag/bin/python -m app.knowledge.cli graph --method global --query '这批家常菜共有哪几类食材，哪些菜用鸡蛋'
```

`build-graph` 从确定性 BYOG 输入实际运行官方社区发现、LLM 报告，再附上对应社区成员的规范原始事实，最后调用官方向量生成；没有让 LLM 重新猜测已知关系。正常 v3 数据规模为 44 实体、61 关系、26 文本块、11 社区/报告，三张 Lance 表为 512 维。建库有任何 `PipelineRunResult.error` 就失败，未完成不写 ready manifest。重建应在本地服务停止时进行。

查询返回 `selection`、规范事实、来源映射、索引与查询版本及实际 calls。Local 呈现聚焦事实；Global 呈现实际检索社区的完整规范视图与必需食材→菜谱关系。未知查询保留空结果。自由生成摘要在真实采样中曾反复矛盾，因此未作为商家事实直接发布；这些失败样本保留，模型选择本身的召回与宿主结构化补齐分别评分。

商品 q、一般政策和菜谱入口已走真实 hybrid；完全匹配的菜名/别名先限定业务身份。中文 sparse 保留单字与二元字组。相关性门槛来自 [开发查询集](../evals/ceres2-optimization-retrieval-dev.json)，不是独立验收：recipe .54 / product .56 / policy .50；查询字面量存在于候选标题/正文时也保留该直接证据。返回两路 raw 候选、RRF 与相关 hits，价格库存从当前 Offer 重读，资格与确认不由分数裁定。后端懒启动 JSONL knowledge worker 缓存 BGE，不导入旧库或旧环境；错误与超时明确失败。

API/Pi/前端启动沿原启动指南，在本 worktree 独立安装与构建即可。生成数据在 `data/runtime/`、`data/indexes/`、`.cache/`；失败原始产物在 `work/ceres2-optimization/testing/tmp/`。这些均不 Git 跟踪。Git 保留数据定义、构建/查询代码、锁版本与去敏证据。

## 可操作闭环

商品图片或名称可进入当前详情，销售包装直接加购物车，数量实际写入；明确模拟结算保存不可修改的订单快照。订单详情可以按版本依次模拟配送、签收，不能跳级、跨用户或改原订单金额。

问具体菜谱食材、基准用量或共用关系时，可可用 `recipe_facts` 提交本轮菜谱引用，显示原始数量与来源；指定菜谱内的食材商品信息由宿主重读当前规格、报价和库存。这个输出不擅自生成采购方案或加购。未收录商品仍保持空候选，如当前 demo 没有酸奶；不能为使采样有卡片而把负例称为通过的正例或补成全量目录。

售后区分未发货整单退款、签收后无理由整行退货、签收后的质量问题与漏送错送/包装破损登记。质量与履约异常申请要求用户明确商品和问题销售包装数，不能超出订单行；不可无理由退货不阻止问题登记。最多关联 3 张 4MB JPEG/PNG/WebP 照片。明确确认后写入申请/回执并同事务转人工工单；照片供人工查看，申请不等于审批、补送或资金到账。人工图片仍按工单订单与独立处理者凭据读取。

一次 Pi 请求可以在真实工具同轮输出可选普通过程文本，已有受控调用的 `interim_message` 对象亦须同样审校。main 采用 function calling 与 `tool_choice=auto`，结束时单独用 `finish_response` 提交原最终引用参数并通过 SDK `finishTurn` 结束；没有再生成一次总结。这个结束工具没有业务写权，Python 仍校验引用并渲染实际结果。独立审校允许不声称结果、执行或承诺的自然核对方向；不合格候选扣留。过程审校提示明确区分“将核对的对象”与“已经查到的事实”，以及“不下单”与承诺下单，普通聊天审校提示保持原合同。公开消息用稳定 ID，独立短事务只提交输入/过程历史与事件，前端在完成前显示并按 ID 去重，位置保持在该次请求的最终回复之前。工具进度仍在原区域，最终业务结果保持单独语义。只读食材/用量查询不会再触发购前结果介绍；可操作商品卡、选择问题、方案与确认回执沿用原介绍入口。此前 JSON 正文握手、去 JSON mode、required 无正文及 auto 的单变量对照均保留；新接缝须重新真实采样，不能继承受控通过来称自然性改善。

## 本人验收入口

以下在当前独立 worktree 与模拟业务环境操作，结果以页面和当次运行证据为准：

1. 在可可处问“先说明核对方向，再查番茄炒蛋和蛋炒饭的食材、基准用量、共用食材及鸡蛋规格价格；只查询，不准备购买”。观察可选过程消息在完成前出现、完成后仍在最终事实之前；原始两人用量、共用鸡蛋和当前 Offer 可见，购物车不变。过程发言条数不固定，自然程度需人工评分。
2. 对现有商品用不同说法查询，核对规格、价格和约束；问未收录的酸奶作为空商品负例，同时问一般退货政策。空商品不能被解释为没有退货政策，政策也不确认某个不存在 SKU 的资格。
3. 点击虾仁商品进入详情，增减购物车数量并模拟结算；进入该订单，依次模拟配送、签收。
4. 对同一订单提出质量或漏送问题，填写明确的问题销售包装数并上传 demo 图片；核对提案后确认。查看持久申请、模拟回执及人工工单/照片；它不代表审批或资金到账。
5. 在可可仍处理时停止或刷新，确认已发消息保留、恢复不重复气泡、购物车没有被过程消息擅自修改。
6. 按下面导出/标注流程，把一次实际失败明确归因并保存标注，再选择已有对应回归入口复测；标签由人给出，技术采样结果不充作盲评。

数据、知识、UI 与业务闭环的技术证据见 [测试索引](../work/ceres2-optimization/testing/test-evidence-index-2026-10-07.md)。历史浏览器无终态采样、空商品引用及 GraphRAG 模型漏选等失败继续保留；单次成功不证明这些问题已全面消失。

## 评测与回流

检索开发集三路对照、真实建库与 GraphRAG 查询、真实商品 HTTP/当前 Offer、受控 Node/Python/SSE、模拟订单/照片/人工越权与重放、浏览器旅程分别记录，入口在 [testing 目录](../work/ceres2-optimization/testing)。某层通过不代表真实自然性或产品验收通过。旧合成 SQL SKU 的 Pi 业务合同测试只控制检索边界，其 `ranks/scores` 为空，不能充作 BGE 效果测试。

按一个明确 owner 导出其已观察运行，输出放忽略的生成目录：

```bash
cd backend
../.venv/bin/python -m app.evaluation.export_runs --owner-id '<当前匿名用户id>' --output ../data/generated/evals/captured-runs.jsonl
```

导出保留输入、状态/错误、消息身份、观测到的 usage/检索与来源、事件及 export-time 源码 hash。新增事件单独存储宿主写入时刻，SSE 事件顶层提供 recorded_at_ms/elapsed_ms，业务 payload 和缓存回执保持一致。历史事件或开始时刻未知时，相应指标为 null；不补写过去的时间。这能定位过程发言、答案和完成的服务端时间，不代表浏览器实际显示时刻。Pi usage 记录当次模型、provider host、SDK 调用开始至 assistant message_end 的时长与实际 token；结果介绍保持原 expression.metric。缺失 usage/版本不推测。失败运行可能没有完整 runtime usage，保持未知，不把未知计为零。owner 不跨用户，原始运行数据不 Git 跟踪。

人工标注独立保存 `run_id`、错误类型/严重程度、期望来源/行为、解释、标注者/时间、数据及样本层次；确认加购不自动等于正向质量标签。Dots 的方法/独立验收集与本地开发集分别版本化。审核后的失败案例进入 `evals/` 开发回归集，明确 Prompt/检索/数据/业务归因，修复后同版复测；原始独立验收集不反复调参。此阶段实现采集/导出与可重复回归，不自动训练或自动改政策。

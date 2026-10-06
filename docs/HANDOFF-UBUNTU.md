# Ubuntu 本地接力：先补 live 与浏览器证据，不重复已完成验证

更新：2026-10-06。TASK16 状态为 **待验收**；真实浏览器、扩展场景和用户本人验收仍未完成。最新隔离 DeepSeek API batch 已通过 **41/41 checks**，包含 Pi 比较、选品、模拟结算/重放和 Mercury 退款提案/确认/重放。本文是本地接力入口，不是整体验收通过声明；覆盖范围见 [TASK16](../tasks/ceres2-runtime-upgrade-16-integrated-verification.md)。

## 1. Ubuntu 原生运行，保留原项目

本次用户选择在 Ubuntu 接力，下面命令全部在 Ubuntu Bash 中运行。创建独立目录，不覆盖原 Ceres 项目；不能复用旧依赖、数据或配置。

当前实现依赖 Linux：guide run 身份读取 `/proc`，Pi runtime 通过 selector 读取子进程管道，live runner 使用 POSIX process group，锁文件固定 `uvloop==0.23.0`。因此本文不承诺原生 Windows Python 可运行；若以后在 Windows 使用，应另行选择 Linux/WSL2 环境或做正式适配。当前无需做 Windows 适配。

## 2. 已经验证什么，哪些不要无故重做

- `4d4eca7` 对应受控测试隔离版本：后端 **295/295 两次**，独立数据目录、同版 322 文件；两轴审查关闭。只增加测试隔离与回归，没有改变当时生产源码。见 [隔离复验](../work/live-validation/TEST-ISOLATION-REVIEW.md)。
- 前一生产版本：后端 294 两次，以及 **45 项匹配源码的 DOM／build／typecheck／pip 命令记录**通过。45 是命令记录数，不是 45 个浏览器用例；受控 DOM 不是真实浏览器。见 [原集成交付](../work/clean-rebuild/16/DELIVERY.md)。
- 最新 provider 诊断补丁：**3 个定向诊断用例、60 个受影响回归用例、12 个 inert harness 用例**通过，Pi build/typecheck 通过，独立 Standards/Spec 审查关闭。3 和 60 不应相加宣称全量覆盖。该补丁经一次真实运行验证诊断可见性，但运行未通过。见 [诊断与真实运行记录](../work/live-validation/DIAGNOSTICS-20261006.md)。原始受控执行证据保留在原验证环境，不随公开仓库分发。
- 2026-10-06 02:22 UTC 用户启动过一次 live batch：配置、全新隔离数据和 seed 检查通过；Pi 比较返回 `PI_PROVIDER_ERROR`。记录中的 502 是应用状态，**不是已观察到的上游 HTTP 状态**。上游原因未知；采购、结算和售后阶段均未到达。
- 2026-10-06 03:42 UTC，在 `3283e28` 上由专职 Tester 按用户明确指示执行一次有界 live batch：配置、fresh isolation、seed 和 live health gate 通过；Pi 比较以 `protected` 结束，`runtime_status=deadline`、`answer_status=failed`，15 秒内完成 4 轮工具交互，第 5 轮模型调用在截止时仍未完成。未观察到上游 HTTP 状态或 transport cause；购物、结算和 Mercury 未运行。退出码 1。脱敏证据留在本机 [evidence](../work/live-validation/tmp/live-20261006T034233Z-d66f017a40aa/evidence)，不得上传相邻 `private-state`。
- 2026-10-06 04:40 UTC，用户明确要求将导购保护上限调到 30 秒后，Tester 在相同 Git revision、已修改且已构建的工作树上执行一次 live batch：配置、fresh isolation、seed 和 live health gate 通过。Pi 比较约 9.87 秒时以应用错误 `422 PI_UNKNOWN_REFERENCE` 失败；不是 deadline。没有记录 upstream HTTP status、transport cause、runtime status 或工具轮数；购物、结算和 Mercury 未运行。退出码 1。证据：[evidence](../work/live-validation/tmp/live-20261006T044045Z-ade5f6652231/evidence)。仅检查脱敏 evidence，未看相邻 `private-state`，未重试。
- 2026-10-06 06:22 UTC，后续按用户“未完成继续”授权，在独立临时 DB 上使用 `deepseek-flash` / `api.deepseek.com` 执行一次有界 live API batch：**41/41 checks passed**，耗时 34.02 秒、exit 0。真实 Pi 比较与选品、模拟购物车确认、checkout/replay、订单退款提案及确认/replay通过；记忆提取被观察到，Dream 因阈值未达到而跳过。两项 Mercury 定向测试 31/31 通过；Pi typecheck/build 通过。测试前后 canonical active runs=0；未读取临时 DB 的 private-state，仅检查脱敏 evidence。

本工作区安装／构建冒烟已完成：Python 3.11.15（满足 `>=3.11`，uv 未提供指定的 3.12.14）、Node 22.19.0/npm 10.9.3；后端依赖检查、Pi runtime typecheck/build 和前端构建通过。修正 31 秒 admission 边界夹具及 40 秒测试专用 SQLite busy timeout 后，受影响后端模块完整复跑 **23/23 通过**（87.70 秒，退出码 0）；最新 Mercury prompt/tool 描述的定向测试 **31/31 通过**。前端构建输出 Vite 配置警告，npm 提示一项 high severity 依赖漏洞。下一步由用户本人在浏览器验收当前工作区，并按 TASK16 补齐剩余历史、人工、停止恢复、记忆生命周期和独立第二次运行；不得把历史 live 失败改记成功。

阅读路线：[README](../README.md) → 本文 → [参考项目与采用边界](REFERENCES.md) → [TASK16](../tasks/ceres2-runtime-upgrade-16-integrated-verification.md)。

历史交付文件中的“尚未配置 provider”“禁止 push”属于当时条件；当前以本次发布安排及上述时间线为准。TASK16 的各项验收定义仍以任务本身为准。

## 3. 全新克隆与一次性 bootstrap

保留原 Ceres 项目不动。将新仓库克隆到 Ubuntu 的 `~/projects/Ceres2`，不要覆盖旧目录，也不要放入已有项目或复制旧 `.venv`、`node_modules`、数据库、索引、会话、checkpoint 或凭据。

```bash
mkdir -p ~/projects
cd ~/projects
# 目标目录必须不存在；先确认本次发布已完成（包括全部 33 张静态图片），不要将上传中的分支当作完整交付。
git clone https://github.com/2061623884/Ceres2.git Ceres2
cd Ceres2
git rev-parse HEAD
git status --short
```

记录实际下载的 commit。发布仓库可能采用新的提交历史；`4d4eca7` 是验证源版本标识，不保证是发布仓库中可以 checkout 的提交。

版本依据：`backend/pyproject.toml` 要求 Python >=3.11；Pi SDK 要求 Node >=22.19.0，前端锁中 Vite 也有现代 Node 要求。原验证环境为 Python **3.12.14**、Node **24.19.0**、npm **11.9.0**。优先使用同系列 Linux 运行时，保留实际版本；不要借用 Windows 的 Python/Node。环境缺失时由本地负责人安排官方来源安装，不擅自更改锁文件绕开安装失败。

本工作区实际使用 Python 3.11.15、Node 22.19.0、npm 10.9.3；后端 lock 依赖安装及 `pip check`、Pi runtime build、前端 build 均通过。Python 3.12.14 的 uv 安装尝试没有匹配下载，因此没有替换项目依赖或锁文件。

以下安装／构建／验证由专职 Tester 执行；实现者不另跑同一组命令。逐行执行，不要整块粘贴。每步失败即停，保留不含凭据的错误摘要，不继续到 live。

```bash
python3.12 --version
node --version
npm --version
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock
.venv/bin/python -m pip check
(cd runtime/pi && npm ci && npm run build)
(cd frontend && npm ci && npm run build)
```

构建 Pi 必不可少，仓库不依赖已提交的 dist；构建前端是新机器的安装冒烟。安装失败是本地 gate，不能拿云端已有结果代替。此时无需启动后台服务，也不必先手动 seed：下一步 API batch 自带隔离数据和 app lifecycle。

## 4. 用户自己配置新的 `.env`

在仓库根目录复制空模板，仅当 `.env` 尚不存在时操作：

```bash
cp -n .env.example .env
chmod 600 .env
```

用户在本地可信编辑器中填写自己的 API key，不复制云端 `.env`，不把 key 交给 agent、聊天、终端命令、截图或报告。必须使用本次批准的 provider／模型，不能为了跑通自动切换：

- `OPENAI_BASE_URL=https://discovery-api.intern-ai.org.cn/v1`
- `OPENAI_API_KEY`：用户自己的该 provider 凭据
- `LLM_MODE=live`；`BUSINESS_DATA_MODE=demo`；`SHOPPING_WRITES_PAUSED=false`
- `LLM_MODEL=qwen3.8-27b`（Pi 与 Mercury）
- `MEMORY_EXTRACTION_MODEL=qwen3.8-27b`
- `MEMORY_DREAM_MODEL=qwen3.8-27b`
- `HUMAN_OPERATOR_TOKEN`：仅人工工单体验需要时设置独立凭据，不能复用模型 key

保持新模板的本地数据库路径；不要引用旧库。环境变量优先于 `.env`，若有旧的 shell 配置应由用户检查相关项，禁止整体打印环境或 `.env`。空配置、加载成功或 `/health` 成功都不证明 provider 可用。

## 5. 优先补一次用户亲自启动的 bounded API journey

先阅读 [USER-RUN](../work/live-validation/USER-RUN.md) 的请求范围、自动确认和数据共享说明。它会向指定 provider 发送合成购物内容、demo catalog、合成订单／售后及记忆上下文，可能产生正常模型费用；所有购物、支付、退款、配送均为模拟。

确认本地出站访问获准后，由用户亲自在 Ubuntu、仓库根目录执行：

```bash
.venv/bin/python work/live-validation/run_live_batch.py
```

agent 不代跑；不以“连接检查”名义偷偷重试。无需提前 seed 或启动 Uvicorn/Vite。batch 创建全新独立 DB/checkpoint、导入静态数据并启动真实 app lifecycle；最多五轮 guide、一轮 Mercury、240 秒总上限，包含正常后台提取／Dream。它不是浏览器测试，也没有 dry-run 模式。

本工作区先后执行的历史批次和 06:22 UTC 成功批次均保留各自 evidence；历史失败不覆盖或追认为通过。最新一次已经通过，后续 provider 批次不需要重跑，必须有用户新的明确授权。本文下方 `USER-RUN` 命令仍固定到旧 InternAI/qwen 配置，不是最新 DeepSeek runner。

预期顺序：真实 Pi 比较 → 选择返回候选并生成计划 → 单独确认加购／重放 → 模拟结算／重放 → 同一订单真实 Mercury 提案 → 独立确认 requested 回执／重放 → 普通问答、偏好、停止与自动记忆观察。某步失败后下游不再执行。具体断言和退出码以 USER-RUN 为准。

失败时保留本次 evidence：区分应用 502、真实 `upstream_http_status`、有限 transport class/code、保护超时和业务断言。缺失字段保留未知，不猜鉴权／网络原因，不绕过网络限制。新的 live run 需新的用户明确授权。

只回传生成目录下经检查的 `evidence` 文件；不要上传相邻 `private-state`、数据库、checkpoint、`.env`、headers/cookies 或原始 provider 日志。即使退出 0，也不代表完整 TASK16、两次独立 live 验证、真实页面或用户验收通过。

## 6. 再启动页面，做真实浏览器体验

API batch 的数据库保持独立、不复用。页面首次体验使用新克隆默认的全新 `data/runtime/`；不要反复清库。先显式 seed 一次，再启动服务。应用启动可能自动调度后台模型任务；因此下面 Uvicorn 由用户亲自启动，任何会触发 live provider 的浏览器操作也由用户亲自执行，agent 只指导并查看用户允许分享的结果。

Ubuntu 终端 A（仓库根目录）：

```bash
(cd backend && ../.venv/bin/python -m app.services.seed_service)
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8012
```

Ubuntu 终端 B：

```bash
cd ~/projects/Ceres2/frontend
npm run dev -- --host 127.0.0.1 --port 8443
```

后端 `/health`：`http://localhost:8012/health`。用 Ubuntu 上获准的真实浏览器打开 `http://localhost:8443`；它代理 `/api` 和 `/media` 到 8012。正常页面 bootstrap 建立同一匿名身份。seed 应导入 65 SKU、65 模拟 Offer、一个门店；33 张原图，其余缺图不等于导入失败。

如 localhost 不可达，先记录后端／前端启动状态和浏览器连接错误；不要擅自暴露到局域网、改防火墙／VPN，或杀掉占用端口的未知进程。页面能打开之后再检查业务，不能将 API batch 充当浏览器证据。

按 [DELIVERY 的九步体验](../work/clean-rebuild/16/DELIVERY.md#manual-live-experience-when-the-gates-are-available) 逐项留证，重点是：

1. 可可：比较、选候选、数量／预算；如出现报价，接受报价只改预算，购物车仍需独立确认。
2. 精确加购、模拟结算；在独立墨墨入口选同一订单，核对售后提案的订单／金额／理由，确认前无回执，确认后只有一个 `requested`，不能显示成已退款。
3. 历史多菜复购：新人数／预算／排除条件、当前供给和独立重新确认；不能继承历史授权。确定性缺货使用已授权隔离 fixture，不随意改用户数据。
4. 人工工单：单独 operator 凭据、进度／回复／关闭；接管期间禁止 agent 写，关闭后旧提案不能恢复授权，需要新提案和确认。在途竞争两种顺序已有受控证据，人工点击不冒充调度压力测试。
5. 停止，以及另一次真实关页／重开恢复：计划、购物车和 durable 结果不丢失、不重复写。
6. 记忆提取、读取、更正、删除及重启不复活。普通短体验不能证明 Dream 十条记录／24 小时冷却／30 天时钟边界；实际四条模型路径须各有真实证据。

## 7. 仍待关闭的 gate 与下一位 agent 接力

- 指定 DeepSeek provider 上的最新真实比较已完成，P0 购物/结算/退款批次 **41/41** 通过；历史复购、供给修订、用户浏览器、人工工单、停止与浏览器恢复、记忆更正/删除、独立第二次运行仍未覆盖。提取仅为 observed，Dream 因阈值未达到而跳过。
- 完整 API journey；历史多菜／缺货修订、人工工单、关页恢复、记忆更正／删除／重启等剩余场景。
- TASK16 要求的两次独立新增业务验证及最终同版证据核对；一个 batch 通过不够。已有受控双跑不需要为形式而原样重跑，新增 live／页面证据也不能借用历史结果。
- 必要变更后的相关复验和两轴审查；真实浏览器结果；用户本人明确验收。三者分别记录，不自动标已验收。

可复制给本地下一位 agent：

> 在这个 Ceres2 工作区接力，保留原项目。先读 AGENTS.md、docs/HANDOFF-UBUNTU.md、TASK16 和链接 evidence，核对当前工作树与服务状态。当前 `deepseek-flash` / `api.deepseek.com` bounded isolated API batch 已 41/41 通过；不要重跑已完成的 live batch 或读取 `.env`/`private-state`。专职 Tester 唯一执行安装/build/test；实现者按需修复，独立 Standards/Spec 只读审查。当前重点是让用户在已打开的真实浏览器完成验收，并补齐 TASK16 尚未覆盖的历史复购、供给变更、人工、停止/恢复、记忆生命周期、Dream 和第二次独立验证。若后端进程未加载本轮 Python prompt 修正且需要 reload，先确认无 active run，保留数据库与会话，只重启此前由本任务启动的服务。任何新 provider 批次需要用户新的明确授权。记录模型、源码和 evidence 版本；不把单次 API batch 通过写成 TASK16 已验收，也不代替用户签署本人验收。

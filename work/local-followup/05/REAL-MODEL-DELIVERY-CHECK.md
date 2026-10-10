# 真实模型交付核对

核对对象为 HEAD `00b397443bd7258d2166c6445ac4ac066cefd21d`，基线 `739f13ead0c53ce9d82519efc30f51263e29ab45` 与 `170fac0bc75fcc855897b073337ba218abeb5b7d`。本报告只记交付卫生和既有证据的一致性，不运行测试、构建、服务、浏览器或模型。

## Git 与产物

- `git diff --cached --check` 在当前 25 个 staged 文件上退出码为 0。
- 相对 739 与 170，`backend/`、`runtime/pi/`、`frontend/`、`data/fixtures/` 中非 evaluation 产品源码差异均为空；当前未暂存的产品源码路径也为空。比较明确排除了 `backend/app/evaluation/**` 与 `backend/tests/test_local_followup_*.py`。
- staged 文件名共 25 个；对 `.env`、`raw/`、`tmp/`、数据库/Parquet、key/PEM 与私有 case 文件名的扫描命中为 0。该扫描只核对文件名，没有读取或复制私有验收题面。
- `SOURCE-HASHES.sha256` 清单 41/41 与工作树文件匹配，清单本身 SHA-256 为 `d44b7fd0b92c8d654319b3b35b3abe1d310f242cb9d7613f380500a2f5e56c17`；`FRONTEND-DIST.sha256` 为 6/6 匹配，清单 SHA-256 为 `a7b507fdbd25e7720b5383bebbb84c8ba048844ecc56931e1a015abb1693c819`。
- `REAL-COMPONENT-VERIFICATION.md` 与 `REAL-TASK-EVALUATION.md` 的本地 Markdown 链接均可解析。组件报告按要求更正为“capture、机器评分及尚未完成的人工质量标注”。这项更正和本报告都在当前 25 文件暂存快照之后写入，尚未 stage；请 root 一并 stage 后重新执行 `git diff --cached --check`。

## 结果口径复核

- 真实 100 行任务批次：100/100 attempted、100/100 capture；评分执行阶段 `guide_run=99`、`runner_failed=1`。机器业务 verdict 为 pass 66、fail 30、unknown 4。核心 20 题各执行 3 次，verdict 为 44/13/3，严格三次均通过为 11/20。100 行均未人工 review；first-useful 人工有效性标记为 unknown，不能表述为人工评分完成。
- 正式 Guide 的 15 秒阈值记录 100 个样本均未超时；这不替代内容质量或人工验收。正式 100 行中 Graph tool/query/provider/embedding 调用均为 0。
- 独立 Graph 组件 build 与 local/global smoke 使用单独显式 180 秒 query deadline；18.0 秒与 18.704 秒的查询结果不证明生产 Guide 15 秒预算通过。Graph 构建有 11 次成功的 DeepSeek completion，另外 9 次为本地 BGE embedding。
- 正式批次有 90 个 Memory extraction job 成功，usage/token 未持久化，故调用用量不可完整观察；用户自然 Dream 为 0。另一次独立 smoke 用 10 条合成初始记忆触发 1 次真实 Dream，不能算作用户自然触发或内容质量通过。

上述计数来自已冻结的 [正式任务报告](../04/real-model-20261008/REAL-TASK-EVALUATION.md) 与 [组件报告](../04/real-model-20261008/REAL-COMPONENT-VERIFICATION.md)。本次没有改变源码、索引、模型、数据库或正式运行报告。

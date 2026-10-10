# 最终发布前检查

检查固定源码 HEAD `cbca5d15bd40bd200f542d0eeaa1bc8192af9424`。当前交付状态仍为进行中／待验收：真实批次和工具修复有分层证据，但整体规格、自然度/有用性人工标注及本人验收未完成。

## Git、源码与产物范围

- `git diff --cached --check`：exit 0。当前 11 个 staged 文件全为 Markdown 文档/审查报告；`git diff --quiet`：exit 0，无 tracked unstaged changes。
- 只读对比 `170fac0bc75fcc855897b073337ba218abeb5b7d..cbca5d15bd40bd200f542d0eeaa1bc8192af9424` 的 `backend/`、`runtime/pi/`、`frontend/`、`data/fixtures/`，排除 `backend/app/evaluation/**` 与 `backend/tests/test_local_followup_*.py`：非 evaluation 产品路径差异为空。相同范围的 unstaged source diff 也为空。
- 当前 `REAL-HARNESS-FINAL-SOURCE-HASHES.sha256` 11 项与工作树逐项匹配。旧 41 项 `SOURCE-HASHES.sha256` 属于真实执行版本，保留历史原样；本次未用已修复 harness 盲验或改写它。
- 只读计算忽略目录原始 100-run batch 的 SHA 与正式报告登记值一致；仅比较 hash，没有读取、展示或复制 batch 正文。
- staged 文件名扫描未发现 `.env`、raw/tmp、数据库、模型权重、私钥/PEM、私有 case 文件或运行态产物。staged 文本的有限 secret-pattern 扫描没有命中。逐份核对的交接、TASK、README/PROJECT 与最终两轴报告未披露私有题面、case id 或真实消息正文。

## 文档版本、证据与口径

- staged 文档统一标记 2026-10-09 的本地交付；分支起点为 `170fac0…`，最终 driver/harness 源码为 `cbca5d15bd40bd200f542d0eeaa1bc8192af9424`。待验收/进行中的状态与更广范围仍未完成的说明一致。
- 原真实 100 行批次继续绑定执行 HEAD `00b397443bd7258d2166c6445ac4ac066cefd21d` 和执行工具源码 `739f13ead0c53ce9d82519efc30f51263e29ab45`，修复后未重跑或重评分。100/100 attempted 与 100/100 capture；`guide_run=99`、`runner_failed=1`；机器 verdict pass/fail/unknown 为 66/30/4。核心 20 项三次结果为 44/13/3，严格 11/20；15 秒阈值是 100 个样本全部通过，不代表质量或人工验收通过。100 行均未人工 review。
- 正式批次 Graph 调用为 0。Graph build 与 local/global smoke 是独立组件证据，查询 deadline 为 180 秒，分别约 18.0 秒与 18.704 秒；不等于 Guide 15 秒预算通过。Memory 有 90 个成功 extraction、usage unknown、自然 Dream 0；另一次合成 10 条触发的 Dream smoke 独立计数。
- 四模块 35 passed/14.03s 对应源码快照 `4008faacae169d18de80f6a444f59c47a93915b7`；最终五个 harness 测试对应 `cbca` 工作树的签名清理。两个测试阶段重叠，不相加成 40，也不称为 cbca 上重跑的 35 项。
- 在本次 staged diff 中新增或变更的 31 个相对本地 evidence 链接及 Markdown anchors 均可解析。未要求重验 `PROJECT.md` 中未由本次改动引入的历史 archive/reference 链接。

无发布前置阻断项。主会话可在提交后按用户授权执行普通 push，并读回远端 SHA；不得把本报告或旧评测证据表述为整体已验收。

## Post-publication 文档增量

主会话已报告源码/报告候选 `3cc8d804bb3fbd7f405bfb73f4f44c65b3550205` 普通 push，并于 `2026-10-08 16:55:38 UTC` 用 `git ls-remote` 读回同一分支 SHA；发布回执 `REAL-PUBLICATION-RECEIPT.md` 中记录了命令和候选 tree `07118095d8fd4b801e8a8401b98887f1d1f56d56`。当前本地 HEAD 与 tree 均和回执候选相符。本 Tester 未执行 push，也未独立访问 remote。

候选 A 之后的暂存增量仅含四份 Markdown：handoff、主 TASK、05 TASK 与发布回执；无源码、测试、fixture、运行态或索引文件。四个新增相对本地证据链接均解析；文件名检查未发现密钥/数据库/私有 case 产物，有限 secret-pattern 扫描无命中。文档把“已核实 A 发布”与之后尚未推送的文档状态 B 分开；B 的完整 SHA 待主会话提交、普通 push 及读回后在主回复中给出。本报告本次增量另行 stage 后，`git diff --cached --check` 再次退出 0；未运行测试、模型、服务或构建。

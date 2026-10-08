# 本轮结束时未提交文件清单

本清单由 Git 路径元数据生成，不读取原工作树未提交文件的内容。

## 新验收工作树

目录：`Ceres2-integration-20261008`；detached HEAD `170fac0bc75fcc855897b073337ba218abeb5b7d`。产品目录无差异；本轮未 stage、commit 或 push。

以下 14 份是本机准备／执行／去敏证据，保留为未跟踪材料；没有把本地新证据混入已发布的集成源码版本。清单包含自身。

- `work/local-cloud-integration/local-acceptance-20261008/ACCEPTANCE-PLAN.md`
- `work/local-cloud-integration/local-acceptance-20261008/LOCAL-ACCEPTANCE-RESULTS.md`
- `work/local-cloud-integration/local-acceptance-20261008/UNCOMMITTED-FILES.md`
- `work/local-cloud-integration/local-acceptance-20261008/bge-download-record.json`
- `work/local-cloud-integration/local-acceptance-20261008/browser-firefox-run-11.md`
- `work/local-cloud-integration/local-acceptance-20261008/config-preparation-receipt.json`
- `work/local-cloud-integration/local-acceptance-20261008/download_locked_wheels.py`
- `work/local-cloud-integration/local-acceptance-20261008/download_pinned_bge.py`
- `work/local-cloud-integration/local-acceptance-20261008/firefox_webdriver_journey.py`
- `work/local-cloud-integration/local-acceptance-20261008/frontend-entry-smoke.json`
- `work/local-cloud-integration/local-acceptance-20261008/hybrid-dev-smoke.json`
- `work/local-cloud-integration/local-acceptance-20261008/hybrid_dev_smoke.py`
- `work/local-cloud-integration/local-acceptance-20261008/knowledge-requirements.freeze.txt`
- `work/local-cloud-integration/local-acceptance-20261008/start-local-frontend.mjs`

## 被忽略的本机生成物

- `.env`：测试结束后由根会话以0600创建空凭据／空模型配置；用户本机填写，不提交。创建顺序与摘要见 `config-preparation-receipt.json`。冻结 Tester 报告描述的是此前无 `.env` 的测试状态。
- `.venv/`、`.venv-graphrag/`、两处 `node_modules/`、`dist/` 与包管理缓存：本机依赖和构建生成物，由版本锁与执行证据说明来源。
- `.cache/huggingface/`、`data/indexes/hybrid.sqlite3`：模型和新索引；固定 revision、文件与manifest hash在Tester报告，不作为源码提交。
- `data/runtime/ceres2.sqlite3`：仅含新静态demo商品／Offer／Store，无用户、订单或会话；运行库不提交。未构建GraphRAG图索引或checkpoint库。
- 本轮 `tmp/` 和 `*.log`：wheelhouse、独立浏览器工具、每轮截图／原始代理记录、合成TLS私钥、日志等本机证据或临时产物；不随普通Git add入库。详见冻结Tester报告。

## 原本地 main

原工作树 `Ceres2` 仍在main `b118dbea3852026c6a04c790b1e27df67c3c9c18`；当前逐文件Git状态共有 53 项。本轮不修改这些文件；原因是保留原有技能调整、现场工作及独立验收材料，不把它们带入新候选。下列仅为Git状态与路径，不代表对其内容完成审查。

- ` M .agents/skills/ask-matt/SKILL.md`
- ` M .agents/skills/code-review/SKILL.md`
- ` M .agents/skills/implement-spec/SKILL.md`
- ` M .agents/skills/implement/SKILL.md`
- ` M .agents/skills/retro/SKILL.md`
- ` D .agents/skills/setup-matt-pocock-skills/SKILL.md`
- ` D .agents/skills/setup-matt-pocock-skills/agents/openai.yaml`
- ` D .agents/skills/setup-matt-pocock-skills/domain.md`
- ` D .agents/skills/setup-matt-pocock-skills/issue-tracker-github.md`
- ` D .agents/skills/setup-matt-pocock-skills/issue-tracker-gitlab.md`
- ` D .agents/skills/setup-matt-pocock-skills/issue-tracker-local.md`
- ` D .agents/skills/setup-matt-pocock-skills/triage-labels.md`
- ` M .agents/skills/to-spec/SKILL.md`
- ` M .agents/skills/to-tickets/SKILL.md`
- ` D .agents/skills/triage/AGENT-BRIEF.md`
- ` D .agents/skills/triage/OUT-OF-SCOPE.md`
- ` D .agents/skills/triage/SKILL.md`
- ` D .agents/skills/triage/agents/openai.yaml`
- ` D .agents/skills/wayfinder/SKILL.md`
- ` D .agents/skills/wayfinder/agents/openai.yaml`
- `?? .agents/skills/chief-of-staff/SKILL.md`
- `?? .agents/skills/chief-of-staff/agents/openai.yaml`
- `?? .agents/skills/claude-handoff/SKILL.md`
- `?? .agents/skills/claude-handoff/agents/openai.yaml`
- `?? .agents/skills/grill-me/SKILL.md`
- `?? .agents/skills/grill-me/agents/openai.yaml`
- `?? .agents/skills/grilling/SKILL.md`
- `?? .agents/skills/grilling/agents/openai.yaml`
- `?? .agents/skills/handoff/SKILL.md`
- `?? .agents/skills/handoff/agents/openai.yaml`
- `?? .agents/skills/loop-me/SKILL.md`
- `?? .agents/skills/loop-me/agents/openai.yaml`
- `?? skills-lock.json`
- `?? work/live-validation/run_live_batch_deepseek_once.py`
- `?? work/next-experience/live-acceptance/README.md`
- `?? work/next-experience/live-acceptance/baseline-provenance.md`
- `?? work/next-experience/live-acceptance/cursor-handoff-snapshot.json`
- `?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007.tar.gz`
- `?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/MANIFEST.md`
- `?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/acceptance/desensitized-regression-20261007.json`
- `?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/freeze/thinking-disable-source-freeze.json`
- `?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/patch/4bed9c8-to-worktree.patch`
- `?? work/next-experience/live-acceptance/export/ceres2-4bed9c8-to-worktree-20261007/tests/test_official_deepseek_thinking.py`
- `?? work/next-experience/live-acceptance/holdout/SHA256SUMS`
- `?? work/next-experience/live-acceptance/holdout/cases.json`
- `?? work/next-experience/live-acceptance/holdout/language-rubric.md`
- `?? work/next-experience/live-acceptance/observers/memory_watch.py`
- `?? work/next-experience/live-acceptance/observers/node_usage.mjs`
- `?? work/next-experience/live-acceptance/observers/provider_usage.py`
- `?? work/next-experience/live-acceptance/primary-path-language-review.md`
- `?? work/next-experience/live-acceptance/spec-live-fix-review.md`
- `?? work/next-experience/live-acceptance/standards-live-fix-review.md`
- `?? work/next-experience/live-acceptance/thinking-disable-source-freeze.json`

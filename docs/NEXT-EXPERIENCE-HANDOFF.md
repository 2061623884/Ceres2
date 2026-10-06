# 下一阶段体验：接手与剩余验收

## 本次交付与精确版本

- **当前已完成受控验证、待外部验收的源码：`0c752a2b252d797297b4b073883571884ff6855a`**，集成分支 `ceres2/next-experience-20261006`。冻结目录：`Ceres-workspace/worktrees/next-final-fixture`。后续文档提交不改变该源码候选；任何产品修复都必须换版本并重验。
- 用户已明确授权整理并推送至独立 `2061623884/Ceres2`；**当前是授权后待发布状态，尚未声明推送或部署完成**。发布采用经独立审查的最终 tracked 文件树，在远程 main 基线 `64ca7b6b9a7aa113aa42d54270604913f6c19d58` 上形成集成提交，保留公开历史、不修改原 Ceres。上述 `0c752a2` 是云端测试来源 SHA，不保证在 GitHub 可 checkout；公开发布 commit 与测试来源的映射在推送后记录。接手前核对实际公开分支／commit 和 `git status --short`，保留原工程、配置和业务数据库。
- 当前状态以[总 TASK](../tasks/ceres2-next-experience.md)及[TASK10](../tasks/ceres2-next-10-candidate-evidence.md)为准。本说明不建立另一份实时进度表。

已实现：真实模拟供给驱动的零食／饮品选类与筛选、稳定问题／选项身份、明确加购；单次 Kev 职责／能力判断和用户控制跳转；两角色无订单政策；已有活动的成品选购；结果先出现、随后受校验的增量介绍；售后结果／失败保存及回购物；按需 Prompt 模块。共70个模拟SKU／Offer，沿用Python业务权威、实际Pi／LangGraph与原事务／记忆／人工保护。

最终审查修复包括普通搜索／比较条件保护、跨货架明确搜索、已知数量、购物＋政策复合结果、表达诊断原因及死代码清理。原发现与闭合分开保存：[Standards](../work/next-experience/10/standards-review.md)、[Spec](../work/next-experience/10/spec-review.md)、[修复说明](../work/next-experience/10/review-fixes.md)。两轴独立复审已关闭具体实现问题，同一最终候选的完整受控验证已通过；真实provider／浏览器／语言品质／holdout／V3独立比较和本人验收仍开放。

## 证据：不要把局部通过当最终通过

**同一最终冻结0c752a2受控技术验证通过：** 完整backend426/426（pytest645.95秒）、37个DOM/client场景、runtime/frontend build和严格TypeScript、隔离OS restart1/1。四次capture源未变，238backend源／280build-UI源与文档后继integration完全相同，两独立review及fixture窄复核闭合。01–09受控门槛已放行；TASK10仍待外部与本人验收。

[最终Tester报告](../work/next-experience/10/final-controlled-verification.md)、[精确等价](../work/next-experience/10/final-controlled-equality.json)、[当前环境／哈希](../work/next-experience/10/final-fixture-environment-source.json)提供完整记录。历史e267fc9的403通过、d2166e3的424/1及其他早期失败均保留，未拼成当前结果。受控SDK／loopback／React DOM不是实际provider／浏览器验收。

最终结果入口：[运行计划](../work/next-experience/10/final-run-plan.md)、[覆盖清单](../work/next-experience/10/coverage-manifest.json)、[集成证据索引](../work/next-experience/integration.md)。计划文件中的pending字段是当时准备快照，实际结果以TASK10和对应原始记录为准。没有声明lint脚本，故lint应记“未配置”，不写通过。

已做的OS重启探针限于隔离Linux进程组SIGKILL／重启、SQLite已提交结算回执、运行中Pi中断／不重放及显式继续；该探针已在最终候选单独重跑通过。它不证明任意断电、磁盘损坏、多机切换或后台记忆的全部OS重启场景。

## 本地入口（仅供获准体验；这些命令未由本说明执行）

使用Linux；本轮受控环境为Python3.12.14、Node24.19.0、npm11.9.0。新机器由Tester按 `backend/requirements.lock` 和两个 `package-lock.json` 安装／构建，不复用旧工程依赖。已有稳定同版依赖与测试证据时，不要求用户再跑整套unit suite。

开始前，由用户在本地可信编辑器自行配置新的 `.env`，不要上传内容或复制旧凭据。主模型、提取模型和Dream模型保持用户实际批准值，本轮没有重新选型。除模板的 `OPENAI_BASE_URL`／`OPENAI_API_KEY`／`LLM_MODEL` 外，自动新文字职责／能力判断还需 **`KEV_BASE_URL`**，模板提供空占位。它不是应用启动必填项：空值／服务失败会显示职责判断不可用，用户可明确手动选角色续接，没有自动模型兜底。配置服务须支持当前 `/v1/systemone` 联合职责／四能力合同；不能猜地址或把手动继续算自动路由成功。独立人工入口另需 `HUMAN_OPERATOR_TOKEN`。使用全新明确的本地数据库／checkpoint路径，别指向旧数据。

启动服务及对话可能触发真实模型、记忆后台任务和费用；仅由用户在同意相应数据发送与费用后亲自操作，或另行明确授权。不要直接套用旧 `run_live_batch.py` 的历史模型、固定用例／旧41项成绩来声称本候选已验证。

以下命令从**准确候选仓库根目录**执行；已有Pi构建且匹配本候选时无需重复构建：

```bash
(cd runtime/pi && npm run build)
(cd backend && ../.venv/bin/python -m app.services.seed_service)
(cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8012)
```

第二个终端同样从仓库根目录：

```bash
(cd frontend && npm run dev -- --host 127.0.0.1 --port 8443)
```

浏览器打开 `http://127.0.0.1:8443`；Vite将 `/api` 与 `/media` 代理至8012。健康入口为 `http://127.0.0.1:8012/health`，其成功不证明provider可用。端口占用时先查原因，不杀未知进程或擅自开放公网。命令依据实际package scripts、seed模块、config和Vite代理；旧接力文档的65商品／旧角色入口／固定模型不覆盖本次版本。

## 用户剩余验证：只补当前缺口

1. **真实页面和真实模型的一次完整旅程**：先问“来点零食，预算20元”并选择类型／数量；再从饮品货架明确问其他品类、加饮食限制；核对卡片实际条件、已知数量、旧选项失效和选择不等于加购。一次复合购物＋政策问题必须两部分都有结果。
2. **角色与时序**：在没有订单时问政策；跨角色接受／拒绝、明确回购物并附新要求、刷新／关闭重开／后退前进／连点。确认不会擅自切换或漏掉原请求。卡片应先可用，介绍随后开始；记录首次事实、可操作、首段、完成时刻，慢／失败也保存，不把30／15秒保护当SLA。
3. **活动与交易闭环**：点已有活动卡选择成品；普通修改／退出不遗留旧限制或旧授权。单独确认加购、再单独模拟结算；同一订单售后提案／明确提交／回购物。申请只能表述“已提交”，失败和响应丢失不能重复业务写入。
4. **自然中文**：查看整个屏幕上卡片、host事实和连接语是否简短、不重复、来源条件完整；两角色／无匹配／失败都取样。07指令长度实际增加（Keke925→1656、Momo935→1665 Unicode codepoints），不是token／费用改善。真实模型前后成对比较、盲评及真实usage／时延尚未完成。
5. **独立验收**：由独立负责者执行可用且获准的未见holdout及冻结V3业务比较，不把公开开发用例改称holdout。真实提取／Dream及长周期行为另行观察；受控触发阈值／时钟推进不等于已经观察了真实24小时生命周期。最后由用户确认体验，agent不能代签。

只分享去敏后的结果、错误码、必要截图和时间记录，不分享凭据、headers、数据库或未审查的provider原文。当前已知非阻塞React `ShelfScreen` render期间更新 `ShoppingApp` 警告保留在日志，真实页面验收仍需关注，不能靠压制warning算解决。

## 收尾与保留

工作树暂不自动清理。只在其提交已进入集成、没有独有源／报告／日志、Tester不再运行且已保留必要证据后，逐个确认并删除本次明确创建的可恢复工作树；不使用force、reset、盲目prune或删除未知文件。历史冻结目录与原始证据可继续保留。本次仅新增独立 Ceres2 仓库发布授权；部署和清理不包含在此次发布中。

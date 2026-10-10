# Ceres2 云端重建：执行决定与交付契约

日期：2026-10-07。状态：规划冻结，尚无本轮产品实现或测试成绩。当前任务状态只由 [总 TASK](../tasks/ceres2-judge-prefetch.md) 维护。

## 1. 授权时序、真实基线与不继承原则

用户最新授权从 GitHub 已发布源码重新开展四票实现，使用 implement-spec、TDD、Agent Team、可追溯提交与分支推送。它取代 2026-10-06 草案中的“仅 to-spec / to-tickets”“未授权 implement”“不测试、不提交、不推送”限制，以及早期重建阶段仅针对当时工程的“无 remote／禁止推送／仅 16 票”限制。只覆盖本次已批准范围；不授权改前端、部署、合并 main、改模型／额度或破坏性清理。原始草案与历史记录保留其时点含义，不能再次据此阻止已授权实施，也不能据最新授权追认历史验收。

- 干净起点：已发布 `main` 的真实提交 `4bed9c891261e382122d424825b649989ea92c92`，tree `73bb2a44f22fa504448fbc19ab1fb6fec095d724`。
- 集成分支：`ceres2/judge-prefetch-rebuild-20261007`。基线、归档哈希与源码清单见 [bootstrap](../work/judge-prefetch/rebuild-bootstrap.md) 和 [manifest](../work/judge-prefetch/rebuild-baseline.json)。
- 本次是新实现，不伪造或恢复不可得的 `f45c4ff92f96f535d156a2f88053ae10e8486fa1` 祖先，不称已取得其完整源码，不继承其测试。旧 `0c752a2` 的 426 backend／37 DOM、本地 24 文件补丁和局部 13 passed／1 failed 都不是当前候选成绩。
- 原补充稿“必须先取得 f45c4ff 才合并”的门槛针对恢复／合并旧候选。最新决定选择从公开基线重建，因此不再把取得丢失候选作为新实现开工条件；仍不能声称对其完成跨版本代码审查或完整合并。
- Python 仍是身份、事实、授权、事务与回执唯一权威；Pi 售前与 LangGraph 售后分工、人工责任和模拟业务限定继续有效。

## 2. 保留四票及显式前端负责人拆分

功能依赖保持 **01 → 02 → 03 → 04**。没有并行实现依赖票的许可，也没有新建“05 传输优化”票。当前云端交付包含服务端、runtime、公开 HTTP/SSE／typed action 契约、受控证据、文档及前端交接。

用户明确自行在本地实现前端。因此所有 `frontend/` 实现和前端测试文件写入均不在云端范围。原票涉及 typed UI、页面展示、DOM、真实浏览器和用户体验的条目不删除，按如下负责人拆分：

| 原票 | 云端实现者必须完成 | 用户本地前端／验收保留项 |
| --- | --- | --- |
| 01 | Coco-only Kev、Momo 直达、结构化返回动作的服务端行为、身份／opening／版本／重放保护、完整首次上下文；公开 action 契约与 fixture | 切换建议／拒绝／按钮、typed 客户端适配、页面与重连竞态；浏览器验证没有文字自动切页或业务重放 |
| 02 | 政策判断／预取／同 Pi 真实输入与引用、全部失败语义、混合请求完整性；既有 SSE 与事实投影可消费 | 实际页面正确呈现政策来源、未知／部分／错误、购物结果及确认边界 |
| 03 | 确定性同范围复用与补查、多有效引用、请求／来源版本／取消隔离、计数 | 页面中多范围来源与混合结果的同版呈现和刷新／恢复行为 |
| 04 | 同候选服务端/runtime 集成、受控验证、可用真实 provider 对照、两轴审查、版本／未测清单与交接包 | 使用交接的准确服务端提交及自己的前端提交完成 DOM／真实浏览器与本人验收 |

01–03 的云端功能及受控门槛完成后可向下一票交接；未完成的用户所有前端项仍列“待本地验收”。这允许后端依赖图推进，不把未测的 typed UI／端到端验收记为通过。04 仍被 03 阻塞；仅可提前准备非业务交付的证据模板和独立支持项。

## 3. 冻结的公开服务端兼容策略

依据基线 `backend/app/api/navigation.py`、`backend/app/api/guide.py`、`frontend/src/lib/chatNavigation.ts` 及 App 的调用方核实，优先复用既有路径和载荷，不为前端移交发明第二套导航 API。

### 导航与文字准入

1. 保留 `/api/v1/navigation/sessions/{session_id}` 下的 `/opening`、`/routes`、`/prompt-displayed`、`/switches` 路径及当前请求字段。内部产品名称 Coco 继续映射 wire role `keke`，Momo 为 `momo`，不把名称清理扩大成 breaking rename。
2. `POST /routes` 继续接收 `request_id`、`opening_id`、`role`、完整 `message`、可选 `selected_object`／`role_session_id`。可信 owner 来自既有身份，不从载荷新增 owner 授权。请求原文、身份与已确认数据不因兼容处理重写。
3. 新 Coco 文字只执行一次入口角色判断。yes 返回现有 `status: switch`、`target_role: momo` 及明确确认所需原文／request 引用；在接受前不赋予目的角色准入。no／uncertain／timeout／error 都返回可由既有客户端继续的 `status: ready`、`target_role: keke` 和同一 `routing_request_id`；真实判断结果、失败原因、耗时与规则版本分别记录，不把故障写成 no。
4. 新 Momo 文字返回 `ready` 并直接走既有售后入口，零入口 Kev、零政策 Kev；纯／复合“回可可”文字也不返回 `navigation` 或自动续接购物。结构化购物／售后动作绕过这两个判断。
5. 已有 `RouteDecision` 字段 `routing_request_id`、`original_message`、`selected_object`、`target_role`、`show_prompt`、`continue_original` 保持意义。`capability` 不再驱动新请求；不得填造 exploration 或依赖 null 触发旧裁剪。允许兼容保留旧字段，但首次 Prompt／工具／上下文三个消费者必须一同脱离四分类。
6. 新流程不产生 `navigation` 自动文字返回，也不再用 `clarify`／`unavailable` 阻断应继续可可的文字。保留旧客户端对旧枚举的类型声明不代表恢复旧行为。诊断字段若新增，应为加法字段，并在 01 的公开 fixture／交接中固定实际名称，不能依赖旧 UI 读取它才能继续。
7. `POST /switches` 保留 `opening_id`、`target_role`、`accept`、可选 `routing_request_id`。明确接受建议必须携带其 `routing_request_id`，服务端验证其仍属于当前 owner／opening／版本并仅消费一次原文。`accept: false` 留在原角色，不制造 handoff，不自动执行请求或写入。
8. 角色按钮没有 `routing_request_id`（省略或 null）时是显式纯导航，返回 `handoff: null`；尤其 Momo → Keke 按钮不能隐式捡起 pending／accepted 原文。按钮本身不调用 Kev、不继承购买或退款授权。不能为兼容旧隐式推断而恢复已删除的文字返回续接。
9. 保留当前 opening 提示配额及显示 ACK 意义。角色、opening、owner、引用、请求原文与版本过期沿既有 4xx 冲突契约明确拒绝；对旧未完成 11 类／自动返回回执明确失效，可使用既有 `STALE_NAVIGATION` 并解释重新发起，不猜测升级旧授权。旧已完成业务通过原回执安全读回，不因此再次导航或执行。

### Guide、SSE 与政策事实

- 保留 Guide `/runs`、`/turns/stream`、`/runs/{run_id}/events`、`/runs/{run_id}/stream`、停止与回执入口，以及现有 request/version/displayed refs 校验；续接仍沿用原 `request_id`，不能换 ID 绕过幂等。
- 保留 SSE envelope 的 `protocol_version`、`run_id`、`sequence`、`type`、`session_id`、`target_task_id`、`payload` 与结果先行顺序。新诊断不替换既有事实消息或要求未交付前端才能收到终态。新事件／字段若确有当前消费者，必须由该票固定兼容规则和 fixture 后交接，不臆造全新协议版本。
- 政策预取的完整证据、实际查询参数、来源版本和真实 `policy_ref` 在 Python 当前请求登记并实际送达同一个 Pi。对用户展示仍通过既有宿主事实消息与结果投影，不把未真实发生的模型 tool call 伪装成 tool result。
- 03 的多引用扩展发生在宿主／runtime 实际消费契约；用户可见输出保留每个有效范围和来源。即使最后采用内部 `policy_refs` 等新字段，也必须有真实调用方，兼容现有单引用结果，不要求前端先改才能保留证据内容。

以上冻结的是路径、原文／请求身份、状态继续性、按钮／确认含义与安全行为。实施者可确定最小加法诊断字段，但不得改动这些语义或以“旧 UI 无法满足”为理由偷偷改前端。当前 UI 已使用 ready 继续和显式 route ID 接受，因而主导航行为具备兼容基础；这只是源码判断，不是已验证的浏览器兼容结论。

## 4. 写入所有权与可并行支持项

主会话负责在启动前把下列角色绑定到唯一实际工作者／worktree；转交须记录交接提交和文件列表。没有明确交接时，前一所有者仍保留写入权。

| 所有者 | 独占范围 | 转交／限制 |
| --- | --- | --- |
| 规划维护者 | 本规格、四票及总 TASK、PROJECT 当前阶段、本文 | 仅规划导入；首规划里程碑由集成者提交 |
| 01 实现者 | `backend/app/services/kev_provider.py`、`navigation_service.py`、`backend/app/api/navigation.py`／`guide.py` 所需准入；`pi_product_turn_service.py`、`pi_product_runtime.py`、`runtime/pi/src/worker.ts`、`prompt-modules.ts` 与首次 Prompt 的必要改动；01 专属 fixture | 先完成三个上下文消费者；共享入口、runtime、Prompt、fixture 经提交后向 02 交接；导航修复由主会话再指派单人 |
| 02 实现者 | 接收上述必要共享文件；政策判断、预取、Python 引用登记、同 Pi 输入、政策 Prompt／fixture | 不并行重写 01 导航；交付真实证据／引用／错误／计数后向 03 转交 |
| 03 实现者 | 当前请求证据复用、查询范围／版本、引用适用性、多引用结果及 fixture；已交接的公共 runtime 文件 | 不建设跨请求缓存平台；交付完整功能给 04 |
| 04 证据维护者 | 集成用例、冻结 manifest、运行记录、评审与交接 | 无前三票业务补齐权；发现缺陷退回所属责任人修复再重新冻结 |
| Tester | 全部依赖安装、测试、lint、typecheck、build、受控与授权真实实测命令 | 实现者写红测但不运行；没有“仅快速跑一下”例外 |
| 集成者 | 集成分支、合并、提交、推送及远端核实 | 不与实现者同时改共享产品文件；只提交已审阅精确清单 |
| Standards／Spec 审查者 | 两轴独立只读审查 | 不修改产品、测试或候选；有效发现集中交实现者 |

官方 DeepSeek thinking 支持作为原四票的**有界传输支持项**登记在 04 的证据范围，可在 01 之前或其期间准备，不改变 04 被 03 阻塞的业务依赖。若要并行，使用独立 worktree／branch，并仅拥有以下与 01 非冲突文件：

- `backend/app/core/deepseek_request.py`、`backend/app/mercury/provider.py`、`backend/app/services/memory_model.py`；
- `runtime/pi/src/official-deepseek.ts`、`runtime/pi/src/result-expression.ts`；
- 其独立传输测试文件及经核准、未被其他工作者写入的 memory／Mercury wire 测试；不得改共享 `conftest.py`、依赖锁文件、配置、Prompt 或 frontend。

`runtime/pi/src/worker.ts` 与 01 明确冲突，**排除在并行支持项写入范围外**。支持项把所需 import 与两处请求组装改动作为可审阅片段交给 01 当前所有者，由其串行整合；整合后再验证完整 Pi 传输路径。若实际需要其他共享文件，先缩小并行范围或重新交接，不以不同函数／小 hunk 当作可以并行写同文件的理由。

## 5. 传输与 Prompt 的采纳边界

### 官方 DeepSeek 关闭 thinking

选择性重新实现本地审阅过的官方端点请求配置，不整体应用 24 文件补丁。精确规范化 hostname 为 `api.deepseek.com` 时显式发送 `thinking: {type: disabled}`；其他主机（包括后缀伪装域名）不新增 thinking／reasoning_effort 字段，字段缺失不能用 null 代替。保留已有 JSON 输出需要、取消、usage 收集及传输语义。

- 保留当前配置的 provider、模型、temperature、输出额度、重试及 deadline；不新选 `deepseek-flash`，不增加 1536／512／256 或其他额度，也不把本地样本配置当成云端用户决定。
- 本地审查只说明补丁来源与测试缺口。新的受控 wire fixture 必须区分字段不存在与显式 null，覆盖精确官方域名、大小写规范化、非官方及后缀 look-alike；主 Pi、其 validator、结果表达及其 validator、Mercury／memory 实际请求路径分别核对。
- 官方配置是用户已选择的实现项，不等于历史失败原因已被证明，也不等于真实模型行为或性能通过。

### Prompt 改善跟随业务票

来源为已核查的 `shareAI-lab/learn-claude-code` 固定提交 `ce8f9f186058939da54c9d6fead78dfb5d0fd6c3`；参考 [s01 主循环](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s01_agent_loop/code.py#L95-L126)、[s02 工具契约](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s02_tool_use/code.py#L136-L185)、[s07 按需知识](https://github.com/shareAI-lab/learn-claude-code/blob/ce8f9f186058939da54c9d6fead78dfb5d0fd6c3/s07_skill_loading/code.py#L89-L144)。它是教学参考，不是政策缓存实现，也不提供本项目性能证明。

- 01：短且稳定的角色核心，完整原请求、当前任务、活动问题、待澄清及有效引用；删除对四能力输出的上游依赖。
- 02：政策证据作为低信任事实；工具事实优先，未知不猜；完成条件覆盖当前所有明确子请求或说明需用户输入／授权的边界，不能“某工具成功就收口”。
- 03：删除“混合政策必须另行再查”的无条件指令。同请求同范围、同有效来源已有充分证据时复用；新问题、条件变化、证据缺口、失效或此前失败可以补查。
- 不凑候选数、不放宽糖／数量／预算条件、不以商品名称推断属性；连接语不复述宿主已展示事实，同时保留未知、模拟、提交申请与到账区别。工具与模块选择规则只保留一个可信维护位置。
- 不复制整套教程、不新增第二回答 Agent、不以逐失败句堆补丁代替完整混合请求回归。Prompt 与关闭 thinking 分别留变更来源和证据。

## 6. 已批准测试接缝与 TDD 执行

原规格已明确批准公开 HTTP/SSE、typed action／UI、模型实际输入、provider／检索边界计数及权威业务读回。不新增访谈、grilling、专用测试 API 或私有函数 seam 来重新审批这些已批准接缝。typed UI 的浏览器执行按第 2 节移交，公开 typed action 服务端接缝仍由云端验证。

每个纵向切片严格执行：实现者准备一个行为红测 → Tester 在准确工作树运行并记录预期失败 → 实现者最小实现 → Tester 同接缝绿色及必要相关回归 → 下一行为。红测和绿测分别保留源码／diff 摘要、命令、退出码与原始输出。避免一次写全套想象中的测试、再整包补实现；重构留到 review 阶段。测试观察外部行为，不通过私有方法或篡改内部状态自证成功。

原票全部安全 fixture 保留：两 owner、request 重放与不同原文冲突、旧导航及回执、已确认加购／售后、跨请求／版本／伪造 ref、取消／恢复、相关任务与“第二个”、政策空／部分／异常、多问题与补查。独立传输支持项同样需要自己的 red → green，不能借旧单测成绩通过。

## 7. Deadline 与性能证据的实际边界

基线代码核查发现两条真实路径，须在 02 适配中分别记录：

- 现有 UI 先 `POST /navigation/.../routes`，再发 Guide run；前一个独立入口 Kev 耗时不包含在后一个 run 的 30 秒 deadline 内。
- 直接 `POST /guide/.../runs` 或 `/turns/stream` 在调用 `authorize_text` 之前创建 `time.monotonic() + 30.0`；若该路径内部首次判断角色，入口耗时实际占用该 deadline。不能笼统写“旧 Pi deadline 从不包含入口”。

新流程沿已批准提案，使政策判断／预取与 Pi 使用同一个既有可可运行阶段 deadline，不逐阶段重置、不增加隐藏重试或预算。入口仍遵循现有独立 provider 超时，但是否也消耗直接准入路径的运行时间必须与实际实现一致。每次进入政策检索／Pi 和发布前检查取消、当前请求及剩余时间；整轮已截止时不因 fallback 启动模型。

端到端一律从第一次可信接纳该原请求起算，覆盖分离 `/routes` 的耗时；记录判断、预取、主模型和表达阶段，不能只展示 Pi 内部时间。若调整上述路径的起算位置，必须显式记录理由、受影响路径与回归，不把工程适配说成用户批准了新数值上限。

## 8. 候选、里程碑与完成用语

1. 首里程碑是规划／授权差异与真实基线入库，不代表功能通过。
2. 每个功能里程碑固定一个提交及源码树，Tester 证据明确对应该提交或完整未提交 diff；合并后重新核对必要受影响与集成门槛，不拼接不同候选的成功记录。
3. 只有本地 commit 成功、发布到授权分支成功且通过远端 ref 读取核实远端完整 SHA，并证明远端 tree 与本地已冻结 tree 完全相同后，才能向用户说“该里程碑已推送”。主会话采用 GitHub connector 发布时可能生成不同 commit SHA；必须保留本地 SHA → 远端 SHA、相同 tree、目标分支和读取回执的持久映射，不要求两个 commit SHA 相等，也不能因 SHA 不同跳过内容验证。无远端权限时保留本地成果并报告具体阻塞，不能把网页／附件链接等同于已发布。
4. 总 TASK 记录精确提交、来源、独立审查状态和证据链接。工作树与输出中不提交秘密、旧数据库、依赖目录或本地凭据。
5. 最终报告分别列：受控服务端/runtime、受控 wire、真实模型、typed DOM／真实浏览器、用户本人验收。无凭据、额度或前端时写 not run／阻塞；不写零 tokens／零成本；不把库初始化、空候选或售后申请提交写成真实业务成功。
6. 真实 provider 采样前冻结有限用例、重复次数、顺序、实际配置、数据／Prompt 版本及已授权整次时间或费用上限；缺少授权不启动无界付费试验。样本不足不能支持稳定 P95／降本结论；质量失败不能由速度抵销。
7. 01–03 云端门槛和两轴审查完成可报告“云端实现与受控验证完成，待本地前端／真实验收”；只有原定的所有适用验收得到同版证据后才写整体已验收。

## 9. 本地真实问题的保留交接

下列来自最新本地补充，保留在最终交接，不自动扩大当前四票为商品或记忆重设计：

- 稳定偏好仍有 `PI_UNGROUNDED_BUSINESS_TEXT`／422，工具列表空、Guide message 未提交；需真实脱敏 verdict、工具阶段、消息与 extraction job 追踪。
- 茶／饮水虽走到 `guide_request → explore_products`，候选仍为 0。需区分语义召回、权威糖属性、canonical type、包装 `bottle`、`pack_count=12` 与销售单位“箱”，合法无供给不可伪装成功；不能按名称推断无糖或自动放宽条件。
- 旧能力按钮曾续接原请求，不证明新导航合同已验收；需用户本地前端同版验证原文只消费一次、业务确认独立。
- 自然记忆目前仅报告 ownerB 一条 automatic；首次真实 Dream 和 24 小时观察未开始。原交接门槛仍保留：正常对话达到至少 10 条有效 automatic 记忆，不造记录／改时钟／强制调用；首次真实 Dream 成功后按 completed_at 开始实际 24 小时只读观察。当前重建不自动启动或伪造此项验收。

若其中某个问题由本次改动直接引起，或确实阻断当前已批准 runtime 的必要公开旅程，先提供最小复现与所属票归属，由该票修复最小必要范围。其他缺口只移交，不能顺便更换商品建模、放宽事实守卫、改记忆设计或承诺修完全部历史外部验收。

## 10. 输入来源

- 原 2026-10-06 四票规格／总 TASK／01–04，从 `Ceres2-Kev-policy-review/Ceres2-next` 用户提供归档导入；原输入摘要见基线 manifest。
- 2026-10-07 `JUDGE-PREFETCH-HANDOFF.addendum.md`：本地补丁证据、前端所有权、真实失败、Prompt 方向；其旧候选恢复门槛按第 1 节更新。
- 2026-10-07 `prompt-guidance.md`：固定教程源码来源、三项采纳／重写／删除建议；本文已纳入必要决定与公开来源，不把机器上的外部输入路径当作仓库运行依赖。
- 本文建立时仅阅读源码并维护规划文件，没有运行测试、调用真实模型、修改产品或推送。后续状态以总 TASK 和对应候选证据为准。

# DeepSeek JSON-mode 与 Pi tool-call interim 兼容性

核查日期：2026-10-07。范围是当前真实 Pi 配置：`deepseek-flash`、`https://api.deepseek.com`、thinking disabled、streaming、`response_format: {type: "json_object"}` 与函数工具。未发送模型请求、运行测试或安装依赖；下文是官方 API 文档、当前安装 SDK 源码和已提供采样记录的交叉核对。

## 结论

DeepSeek Chat Completions 的请求模式允许同一个请求携带 `response_format` 和 `tools`：两者是同级请求字段，工具默认 `tool_choice=auto`。官方响应 schema 将 assistant `content`（可空）与 `tool_calls` 分列，流式 delta 也分别包含 `content` 与 `tool_calls`。因此文本块和工具调用在 API 数据模型中可以并存；当前采样也证明服务端接受了这种请求并返回了工具调用。不过，DeepSeek 文档没有给出 JSON Output 与 Function Calling 同时启用、且保证每次都有非空 assistant 文本的组合示例或该保证。不能据此断言模型普遍不支持组合，也不能把非空文本视为接口保证。[Chat Completions API：请求字段](https://api-docs.deepseek.com/api/create-chat-completion/)、[响应与流式 schema](https://api-docs.deepseek.com/api/create-chat-completion/)、[Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/)

DeepSeek 的 JSON Output 文档明确提示：JSON 模式偶尔可能返回空 `content`；建议 prompt 提到 JSON 并给格式示例、合理设置 `max_tokens`。Chat API 另说明，如果没有指示模型输出 JSON，它可能生成持续空白直到 token 上限。Ceres 当前 prompt 含 JSON 字样和 interim 对象示例，worker 将主轮 `maxTokens` 设为 1536，符合文档建议；这些建议不能消除文档承认的空内容情形。[JSON Output 指南](https://api-docs.deepseek.com/guides/json_mode/)、[Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)

## Pi 1.0.3 源码核对

- 当前锁定与安装版本为 `@earendil-works/pi-ai@1.0.3`、`@earendil-works/pi-agent-core@1.0.3`（`runtime/pi/package.json:10-13`; `runtime/pi/node_modules/@earendil-works/pi-ai/package.json:2-4`; `runtime/pi/node_modules/@earendil-works/pi-agent-core/package.json:2-4`）。worker 为 DeepSeek 主轮启用 JSON mode 并保留工具列表；`officialDeepSeekSampling` 对官方 host 附加 `thinking: {type: "disabled"}`（`runtime/pi/src/worker.ts:183-196`; `runtime/pi/src/official-deepseek.ts:1-7`）。
- OpenAI-compatible provider 构造请求时先写入 `tools` 与可选 `tool_choice`，随后将 `samplingParams` 合并到请求体；`response_format` 因此与工具字段一起发送，不会在 Pi 中因设置 JSON mode 而删除 tools（安装源码 `runtime/pi/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.js:566-615,747-752`）。
- 流式 parser 对非空 `delta.content` 建立并追加 text block，对 `delta.tool_calls` 独立建立并追加 tool-call block，完成时分别 finalize 两类 block（同文件 `353-395,426-453,470-488`）。它没有丢弃非空文本；null、未提供或空字符串不会创建 text block，空白字符串会作为非空 text block 保留。
- Agent core 从同一 assistant message 中筛出 tool-call block 来执行工具，保留整个 message（含其他内容块）作为本轮消息；stream adapter 将最终 message 发出 `message_end`（`runtime/pi/node_modules/@earendil-works/pi-agent-core/dist/agent-loop.js:140-180,260-320`）。因此目前未发现 Pi SDK 在 `message_end` 前过滤文本的接缝。
- Ceres worker 在 `message_end` 从 text blocks 合并字符串、解析 `interim_message` JSON、要求非空文本，并拒绝没有 tool-call 的最终 JSON；纯空白或空内容不会被发布为 interim（`runtime/pi/src/worker.ts:232-273`）。

## 对本轮样本的解释与边界

按本任务提供的真实样本记录，收紧提示后唯一完成的样本中，两轮带工具调用的 assistant message 分别出现空文本与 25 个空白字符，未出现可解析的 interim JSON。该结果与官方 JSON-mode 文档记载的空内容/空白风险相容；它不是“非 JSON 格式”错误的证据。SDK 源码表明，若响应中的 `delta.content` 真是 25 个空格，Pi 会保留这段文本，Ceres 才会因无法解析/无有效 interim 而不发布；若 `content` 为空或 null，Pi 不会生成 text block。这些样本不能区分模型本身选择空白、JSON-mode 行为或调用上下文影响，也不能证明普遍不兼容。

Tester 计划做真实请求 A/B：保持模型、prompt、工具、输入和其余参数固定，仅移除 `response_format=json_object`，记录脱敏后的有效请求参数、每个 stream delta 中的 `content`/`tool_calls`、finish reason、输出与 usage。该实验可以判断 JSON mode 是否与此样本的空文本相关；少量采样仍不足以推出总体模型能力。当前没有证据要求改 Pi parser 或更换运行框架；真实 Pi 的 interim 可用性与自然性仍须按任务验收集继续评估。

## `tool_choice=required` 与握手调整

DeepSeek Chat Completions 文档将 `required` 列为合法 `tool_choice`，定义为必须调用一个或多个工具；同一文档明确说 `required` 与指定命名工具的选择不支持 thinking mode，禁用 thinking 后才可用。Ceres 的官方 host helper 正是为该 host 附加 `thinking: {type: "disabled"}`（[DeepSeek Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)，`tool_choice` 章节；`runtime/pi/src/official-deepseek.ts:1-7`）。

Pi 1.0.3 有两层不同的 TS 合同：OpenAI 专用 `stream()` 使用 `OpenAICompletionsOptions.toolChoice`，其类型引用 OpenAI SDK 的 `ChatCompletionToolChoiceOption`，该联合包含 `'required'`（`runtime/pi/node_modules/@earendil-works/pi-ai/dist/api/openai-completions.d.ts:5-6`; `runtime/pi/node_modules/openai/resources/chat/completions/completions.d.ts:1606`）。当前 Ceres 使用的 `streamSimple()` 则接受 provider-neutral `SimpleStreamOptions.toolChoice`，限于 `'auto' | 'none'`（`runtime/pi/node_modules/@earendil-works/pi-ai/dist/types.d.ts:23,244-247`; `dist/api/openai-completions.js:518-530`）。因此，在当前 `streamSimple` 调用点，直接写 `toolChoice: 'required'` 不符合公开 TS 类型；若保留该 helper，可经它公开的 `samplingParams` 传原生 API 字段 `tool_choice: 'required'`。`SamplingParams` 是 `Record<string, unknown>`，且 provider 在构造完 `tools`/`tool_choice` 后最后合并 sampling 参数，故这个字段会发送/覆盖 wire `tool_choice`（`runtime/pi/node_modules/@earendil-works/pi-ai/dist/types.d.ts:27,128-135`; `dist/api/openai-completions.js:600-615,747-752`）。无需假定或使用未核实的 `toolChoice` alias。

最新真实对照样本（由本任务提供）显示，JSON mode 下手写 `{"content", "tool_calls"}` 正文未产生原生工具调用；regular mode 则出现原生工具调用与 65 字符普通过程文本并存，但其 141 字符普通最终文本不满足既有引用 JSON 合同。这是这两种具体配置的观察结果，不等于 DeepSeek API 普遍不兼容 `response_format` 加 tools；官方响应 schema 本身仍分别容纳 assistant content 和 tool calls，上文也记录了 JSON mode 空 content 的官方提示。

因此新的边界选择是避免让主循环在 JSON mode 下同时生成“工具调用 + interim JSON 正文”：主循环使用原生函数工具模式，过程普通文本单独审校；以不具业务写权限的 `finish_response` 函数承载原先最终引用 JSON，`tool_choice=required` 令结束响应走结构化工具参数，Node 保存已验证的最终引用后结束 Pi turn，不再要求从自然语言 final 猜引用，也不因握手另开表达 LLM。现有 JSON final 合同可继续用于受控旧路径/测试。这个设计回应的是本样本中的空正文与最终协议冲突；真实实现、引用验证与端到端行为仍须 Tester 验证，不据此宣称自然性或模型通用兼容结论。

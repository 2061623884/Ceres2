/** A bounded actual Pi Agent. Business facts and authority stay in Python. */
import { createHash } from 'node:crypto';
import { createInterface } from 'node:readline';
import { Agent, type AgentTool } from '@earendil-works/pi-agent-core';
import { streamSimple } from '@earendil-works/pi-ai/api/openai-completions';
import type { Model, Usage } from '@earendil-works/pi-ai';
import { Type } from 'typebox';
import { GENERAL_CLAIM_PROMPT, INTERIM_CLAIM_PROMPT } from './general-claim.js';
import { officialDeepSeekSampling } from './official-deepseek.js';
import { composePrompt, selectTools, type PromptModules, type TurnContext } from './prompt-modules.js';

interface Start {
  type: 'start'; run_id: string; sequence: number; message: string; categories: Array<{ id: string; name_zh: string }>;
  model: { id: string; baseUrl: string; apiKey: string };
  context: TurnContext;
  promptModules: PromptModules;
  maxToolRounds: number; timeoutMs: number;
}
const input = createInterface({ input: process.stdin });
let runId = '';
let outputSequence = 0;
let inputSequence = 0;
const send = (frame: Record<string, unknown>) => process.stdout.write(JSON.stringify({ ...frame, run_id: runId, sequence: ++outputSequence }) + '\n');

const errorKinds = new Set(['Error', 'TypeError', 'SyntaxError', 'AbortError', 'ProviderError']);
const transportCodes = new Set(['ECONNRESET', 'ECONNREFUSED', 'ENOTFOUND', 'EAI_AGAIN', 'ETIMEDOUT', 'CERT_HAS_EXPIRED', 'UNABLE_TO_VERIFY_LEAF_SIGNATURE', 'UND_ERR_CONNECT_TIMEOUT', 'UND_ERR_HEADERS_TIMEOUT', 'UND_ERR_BODY_TIMEOUT', 'UND_ERR_SOCKET']);
interface TransportDiagnostic {
  upstream_http_status: number | null;
  transport_phase: 'not_started' | 'request' | 'response' | 'fetch_error';
  transport_error_class: string | null;
  transport_error_code: string | null;
}
let transport: TransportDiagnostic = { upstream_http_status: null, transport_phase: 'not_started', transport_error_class: null, transport_error_code: null };
const beginProviderCall = () => {
  transport = { upstream_http_status: null, transport_phase: 'not_started', transport_error_class: null, transport_error_code: null };
};
const providerFetch: typeof globalThis.fetch = async (...args) => {
  // Observe the same fetch exactly once. Do not read URLs, headers or bodies,
  // change options/signals, add retries, or alter the SDK's error propagation.
  transport = { upstream_http_status: null, transport_phase: 'request', transport_error_class: null, transport_error_code: null };
  try {
    const response = await globalThis.fetch(...args);
    transport = { ...transport, upstream_http_status: response.status, transport_phase: 'response' };
    return response;
  } catch (error) {
    const kind = error instanceof Error && errorKinds.has(error.name) ? error.name : 'Error';
    const cause = error instanceof Error ? error.cause : undefined;
    const code = cause !== null && typeof cause === 'object' && 'code' in cause && typeof cause.code === 'string' && transportCodes.has(cause.code) ? cause.code : null;
    transport = { upstream_http_status: null, transport_phase: 'fetch_error', transport_error_class: kind, transport_error_code: code };
    throw error;
  }
};

function diagnostic(error: unknown) {
  const source = error instanceof Error ? error.message : String(error);
  const kind = error instanceof Error && errorKinds.has(error.name) ? error.name : 'Error';
  // HTTP status is evidence from Response, never a number found in provider prose.
  const code = transport.upstream_http_status !== null && transport.upstream_http_status >= 400
    ? `HTTP_${transport.upstream_http_status}` : transport.transport_error_code ?? kind;
  return { kind, code, fingerprint: createHash('sha256').update(source).digest('hex'), ...transport };
}
const sendError = (code: string, cause: unknown) => send({ type: 'error', code, diagnostic: diagnostic(cause) });

const waiting = new Map<string, (value: unknown) => void>();
let started = false;
input.on('line', (line) => {
  const frame = JSON.parse(line);
  if (frame.type === 'start' && !started) {
    if (typeof frame.run_id !== 'string' || !frame.run_id || frame.sequence !== 1) {
      sendError('PI_PROTOCOL_INVALID', new Error('Invalid start envelope'));
      input.close();
      return;
    }
    runId = frame.run_id;
    inputSequence = 1;
    started = true;
    run(frame).catch(error => sendError('PI_RUNTIME_ERROR', error)).finally(() => input.close());
  } else if (frame.type === 'tool_result' && started && frame.run_id === runId && frame.sequence === inputSequence + 1 && waiting.has(frame.id)) {
    inputSequence = frame.sequence;
    waiting.get(frame.id)!(frame.result);
    waiting.delete(frame.id);
  } else {
    sendError('PI_PROTOCOL_INVALID', new Error('Invalid tool envelope'));
    input.close();
  }
});

async function run(start: Start) {
  let toolRounds = 0;
  let status = 'completed';
  let errorCode: string | undefined;
  let validator: Agent | undefined;
  let shoppingContext = false;
  let guideRegistered = false;
  let interimChecks: Promise<void> = Promise.resolve();
  let interimNumber = 0;
  let finalAnswer: string | undefined;
  const providerStartedAt = new Map<string, number>();
  const recordUsage = (kind: string, usage: Usage) => {
    const {input,output,cacheRead,cacheWrite,totalTokens} = usage;
    const startedAt = providerStartedAt.get(kind);
    send({type:'event',event:{type:'model_usage',kind,model:start.model.id,
      provider_host:new URL(start.model.baseUrl).hostname,
      duration_ms:startedAt===undefined?null:performance.now()-startedAt,
      usage:totalTokens>0?{input,output,cacheRead,cacheWrite,totalTokens}:null,cost:null}});
  };
  const model: Model<'openai-completions'> = {
    id: start.model.id, name: start.model.id, api: 'openai-completions', provider: 'ceres',
    baseUrl: start.model.baseUrl, reasoning: false, input: ['text'],
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
    contextWindow: 32768, maxTokens: 1536,
  };
  const remote = async (name: string, id: string, args: unknown, signal?: AbortSignal) => {
    await interimChecks;
    const result = await new Promise<unknown>((resolve, reject) => {
      const abort = () => { waiting.delete(id); reject(new Error('aborted')); };
      if (signal?.aborted) return abort();
      signal?.addEventListener('abort', abort, { once: true });
      waiting.set(id, value => { signal?.removeEventListener('abort', abort); resolve(value); });
      send({ type: 'tool_call', id, name, arguments: args, round: toolRounds + 1 });
    });
    if(name==='guide_request') guideRegistered=true;
    if (name === 'guide_request' && ['new_goal', 'continue', 'amend'].includes((result as {kind:string}).kind)) shoppingContext = true;
    return { content: [{ type: 'text' as const, text: JSON.stringify(result) }], details: result };
  };
  const tools: AgentTool[] = [
    { name:'finish_response', label:'完成当前回复',
      description:'End this run with the final structured reference object. Call alone after all necessary tool results. This is only a response contract: Python validates every reference and renders facts; this tool cannot add to cart, submit an order or application, or authorize business writes. Do not put content/tool_calls in its arguments.',
      parameters:Type.Object({
        status:Type.Union([Type.Literal('completed'),Type.Literal('waiting')]),
        answer_kind:Type.Optional(Type.Union(['products','comparison','policy_result','purchase_plan','exploration','question_selection','history_result','memory_result','dish_candidates','recipe_facts','general_explanation','status'].map(value=>Type.Literal(value)))),
        product_refs:Type.Optional(Type.Array(Type.String())),
        dish_refs:Type.Optional(Type.Array(Type.String())),
        ingredient_ids:Type.Optional(Type.Array(Type.String())),
        policy_ref:Type.Optional(Type.String()), proposal_ref:Type.Optional(Type.String()),
        exploration_ref:Type.Optional(Type.String()), selection_ref:Type.Optional(Type.String()),
        history_ref:Type.Optional(Type.String()), memory_ref:Type.Optional(Type.String()),
        general_ref:Type.Optional(Type.String()),
        clarification_slot:Type.Optional(Type.Union(['target','packaging','brand','budget'].map(value=>Type.Literal(value)))),
      },{additionalProperties:false}),
      execute:async(_id,args)=>{
        if(!guideRegistered) throw new Error('guide_request must precede finish_response');
        finalAnswer=JSON.stringify(args);
        return {content:[{type:'text',text:'Response references supplied for host validation.'}],details:{final_response:true}};
      },
    },
    { name: 'guide_request', label: '登记当前请求', description: 'Classify this user message once, before product tools. question preserves shopping work; progress reads status; continue keeps goal; new_goal explicitly replaces goal; amend records explicit new conditions; stop only stops current processing; abandon ends the shopping task without changing cart. This never authorizes cart or order writes.', parameters: Type.Object({ kind: Type.Union(['question','progress','continue','new_goal','amend','stop','abandon'].map(value => Type.Literal(value))), goal: Type.Optional(Type.String({minLength:1,maxLength:8000})), conditions: Type.Optional(Type.Record(Type.String(), Type.Unknown())) }, {additionalProperties:false}), execute: (id, args, signal) => remote('guide_request', id, args, signal) },
    { name: 'validate_general_text', label: '核对普通解释', description: 'For unrelated general knowledge only, submit proposed short messages once. Uses the same configured model to check merchant/execution claims within this run deadline. Return only the resulting general_ref in your final answer. No merchant facts or execution receipts are authorized.', parameters: Type.Object({messages:Type.Array(Type.String({minLength:1}),{minItems:1})},{additionalProperties:false}), execute: async (id, args, signal) => {
      const reserved = await remote('validate_general_text', id, args, signal);
      const ref = (reserved.details as {general_ref:string}).general_ref;
      if (signal?.aborted) throw new Error('aborted');
      validator = new Agent({
        initialState: {model, thinkingLevel:'off', tools:[], systemPrompt:GENERAL_CLAIM_PROMPT},
        streamFn: (_model, context, options) => {
          providerStartedAt.set('general_audit',performance.now());
          beginProviderCall();
          const samplingParams = officialDeepSeekSampling(start.model.baseUrl, options?.samplingParams);
          return streamSimple(model, context, {
            ...options, apiKey: start.model.apiKey, maxTokens: 256, fetch: providerFetch,
            ...(samplingParams ? { samplingParams } : {}),
          });
        },
      });
      validator.subscribe(event=>{
        if(event.type==='message_end' && event.message.role==='assistant') recordUsage('general_audit',event.message.usage);
      });
      const abort = () => validator?.abort();
      signal?.addEventListener('abort',abort,{once:true});
      send({type:'event',event:{type:'general_validation_start',model_calls:1}});
      let approved=false;
      let reason='uncertain';
      try {
        await validator.prompt(JSON.stringify((args as {messages:string[]}).messages));
        const last=[...validator.state.messages].reverse().find(message=>message.role==='assistant');
        if(last?.role==='assistant' && last.stopReason!=='error' && last.stopReason!=='aborted') {
          const raw=last.content.filter(block=>block.type==='text').map(block=>block.text).join('');
          const verdict=JSON.parse(raw);
          if(verdict && Object.keys(verdict).length===2 && typeof verdict.merchant_claims==='boolean' && typeof verdict.execution_claims==='boolean') {
            approved=!verdict.merchant_claims && !verdict.execution_claims;
            reason=approved?'approved':'claims';
          }
        }
      } catch {
        // The caller receives an uncertain rejection, never raw provider text.
      } finally { signal?.removeEventListener('abort',abort); validator=undefined; }
      if (status !== 'completed' || signal?.aborted) return {content:[{type:'text' as const,text:'Validation interrupted'}],details:{interrupted:true}};
      send({type:'general_validation',general_ref:ref,approved,reason});
      send({type:'event',event:{type:'general_validation_end',approved}});
      if(!approved) { errorCode=reason==='uncertain'?'PI_GENERAL_VALIDATION_UNCERTAIN':'PI_UNGROUNDED_BUSINESS_TEXT';agent.abort(); }
      const result={general_ref:ref,approved};
      return {content:[{type:'text' as const,text:JSON.stringify(result)}],details:result};
    } },
    { name: 'search_products', label: '查询商品', description: 'Search the current store catalog by query and/or a category_id from the supplied category list. Read-only; returns scoped refs.', parameters: Type.Object({ query: Type.Optional(Type.String({ minLength: 1, maxLength: 100 })), category_id: Type.Optional(Type.String({ minLength: 1, maxLength: 32 })) }, { additionalProperties: false, minProperties: 1 }), execute: (id, args, signal) => remote('search_products', id, args, signal) },
    { name: 'search_after_sales_policy', label: '查询服务政策', description: 'Hybrid retrieval of versioned general service policies without selecting an order. Finish with policy_result and this policy_ref. Does not determine order eligibility or submit an application.', parameters:Type.Object({query:Type.String({minLength:1}),category:Type.Optional(Type.Union(['price','stock','delivery','order','refund','fulfillment','quality','return','safety','human'].map(value=>Type.Literal(value))))},{additionalProperties:false}), execute:(id,args,signal)=>remote('search_after_sales_policy',id,args,signal) },
    { name: 'history_command', label: '查看或选定历史采购', description: 'List historical source plans before selecting. Ambiguous last time must list, never guess. select requires a source_task_id explicitly named in current user message or unique named historical goal. Interpret ordinary prose effective shopping memories from list into typed memory_defaults (people, budget_fen, exclusions), with all effective non-reference shopping memory ID/revision refs. Current task explicit conditions override defaults. Never infer price, stock, approval or cart. If interpretation is uncertain, clarify instead. Finish history_result with latest history_ref.', parameters:Type.Object({action:Type.Union([Type.Literal('list'),Type.Literal('select')]),source_task_id:Type.Optional(Type.String()),memory_defaults:Type.Optional(Type.Object({people:Type.Optional(Type.Integer({minimum:1})),budget_fen:Type.Optional(Type.Integer({minimum:0})),exclusions:Type.Optional(Type.Array(Type.String()))},{additionalProperties:false})),memory_refs:Type.Optional(Type.Array(Type.Object({memory_id:Type.String(),revision:Type.Integer({minimum:1})},{additionalProperties:false})))},{additionalProperties:false}), execute:(id,args,signal)=>remote('history_command',id,args,signal) },
    { name: 'memory_command', label: '处理明确记忆指令', description: 'Only current explicit user save/list/update/delete instructions. source_quote must quote that instruction exactly. Read-only list may resolve real references, followed by at most one save/update/delete. Ambiguous matches require clarification. Return only the latest memory_ref. shopping domain is Keke only, aftersales Momo only, communication relevant to both. Recall never grants business authority. Return memory_result with host memory_ref. list is explicit full owned memory management; update/delete require real memory_id and revision from prior results.', parameters: Type.Object({action:Type.Union(['save','list','update','delete'].map(v=>Type.Literal(v))),category:Type.Optional(Type.Union(['user','feedback','project','reference'].map(v=>Type.Literal(v)))),domain:Type.Optional(Type.Union(['shopping','aftersales','communication'].map(v=>Type.Literal(v)))),key:Type.Optional(Type.String({minLength:1,maxLength:100})),content:Type.Optional(Type.String({minLength:1,maxLength:2000})),source_quote:Type.Optional(Type.String({minLength:1,maxLength:4000})),memory_id:Type.Optional(Type.String({minLength:1,maxLength:80})),expected_revision:Type.Optional(Type.Integer({minimum:1})),expires_at:Type.Optional(Type.Union([Type.String(),Type.Null()])),reference_url:Type.Optional(Type.Union([Type.String({minLength:1,maxLength:2000}),Type.Null()]))},{additionalProperties:false}), execute:(id,args,signal)=>remote('memory_command',id,args,signal) },
    { name: 'select_question_products', label: '选定已展示商品与数量', description: 'Answer the current products/quantity question using its exact question_id and option_ids. Only explicitly selected products; omit quantity if unknown, so the host asks just that missing information. Never adds to cart. Finish question_selection with returned selection_ref.', parameters:Type.Object({question_id:Type.String({minLength:1}),selections:Type.Array(Type.Object({option_id:Type.String({minLength:1}),quantity:Type.Optional(Type.Integer({minimum:1}))},{additionalProperties:false}),{minItems:1})},{additionalProperties:false}), execute:(id,args,signal)=>remote('select_question_products',id,args,signal) },
    { name: 'explore_products', label: '查看真实选购方向', description: 'Explore actual constrained supply. Generic cross-type requests get one type question; specific product_type goes straight to products. Finish with answer_kind exploration and the returned exploration_ref. Never selects or adds to cart.', parameters:Type.Object({category_id:Type.String({minLength:1}),product_type:Type.Optional(Type.String()),query:Type.Optional(Type.String()),answer_question_id:Type.Optional(Type.String())},{additionalProperties:false}), execute:(id,args,signal)=>remote('explore_products',id,args,signal) },
    { name: 'compare_products', label: '比较商品', description: 'For a category comparison, call this once. Use only the product refs returned here; do not follow with search_products or another compare_products call. Query alone never selects or purchases.', parameters:Type.Object({query:Type.Optional(Type.String()), category_id:Type.Optional(Type.String()), brand:Type.Optional(Type.String()), packaging:Type.Optional(Type.String()), pack_count_mode:Type.Optional(Type.Union([Type.Literal('single'),Type.Literal('multi')]))},{additionalProperties:false}), execute:(id,args,signal)=>remote('compare_products',id,args,signal) },
    { name: 'search_dishes', label: '查询菜谱', description: 'Look up dish suggestions or a user-selected recipe and actual ingredient SKU candidates. Pantry has unknown amounts, not presumed at home.', parameters:Type.Object({query:Type.String({minLength:1})},{additionalProperties:false}), execute:(id,args,signal)=>remote('search_dishes',id,args,signal) },
    { name: 'search_recipe_relations', label: '检索菜谱关系', description: 'Use real GraphRAG Local retrieval for relationship questions, such as recipes sharing ingredients or dishes using ingredients explicitly mentioned by the user. Returns canonical recipe refs and sourced graph context. Amounts at home, substitutions, nutrition and allergy safety remain unknown unless explicit facts exist. Finish with dish_candidates refs or prepare only a user-selected dish; graph does not authorize purchase.', parameters:Type.Object({query:Type.String({minLength:1})},{additionalProperties:false}), execute:(id,args,signal)=>remote('search_recipe_relations',id,args,signal) },
    { name: 'propose_dish', label: '准备菜品清单', description: 'Prepare the selected recipe. operation append is only for an explicitly selected additional dish. update preserves all other groups; group_id must identify the existing target when ambiguous. Omit people if user did not specify it; host preserves existing explicit people and SKU selections. selections maps ingredient IDs to actual queried candidate SKU IDs explicitly selected by user. Never confirms cart.', parameters:Type.Object({dish_ref:Type.String({minLength:1}), operation:Type.Optional(Type.Union([Type.Literal('append'),Type.Literal('update')])), group_id:Type.Optional(Type.String({minLength:1})), people:Type.Optional(Type.Integer({minimum:1})), selections:Type.Optional(Type.Record(Type.String(),Type.String()))},{additionalProperties:false}), execute:(id,args,signal)=>remote('propose_dish',id,args,signal) },
    { name: 'propose_purchase', label: '准备采购清单', description: 'Only after the user explicitly selects this concrete product and positive sale-package count. Prepare a plan using a current search ref; never adds to cart. Do not propose merely recommended or related products. Return proposal_ref as purchase_plan final answer.', parameters: Type.Object({ref:Type.String({minLength:1}),quantity:Type.Integer({minimum:1})},{additionalProperties:false}), execute:(id,args,signal)=>remote('propose_purchase',id,args,signal) },
    { name: 'product_details', label: '查看规格和供给', description: 'Read full details for a product ref returned by this run. Read-only.', parameters: Type.Object({ ref: Type.String({ minLength: 1 }) }, { additionalProperties: false }), execute: (id, args, signal) => remote('product_details', id, args, signal) },
  ];
  const agent = new Agent({
    initialState: {
      model, thinkingLevel: 'off', tools,
      systemPrompt: composePrompt(start.promptModules, start.context, start.context.capability),
    },
    streamFn: (_model, context, options) => {
      providerStartedAt.set('main',performance.now());
      beginProviderCall();
      const toolSampling = {...options?.samplingParams, tool_choice:'auto'};
      const samplingParams = officialDeepSeekSampling(start.model.baseUrl,toolSampling) ?? toolSampling;
      return streamSimple(model, context, {
        ...options, apiKey: start.model.apiKey, maxTokens: 1536, fetch: providerFetch,
        ...(samplingParams ? { samplingParams } : {}),
      });
    },
    prepareRequest: ({context}) => {
      const capability = shoppingContext ? 'exploration' : start.context.capability;
      const selected = selectTools(tools, capability);
      const prompt = composePrompt(start.promptModules, start.context, capability);
      return {context: {tools:selected, messages:context.messages.map((message,index) => index === 0 && message.role === 'system' ? {...message,content:prompt,toolsAdded:selected} : message)}};
    },
    toolExecution: 'sequential',
    finishTurn: ({ toolResults }) => {
      if (finalAnswer !== undefined) return {action:'end'};
      if (toolResults.length > 0) toolRounds += 1;
      if (toolRounds >= Math.min(5, start.maxToolRounds)) {
        status = 'tool_budget';
        return { action: 'end' };
      }
    },
  });
  const timer = setTimeout(() => { status = 'deadline'; agent.abort(); validator?.abort(); }, Math.min(30000, start.timeoutMs));
  agent.subscribe(event => {
    // These are actual SDK lifecycle events, projected without hidden thinking,
    // provider credentials, or unvalidated assistant prose.
    if (event.type !== 'message_update') {
      send({ type: 'event', event: {
        type: event.type,
        ...('toolName' in event ? { toolName: event.toolName, toolCallId: event.toolCallId } : {}),
        ...('isError' in event ? { isError: event.isError } : {}),
      } });
    }
    if (event.type === 'message_end' && event.message.role === 'assistant') {
      recordUsage('main',event.message.usage);
      const calls = event.message.content.filter(block=>block.type==='toolCall');
      if(calls.some(block=>block.name==='finish_response') && calls.length!==1) {
        errorCode='PI_TOOL_INVALID';agent.abort();
      }
      for (const block of event.message.content) {
        if (block.type === 'toolCall' && !tools.some(tool => tool.name === block.name)) {
          errorCode = 'PI_TOOL_FORBIDDEN'; agent.abort();
        }
      }
      // Native tool iterations can include ordinary public prose. Completion
      // references have their own tool contract and never become an interim.
      if (!errorCode && event.message.stopReason !== 'error' && event.message.stopReason !== 'aborted' && calls.some(block=>block.name!=='finish_response')) {
        const raw = event.message.content.filter(block=>block.type==='text').map(block=>block.text).join('');
        let text: string | undefined;
        const prose = raw.trim();
        if(prose.startsWith('{') || prose.startsWith('[')) {
          // Existing controlled callers use the explicit interim object.
          try {
            const content = JSON.parse(prose);
            if (Object.keys(content).length === 1 && typeof content.interim_message === 'string' && content.interim_message.trim()) text = content.interim_message.trim();
          } catch { /* Invalid structured text is withheld, not repaired. */ }
        } else if(prose) text=prose;
        send({type:'event',event:{type:'interim_candidate',
          status:text?'ready':raw.trim()?'invalid_format':'absent',
          text_characters:raw.length,
          tool_call_count:event.message.content.filter(block=>block.type==='toolCall').length}});
        if (text) {
          const candidate = text;
          const messageId = `${runId}:interim:${++interimNumber}`;
          interimChecks = interimChecks.then(async()=>{
            if (status !== 'completed') return;
            validator = new Agent({
              initialState:{model,thinkingLevel:'off',tools:[],systemPrompt:INTERIM_CLAIM_PROMPT},
              streamFn:(_model,context,options)=>{
                providerStartedAt.set('interim_audit',performance.now());
                beginProviderCall();
                const samplingParams = officialDeepSeekSampling(start.model.baseUrl,options?.samplingParams);
                return streamSimple(model,context,{...options,apiKey:start.model.apiKey,maxTokens:256,fetch:providerFetch,...(samplingParams?{samplingParams}:{})});
              },
            });
            validator.subscribe(check=>{
              if(check.type==='message_end' && check.message.role==='assistant') recordUsage('interim_audit',check.message.usage);
            });
            let approved = false;
            try {
              await validator.prompt(JSON.stringify([candidate]));
              const last = [...validator.state.messages].reverse().find(message=>message.role==='assistant');
              if(last?.role==='assistant' && last.stopReason!=='error' && last.stopReason!=='aborted') {
                const verdict=JSON.parse(last.content.filter(block=>block.type==='text').map(block=>block.text).join(''));
                approved=Object.keys(verdict).length===2 && verdict.merchant_claims===false && verdict.execution_claims===false;
              }
            } catch { /* An uncertain optional message is withheld. */ }
            finally { validator=undefined; }
            send({type:'event',event:{type:'interim_audit',message_id:messageId,approved}});
            if(approved && status==='completed') send({type:'interim_message',message_id:messageId,text:candidate,approved:true});
          });
        }
      }
    }
    if (event.type === 'tool_execution_end' && event.isError) {
      errorCode ??= 'PI_TOOL_INVALID'; agent.abort();
    }
  });
  try {
    await agent.prompt(start.message);
    await interimChecks;
    if (errorCode) return sendError(errorCode, new Error(errorCode));
    if (status !== 'completed') return send({ type: 'result', status });
    if (finalAnswer !== undefined) return send({type:'result',status,answer:finalAnswer});
    const last = [...agent.state.messages].reverse().find(message => message.role === 'assistant');
    if (!last || last.role !== 'assistant' || last.stopReason === 'error' || last.stopReason === 'aborted') {
      const cause = new Error(last?.role === 'assistant' ? last.errorMessage : agent.state.errorMessage);
      cause.name = 'ProviderError';
      return sendError('PI_PROVIDER_ERROR', cause);
    }
    const answer = last.content.filter(block => block.type === 'text').map(block => block.text).join('');
    send({ type: 'result', status, answer });
  } finally {
    clearTimeout(timer);
  }
}

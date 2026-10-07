/** Expression-only Pi process. No tools, business API, or semantic routing. */
import { createHash } from 'node:crypto';
import { createInterface } from 'node:readline';
import { Agent } from '@earendil-works/pi-agent-core';
import { streamSimple } from '@earendil-works/pi-ai/api/openai-completions';
import type { Model } from '@earendil-works/pi-ai';
import { GENERAL_CLAIM_PROMPT } from './general-claim.js';
import { officialDeepSeekSampling } from './official-deepseek.js';

class ExpressionError extends Error {
  constructor(readonly code:string, cause?:unknown) { super(code, {cause}); }
}

type Start = { run_id:string; model:{id:string;baseUrl:string;apiKey:string}; timeoutMs:number; prompt:string; facts:Record<string,string> };
type UsageFields = {
  input_tokens:number|null; output_tokens:number|null; cache_read_tokens:number|null; cache_write_tokens:number|null;
  usage_source:'provider'|'unreported'; input_token_scope:'prompt_total';
};
function observeUsage() {
  const values:UsageFields={input_tokens:null,output_tokens:null,cache_read_tokens:null,cache_write_tokens:null,usage_source:'unreported',input_token_scope:'prompt_total'};
  return {values, onEvent:(data:unknown)=>{
    const chunk=data as {usage?:Record<string,unknown>;choices?:Array<{usage?:Record<string,unknown>}>}|null;
    const raw=chunk?.usage??chunk?.choices?.[0]?.usage;
    if(!raw||typeof raw!=='object'||Array.isArray(raw)) return;
    values.usage_source='provider';
    const details=raw.prompt_tokens_details as Record<string,unknown>|undefined;
    const reported={input_tokens:raw.prompt_tokens,output_tokens:raw.completion_tokens,
      cache_read_tokens:details?.cached_tokens??raw.prompt_cache_hit_tokens??raw.cached_tokens,
      cache_write_tokens:details?.cache_write_tokens};
    for(const key of ['input_tokens','output_tokens','cache_read_tokens','cache_write_tokens'] as const) {
      const value=reported[key];
      // Preserve explicitly reported zero and later cumulative values. SDK
      // defaults/estimates cannot turn an omitted provider field into zero.
      if(typeof value==='number'&&Number.isInteger(value)&&value>=0) values[key]=value;
    }
  }};
}
const input = createInterface({input:process.stdin});
input.once('line', line => { void run(JSON.parse(line) as Start).finally(() => input.close()); });

async function run(start:Start) {
  let sequence=0;
  const send=(frame:Record<string,unknown>)=>process.stdout.write(JSON.stringify({...frame,run_id:start.run_id,sequence:++sequence})+'\n');
  const model:Model<'openai-completions'>={id:start.model.id,name:start.model.id,api:'openai-completions',provider:'ceres',baseUrl:start.model.baseUrl,reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:32768,maxTokens:512};
  let validator:Agent|undefined;
  let buffer='';
  let units=0;
  let failed=false;
  let failure:{code:string;cause:string;fingerprint:string}|undefined;
  let timedOut=false;
  let validations=Promise.resolve();
  const seen=new Set<string>();
  const generationUsage=observeUsage();
  const agent=new Agent({initialState:{model,thinkingLevel:'off',tools:[],systemPrompt:start.prompt},streamFn:(_model,context,options)=>{
    const samplingParams=officialDeepSeekSampling(start.model.baseUrl,options?.samplingParams);
    return streamSimple(model,context,{...options,apiKey:start.model.apiKey,maxTokens:512,onProviderStreamEvent:generationUsage.onEvent,...(samplingParams?{samplingParams}:{})});
  }});
  const stop=(error:unknown, fallback='generation_provider')=>{
    if(!failure) {
      const cause=error instanceof ExpressionError ? error.cause??error : error;
      const kinds=new Set(['Error','SyntaxError','TypeError','AbortError']);
      failure={code:error instanceof ExpressionError ? error.code : fallback,
        cause:cause instanceof Error&&kinds.has(cause.name)?cause.name:'Error',
        fingerprint:createHash('sha256').update(cause instanceof Error?cause.message:String(cause)).digest('hex')};
    }
    failed=true;agent.abort();validator?.abort();
  };
  const timer=setTimeout(()=>{timedOut=true;stop(new ExpressionError('deadline'));},Math.min(30000,start.timeoutMs));
  const usage=(who:string,fields:UsageFields)=>send({type:'metric',phase:who+'_usage',...fields,at_ms:Date.now()});
  const validate=async(unit:{text:string;fact_ref:string})=>{
    if(failed) return;
    const validationUsage=observeUsage();
    validator=new Agent({initialState:{model,thinkingLevel:'off',tools:[],systemPrompt:GENERAL_CLAIM_PROMPT},streamFn:(_model,context,options)=>{
      const samplingParams=officialDeepSeekSampling(start.model.baseUrl,options?.samplingParams);
      return streamSimple(model,context,{...options,apiKey:start.model.apiKey,maxTokens:256,onProviderStreamEvent:validationUsage.onEvent,...(samplingParams?{samplingParams}:{})});
    }});
    validator.subscribe(event=>{
      if(event.type==='message_end'&&event.message.role==='assistant'&&event.message.content.some(block=>block.type==='toolCall')) stop(new ExpressionError('validation_tool_call'));
    });
    send({type:'metric',phase:'validation_start',model_calls:1,at_ms:Date.now()});
    await validator.prompt(JSON.stringify([unit.text]));
    const last=[...validator.state.messages].reverse().find(message=>message.role==='assistant');
    if(failed||!last||last.role!=='assistant'||last.stopReason==='error'||last.stopReason==='aborted') throw new ExpressionError(last?.role==='assistant'&&last.stopReason==='aborted'?'aborted':'validation_provider', new Error(last?.role==='assistant'?last.errorMessage??'validation interrupted':'validation missing'));
    usage('validation',validationUsage.values);
    let verdict;
    try { verdict=JSON.parse(last.content.filter(block=>block.type==='text').map(block=>block.text).join('')); }
    catch(error) { throw new ExpressionError('validation_parse',error); }
    if(!verdict||Object.keys(verdict).length!==2||verdict.merchant_claims!==false||verdict.execution_claims!==false) throw new ExpressionError('validation_rejected');
    validator=undefined;
    send({type:'unit',...unit});
  };
  const acceptLine=(line:string)=>{
    let unit;
    try { unit=JSON.parse(line); }
    catch(error) { throw new ExpressionError('expression_parse',error); }
    if(!unit||Object.keys(unit).sort().join(',')!=='fact_ref,text'||typeof unit.text!=='string'||!unit.text.trim()||unit.text.length>100||typeof unit.fact_ref!=='string'||!Object.hasOwn(start.facts,unit.fact_ref)||seen.has(unit.fact_ref)||units>=2) throw new ExpressionError('invalid_unit');
    units++;seen.add(unit.fact_ref);
    validations=validations.then(()=>validate(unit)).catch(error=>stop(error,'validation_provider'));
  };
  agent.subscribe(event=>{
    if(event.type==='message_update'&&event.assistantMessageEvent.type==='text_delta'&&!failed){
      try{
        buffer+=event.assistantMessageEvent.delta;
        if(buffer.length>4096) throw new ExpressionError('expression_limit');
        let newline:number;
        while((newline=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,newline).trim();buffer=buffer.slice(newline+1);if(line)acceptLine(line);}
      }catch(error){stop(error);}
    }
    if(event.type==='message_end'&&event.message.role==='assistant'){
      usage('generation',generationUsage.values);
      if(event.message.content.some(block=>block.type==='toolCall')) stop(new ExpressionError('generation_tool_call'));
    }
  });
  try{
    send({type:'metric',phase:'generation_start',model_calls:1,at_ms:Date.now()});
    await agent.prompt(JSON.stringify({facts:start.facts}));
    send({type:'metric',phase:'generation_end',at_ms:Date.now()});
    const last=[...agent.state.messages].reverse().find(message=>message.role==='assistant');
    if(!last||last.role!=='assistant'||last.stopReason==='error'||last.stopReason==='aborted') stop(new ExpressionError(last?.role==='assistant'&&last.stopReason==='aborted'?'aborted':'generation_provider',new Error(last?.role==='assistant'?last.errorMessage??'generation interrupted':'generation missing')));
    // A complete last object without newline remains a bounded unit; an
    // incomplete/malformed object is rejected, never surfaced as raw prose.
    if(buffer.trim()&&!failed) acceptLine(buffer.trim());
    await validations;
    if(units===0) stop(new ExpressionError('empty_output'));
  }catch(error){stop(error);await validations;}
  finally{clearTimeout(timer);send({type:'result',status:timedOut?'deadline':failed?'failed':'completed',...(failure?{diagnostic:failure}:{})});}
}

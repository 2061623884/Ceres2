/** Read explicit usage alongside SSE, forwarding each original byte immediately. */
export type ObservedUsage = {input:number|null;output:number|null;cacheRead:number|null;cacheWrite:number|null;totalTokens:number|null};

export function observeProviderUsage(response:Response, record:(usage:ObservedUsage)=>void):Response {
  const decoder=new TextDecoder();
  let pending='';
  const body=response.body!.pipeThrough(new TransformStream<Uint8Array,Uint8Array>({
    transform(chunk,controller) {
      pending+=decoder.decode(chunk,{stream:true});
      const lines=pending.split('\n'); pending=lines.pop()!;
      for(const line of lines) {
        if(!line.startsWith('data:')) continue;
        const data=line.slice(5).trim();
        if(data==='[DONE]') continue;
        let value;
        try { value=JSON.parse(data); } catch { continue; } // SDK handles malformed data.
        const usage=value?.usage;
        if(usage && typeof usage==='object') {
          const number=(value:unknown)=>typeof value==='number' && Number.isFinite(value)?value:null;
          const observed={input:number(usage.prompt_tokens),output:number(usage.completion_tokens),
            cacheRead:number(usage.prompt_tokens_details?.cached_tokens ?? usage.prompt_cache_hit_tokens),
            cacheWrite:number(usage.cache_creation_input_tokens),totalTokens:number(usage.total_tokens)};
          if(Object.values(observed).some(value=>value!==null)) record(observed);
        }
      }
      controller.enqueue(chunk);
    },
  }));
  return new Response(body,{status:response.status,statusText:response.statusText,headers:response.headers});
}

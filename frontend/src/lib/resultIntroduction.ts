import { ensureIdentity, reconnectGuideRun, stopGuideTurn } from './saleGuide'

export type IntroductionSource = {source_kind:'question_answer'|'purchase_confirmation'|'turn'; source_id:string}
export type IntroductionRun = {run_id:string;request_id:string;session_id:string}
export type IntroductionCallbacks = {
  signal: AbortSignal
  onDelta: (text:string,messageId:string,replace:boolean)=>void
}

/** Called after the authoritative result has rendered. Never repeats an action. */
export async function runResultIntroduction(sessionId:string,source:IntroductionSource,callbacks:IntroductionCallbacks) {
  return start(`/api/v1/guide/sessions/${encodeURIComponent(sessionId)}/result-introductions`,source,callbacks)
}
export async function runReceiptIntroduction(caseId:string,receiptId:string,callbacks:IntroductionCallbacks) {
  return start(`/api/v1/mercury/sessions/${encodeURIComponent(caseId)}/result-introductions`,{source_id:receiptId},callbacks)
}
async function start(url:string,body:object,callbacks:IntroductionCallbacks) {
  await ensureIdentity()
  if(callbacks.signal.aborted) return
  // Preserve admission response even if the UI leaves meanwhile, so the exact
  // acknowledged expression can be stopped rather than issuing a new request.
  const response=await fetch(url,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  if(!response.ok) throw new Error('介绍未完成，已有结果仍保留。')
  const run=await response.json() as IntroductionRun
  const cancel=()=>{void stopGuideTurn(run.session_id,run.request_id).catch(()=>{})}
  if(callbacks.signal.aborted){cancel();return}
  callbacks.signal.addEventListener('abort',cancel,{once:true})
  let lastSequence = 0
  try {
    return await reconnectGuideRun(run.session_id,run.run_id,{
      signal:callbacks.signal,
      onAnswerDelta:event=>{
        if(callbacks.signal.aborted) return
        if(Number.isInteger(event.sequence)) {
          if(event.sequence<=lastSequence) return
          lastSequence=event.sequence
        }
        callbacks.onDelta(String(event.payload?.delta??''),String(event.payload?.message_id??''),event.payload?.replace===true)
      },
    })
  } finally {callbacks.signal.removeEventListener('abort',cancel)}
}

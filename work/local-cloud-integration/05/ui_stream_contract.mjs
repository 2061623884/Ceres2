/** Public SSE client: synthetic wire events, no server/provider/network. Tester executes. */
import assert from 'node:assert/strict'
import {createRequire} from 'node:module'
import path from 'node:path'
const require=createRequire(path.join(process.cwd(),'work/local-cloud-integration/05/compiled/package.json'))
const {sendTurnStream,reconnectGuideRun}=require('./lib/saleGuide.js')
const event=(sequence,type,payload)=>({protocol_version:1,run_id:'run-public',session_id:'session-public',sequence,type,recorded_at_ms:null,elapsed_ms:null,payload})
const interim=event(2,'message.interim',{message_id:'interim-public',content:'正在核对模拟商品。'})
const delta=event(3,'answer.delta',{message_id:'final-public',delta:'商品事实',replace:true})
const tail=event(4,'answer.delta',{message_id:'final-public',delta:'与政策',replace:false})
const terminal=event(5,'turn.completed',{message:'商品事实与政策',messages:[{message_id:'final-public',content:'商品事实与政策'}],runtime_status:'completed'})
const calls=[]
globalThis.fetch=async(url,init)=>{calls.push({url,init});return new Response([interim,interim,delta,tail,tail,terminal].map(value=>'data: '+JSON.stringify(value)+'\n\n').join(''),{headers:{'Content-Type':'text/event-stream'}})}
let interimCount=0, assembled=''
const callbacks={onInterimMessage:e=>{interimCount++;assert.equal(e.payload.message_id,'interim-public')},onAnswerDelta:e=>{assembled=e.payload.replace?e.payload.delta:assembled+e.payload.delta}}
await sendTurnStream('session-public','混合问题',null,0,'request-public',0,undefined,callbacks)
assert.equal(interimCount,1,'Approved interim is delivered once despite duplicate sequence')
assert.equal(assembled,'商品事实与政策','Repeated delta sequence must not duplicate visible text')
await reconnectGuideRun('session-public','run-public',{},4)
assert.match(calls.at(-1).url,/after_sequence=4$/)
console.log(JSON.stringify({ok:true,level:'public-client-controlled-wire',checks:['interim dispatch','duplicate sequence fence','terminal result','reconnect cursor']}))

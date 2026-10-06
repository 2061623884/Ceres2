/** Controlled actual AfterSalesPanel DOM; not real-browser or real-model proof. */
import assert from 'node:assert/strict'
import path from 'node:path'
import {createRequire} from 'node:module'
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'))
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true})
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,process.argv[2]??'work/next-experience/06/compiled/package.json'))
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),{AfterSalesPanel}=compiled('./AfterSalesPanel.js')
const preview={proposal_id:'p',revision:1,order_id:'o',kind:'refund',amount_fen:600,reason:'不需要了',policy_id:'P-REF-01',policy:'模拟退款',items:[{item_id:'sku',name:'薯片',quantity:1,amount_fen:600}]}
const receipt={...preview,receipt_id:'r',application_id:'a',status:'requested',message:'模拟申请已提交，尚未审批或退款到账'}
let state={proposal:preview,receipts:[]},writes=0,introductions=0,stops=0,stream
const container=document.getElementById('root'),root=createRoot(container)
const response=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}})
globalThis.fetch=async(input,options={})=>{
 const url=String(input)
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store'})
 if(url.endsWith('/aftersales'))return response(state)
 if(url.includes('/orders/'))return response({items:[{sku_id:'sku',name:'薯片',quantity:1}]})
 if(url.endsWith('/confirm')){writes++;state={proposal:null,receipts:[receipt]};return response(receipt)}
 if(url.endsWith('/result-introductions')){introductions++;assert.ok(container.querySelector('[data-receipt-id="r"]'),'receipt must be in DOM before expression admission');return response({session_id:'guide',request_id:'intro-request',run_id:'intro-run'},202)}
 if(url.includes('/runs/intro-run/stream'))return new Response(new ReadableStream({start(controller){stream=controller}}),{headers:{'Content-Type':'text/event-stream'}})
 if(url.endsWith('/turns/stop')){stops++;return response({cancelled:true})}
 throw new Error('Unexpected '+url)
}
const render=()=>act(async()=>root.render(createElement(AfterSalesPanel,{caseId:'case',orderId:'o',selectionVersion:1,refreshKey:0,disabled:false})))
await render()
await act(async()=>[...container.querySelectorAll('button')].find(b=>b.textContent==='确认提交此模拟申请').click())
assert.ok(container.querySelector('[data-receipt-id="r"]'))
assert.equal(writes,1)
assert.equal(introductions,1,'confirmed receipt should start one independent expression after render')
assert.ok(stream)
assert.equal(container.querySelector('select[aria-label="售后类型"]').disabled,false,'expression must not keep business controls busy')
const emit=(type,payload)=>stream.enqueue(new TextEncoder().encode('data: '+JSON.stringify({type,run_id:'intro-run',sequence:1,payload})+'\n\n'))
await act(async()=>emit('answer.delta',{delta:'模拟申请已提交，尚未审批或退款到账。可以稍后再看看。',message_id:'im'}))
assert.match(container.textContent,/可以稍后再看看/)
await act(async()=>emit('answer.delta',{delta:'模拟申请已提交，尚未审批或退款到账。可以稍后再看看。',message_id:'im'}))
assert.equal(container.textContent.split('可以稍后再看看').length-1,1,'Replayed event sequence must not duplicate visible text')
await act(async()=>{const select=container.querySelector('select[aria-label="售后类型"]');select.value='return';select.dispatchEvent(new dom.window.Event('change',{bubbles:true}))})
await act(async()=>{emit('answer.delta',{delta:'过期的介绍不应再显示',message_id:'im'});emit('turn.completed',{expression_status:'completed'});stream.close()})
assert.doesNotMatch(container.textContent,/过期的介绍/)
assert.ok(container.querySelector('[data-receipt-id="r"]'))
assert.equal(writes,1)
assert.equal(stops,1)
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['receipt visible before introduction request','controls usable during expression','incremental text','new action fences stale text','one confirmation write']}))

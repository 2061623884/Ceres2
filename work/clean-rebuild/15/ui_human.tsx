/** Controlled public component DOM. No real-browser/layout or provider claim. */
import assert from 'node:assert/strict'
import path from 'node:path'
import {createRequire} from 'node:module'
const rootDir=process.cwd()
const support=createRequire(path.join(process.env.MERCURY_TEST_SUPPORT!,'package.json'))
const {JSDOM}=support('jsdom')
const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,HTMLElement:dom.window.HTMLElement,IS_REACT_ACT_ENVIRONMENT:true})
const frontend=createRequire(path.join(rootDir,'frontend/package.json'))
const compiled=createRequire(path.join(process.env.MERCURY_COMPILED_DIR!,'package.json'))
const React=frontend('react');const {createRoot}=frontend('react-dom/client')
const {HumanCasePanel}=compiled('./HumanCasePanel.js');const {HumanOperatorPage}=compiled('./HumanOperatorPage.js')
const {act,createElement}=React
const container=document.getElementById('root')!
let root=createRoot(container)
let ticket:any=null
let messagesSent=0
let operatorTokens:string[]=[]
let pauseMutation=false
let completeMutation: (()=>void) | undefined
const json=(value:unknown,status=200)=>new Response(JSON.stringify(value),{status})
globalThis.fetch=async(input,options)=>{
 const url=String(input), body=options?.body ? JSON.parse(String(options.body)) : null
 if(url.includes('/operator/')){
  const token=new Headers(options?.headers).get('X-Internal-Token')!;operatorTokens.push(token)
  if(token!=='synthetic-operator-only')return json({detail:'需要独立的人工处理者凭据'},403)
  if(!body)return json([ticket])
  ticket={...ticket,status:body.action==='ask'?'waiting_user':body.action==='resolve'?'resolved':'open',version:ticket.version+1,
   messages:[...ticket.messages,{message_id:`m${++messagesSent}`,author:'operator',kind:body.action,content:body.content,created_at:'2026-10-05'}]}
  return json(ticket)
 }
 if(url.includes('/sessions/case-b/'))return json(null)
 if(url.endsWith('/human-ticket/messages')){
  assert.equal(body.ticket_id,ticket.ticket_id,'User reply must identify exact ticket, not only case/version')
  ticket={...ticket,status:'open',version:ticket.version+1,messages:[...ticket.messages,{message_id:`m${++messagesSent}`,author:'user',kind:'reply',content:body.content,created_at:'2026-10-05'}]};return json(ticket)
 }
 if(url.endsWith('/human-ticket')){
  if(body) ticket={ticket_id:'ht-synthetic',case_id:'case-a',owner_id:'owner-a',order_id:'order-a',order_summary:{order_id:'order-a',status:'paid',total_fen:1200,items:[{name:'杯子',quantity:1}]},reason:'explicit_user_request',summary:body.summary,status:'open',version:1,generation:2,history:[{role:'user',content:'查询问题'}],messages:[]}
  return json(ticket)
 }
 throw new Error(`Unexpected request ${url}`)
}
const immediateFetch=globalThis.fetch
globalThis.fetch=async(input,options)=>{
 const result=await immediateFetch(input,options)
 if(pauseMutation && options?.body){pauseMutation=false;return new Promise(resolve=>{completeMutation=()=>resolve(result)})}
 return result
}
async function click(text:string){const button=[...container.querySelectorAll('button')].find(el=>el.textContent===text)!;assert.ok(button,`Missing button ${text}`);await act(async()=>button.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
async function type(selector:string,value:string){await act(async()=>{const element=container.querySelector(selector)!;const prototype=element.tagName==='TEXTAREA'?dom.window.HTMLTextAreaElement.prototype:dom.window.HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(prototype,'value')!.set!.call(element,value);element.dispatchEvent(new dom.window.Event('input',{bubbles:true}));element.dispatchEvent(new dom.window.Event('change',{bubbles:true}))})}
async function mount(component:any,props={}){await act(async()=>root.unmount());root=createRoot(container);await act(async()=>root.render(createElement(component,props)))}
await act(async()=>root.render(createElement(HumanCasePanel,{caseId:'case-a'})))
await type('textarea','需要人工解释我的售后问题');await click('请求人工处理')
assert.match(container.textContent!,/等待人工处理/);assert.equal(ticket.case_id,'case-a')
await mount(HumanOperatorPage)
assert.equal(operatorTokens.length,0,'No operator request before credentials')
await type('input','wrong-token');await act(async()=>container.querySelector('form')!.dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true})))
assert.match(container.textContent!,/需要独立的人工处理者凭据/)
await type('input','synthetic-operator-only');await act(async()=>container.querySelector('form')!.dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true})))
await act(async()=>container.querySelector('[aria-label="工单列表"] button')!.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))
assert.match(container.textContent!,/order-a/);assert.match(container.textContent!,/杯子/);assert.match(container.textContent!,/查询问题/)
await type('textarea','请补充问题细节');await click('追问');assert.equal(ticket.status,'waiting_user')
await mount(HumanCasePanel,{caseId:'case-a'})
assert.match(container.textContent!,/等待您补充信息/);assert.match(container.textContent!,/请补充问题细节/)
await type('textarea','这里是补充信息');await click('发送补充信息');assert.equal(ticket.messages.at(-1).author,'user')
await mount(HumanOperatorPage)
await type('input','synthetic-operator-only');await act(async()=>container.querySelector('form')!.dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true})))
await act(async()=>container.querySelector('[aria-label="工单列表"] button')!.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))
await type('textarea','已解释清楚，没有退款操作');await click('解决');assert.equal(ticket.status,'resolved')
await mount(HumanCasePanel,{caseId:'case-a'});assert.match(container.textContent!,/已解决/)
await act(async()=>root.render(createElement(HumanCasePanel,{caseId:'case-b'})));assert.doesNotMatch(container.textContent!,/ht-synthetic/)
// A submitted draft is distinct from text typed while its request is in flight.
await mount(HumanCasePanel,{caseId:'case-a'})
await type('textarea','提交给人工的问题');pauseMutation=true;await click('请求人工处理')
await type('textarea','用户正在写的下一条消息');await act(async()=>completeMutation!())
assert.equal(container.querySelector('textarea')!.value,'用户正在写的下一条消息','In-flight user send must preserve newer draft')
await act(async()=>root.render(createElement(HumanCasePanel,{caseId:'case-a',refreshKey:1})))
assert.equal(container.querySelector('textarea')!.value,'用户正在写的下一条消息','Background refresh must preserve current-case draft')
await mount(HumanOperatorPage)
await type('input','synthetic-operator-only');await act(async()=>container.querySelector('form')!.dispatchEvent(new dom.window.Event('submit',{bubbles:true,cancelable:true})))
await act(async()=>container.querySelector('[aria-label="工单列表"] button')!.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))
await type('textarea','处理者先回复');pauseMutation=true;await click('回复')
await type('textarea','处理者正在写的下一条消息');await act(async()=>completeMutation!())
assert.equal(container.querySelector('textarea')!.value,'处理者正在写的下一条消息','In-flight operator send must preserve newer draft')
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,level:'controlled-DOM',checks:['explicit user request','operator deny by default','operator ask and context','user progress and reply','operator resolve','case change isolation']}))

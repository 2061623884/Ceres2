/** Public App DOM interactions with controlled transport. Not browser/live acceptance. */
import assert from 'node:assert/strict'
import path from 'node:path'
import {createRequire} from 'node:module'
const cwd=process.cwd(), support=createRequire(process.env.T05_DOM_SUPPORT ?? path.join(cwd,'work/clean-rebuild/02/test-support/package.json'))
const {JSDOM}=support('jsdom'), dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true})
dom.window.HTMLElement.prototype.scrollIntoView=function(){}
const frontend=createRequire(path.join(cwd,'frontend/package.json')), compiled=createRequire(path.join(cwd,process.argv[2] ?? 'work/local-cloud-integration/05/compiled/package.json'))
compiled.extensions['.css']=()=>{}
const React=frontend('react'), {act,createElement}=React, {createRoot}=frontend('react-dom/client')
const App=compiled('./App.js').default, container=document.getElementById('root')
const guide={session_id:'guide-one',task_id:null,state_version:0,session_version:0,task_status:null,entry_context:{page:'home'},available_actions:['send_message'],messages:[],product_cards:[],plan:null,pending_clarifications:[]}
const calls=[]; let opening=null, route=null, mode='yes', sequence=0, failNextBusiness=false, acceptedHandoff=null
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}})
globalThis.fetch=async(input, options={})=>{
 const url=String(input), body=options.body?JSON.parse(options.body):null;calls.push({url,body,method:options.method??'GET'})
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'})
 if(url.endsWith('/cart'))return response({version:0,items:[],total_price_fen:0})
 if(url.endsWith('/categories'))return response([])
 if(url.includes('/products'))return response({items:[]})
 if(url.includes('/navigation/')){
  if(url.endsWith('/opening')){if(!opening||opening.closed)opening={opening_id:'opening-'+(++sequence),role:body?.role??'keke',prompt_displayed:false,closed:false,pending_request_id:null};return response(opening)}
  if(options.method==='DELETE'){opening.closed=true;opening.pending_request_id=null;acceptedHandoff=null;return response(opening)}
  if(url.endsWith('/routes')){const outcome=body.role==='momo'?'not_attempted':mode;route={routing_request_id:body.request_id,original_message:body.message,selected_object:body.selected_object,status:outcome==='yes'?'switch':'ready',target_role:outcome==='yes'?'momo':body.role,continue_original:false,capability:null,entry_judgment:{outcome,elapsed_ms:outcome==='not_attempted'?null:1,reason:null},show_prompt:outcome==='yes'&&!opening.prompt_displayed,message:'要切换到墨墨吗？'};opening.pending_request_id=outcome==='yes'?body.request_id:null;return response(route)}
  if(url.endsWith('/prompt-displayed')){assert.match(container.textContent,/要切换到墨墨吗/,'ACK must occur only after visible prompt');opening.prompt_displayed=true;return response(opening)}
  if(url.endsWith('/switches')){const handoff=body.accept&&body.routing_request_id?route:null;if(body.accept)opening.role=body.target_role;opening.pending_request_id=null;return response({...opening,handoff})}
 }
 if(url==='/api/v1/guide/sessions')return response(guide)
 if(url.endsWith('/sessions/guide-one')||url.includes('/sessions/guide-one?'))return response(guide)
 if(url.endsWith('/status'))return response({...guide,runs:[]})
 if(url==='/api/v1/mercury/sessions')return response({session_id:'case-one'})
 if(url==='/api/v1/mercury/sessions/case-one')return response({session_id:'case-one',order_id:null,selection_version:0,messages:[],responsibility:'agent',status:'ready'})
 if(url==='/api/v1/mercury/orders')return response({orders:[]})
 if(url.includes('/aftersales'))return response({proposal:null,receipts:[]})
 if(url.includes('/human'))return response(null)
 if(url.endsWith('/turns/stream')){if(failNextBusiness){failNextBusiness=false;return new Response(JSON.stringify({error:{message:'该会话正忙，请重试'}}),{status:409,headers:{'Content-Type':'application/json'}})}acceptedHandoff=null;if(url.includes('/guide/'))return new Response('data: '+JSON.stringify({type:'turn.completed',payload:{...guide,request_id:body.request_id,message:'已保留原购物需求，尚未加购。',messages:[{message_id:'compound-result-'+body.request_id,content:'已保留原购物需求，尚未加购。'},{message_id:'policy-'+body.request_id,content:'一般政策说明'},{message_id:'boundary-'+body.request_id,content:'订单问题可以交给墨墨。'}],navigation_action:{type:'switch_role',session_id:guide.session_id,request:{opening_id:opening.opening_id,target_role:'momo',accept:true,routing_request_id:null}}}})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});return new Response('event: turn.completed\ndata: '+JSON.stringify({final_text:'已读取一般政策，未提交申请。',status:'completed'})+'\n\n',{headers:{'Content-Type':'text/event-stream'}})}
 throw new Error('Unexpected transport '+url)
}
let root=createRoot(container)
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
const button=text=>[...container.querySelectorAll('button')].find(b=>b.textContent===text)
async function send(text,placeholder='问问可可吧…'){const input=container.querySelector(`input[placeholder="${placeholder}"]`);assert.ok(input);await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,text);input.dispatchEvent(new dom.window.Event('input',{bubbles:true}))});await act(async()=>input.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true})))}
await act(async()=>root.render(createElement(App)))
await click(button('商品'));await click(button('问问可可'))
await send('查一下退款资格')
assert.equal(calls.filter(c=>c.url.endsWith('/turns/stream')).length,0)
await click(button('留在这里'))
assert.equal(opening.role,'keke')
await click(button('墨墨 · 订单售后'))
assert.equal(calls.filter(c=>c.url.endsWith('/turns/stream')).length,0,'Pure role button cannot replay rejected original')
await send('回到购物，再查我的订单','问问墨墨吧…')
assert.equal(route.entry_judgment.outcome,'not_attempted')
assert.equal(opening.role,'momo','Momo text cannot navigate')
await click(button('可可 · 选购'))
const count=calls.filter(c=>c.url.endsWith('/turns/stream')).length
for(const outcome of ['no','uncertain','timeout','error']){mode=outcome;await send('保留完整原文 '+outcome)}
assert.equal(calls.filter(c=>c.url.endsWith('/turns/stream')).length,count+4)
assert.match(container.textContent,/一般政策说明/)
assert.match(container.textContent,/订单问题可以交给墨墨/)
assert.ok(button('前往墨墨处理'),'Mixed result exposes explicit navigation action')
const beforeAction=calls.filter(c=>c.url.endsWith('/turns/stream')).length
await click(button('前往墨墨处理'))
assert.equal(calls.filter(c=>c.url.endsWith('/switches')).at(-1).body.routing_request_id,null)
assert.equal(calls.filter(c=>c.url.endsWith('/turns/stream')).length,beforeAction)
await click(container.querySelector('[aria-label="关闭聊天"]'))
await click(button('问问墨墨'))
assert.equal(calls.filter(c=>c.url.endsWith('/turns/stream')).length,beforeAction)
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,level:'DOM-controlled-transport',checks:['yes reject','pure button no replay','Momo text direct','four Coco fallback outcomes','mixed message action','close reopen no replay']}))

/** Public App DOM interactions with controlled transport. Not browser/live acceptance. */
import assert from 'node:assert/strict'
import path from 'node:path'
import {createRequire} from 'node:module'
const cwd=process.cwd(), support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'))
const {JSDOM}=support('jsdom'), dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true})
dom.window.HTMLElement.prototype.scrollIntoView=function(){}
const frontend=createRequire(path.join(cwd,'frontend/package.json')), compiled=createRequire(path.join(cwd,process.argv[2] ?? 'work/next-experience/03/compiled/package.json'))
compiled.extensions['.css']=()=>{}
const React=frontend('react'), {act,createElement}=React, {createRoot}=frontend('react-dom/client')
const App=compiled('./App.js').default, container=document.getElementById('root')
const guide={session_id:'guide-one',task_id:null,state_version:0,session_version:0,task_status:null,entry_context:{page:'home'},available_actions:['send_message'],messages:[],product_cards:[],plan:null,pending_clarifications:[]}
const calls=[]; let opening=null, route=null, mode='switch', sequence=0, failNextBusiness=false, acceptedHandoff=null
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
  if(url.endsWith('/routes')){route={routing_request_id:body.request_id,original_message:body.message,selected_object:null,status:mode,target_role:mode==='navigation'?'keke':'momo',continue_original:mode==='navigation',show_prompt:mode==='switch'&&!opening.prompt_displayed,message:mode==='unavailable'?'职责判断暂时不可用，请手动选择角色':'要切换到墨墨吗？'};opening.pending_request_id=mode==='navigation'?null:body.request_id;if(mode==='navigation'){opening.role='keke';acceptedHandoff=route}return response(route)}
  if(url.endsWith('/prompt-displayed')){assert.match(container.textContent,/要切换到墨墨吗/,'ACK must occur only after visible prompt');opening.prompt_displayed=true;return response(opening)}
  if(url.endsWith('/switches')){if(body.accept&&opening.pending_request_id)acceptedHandoff=route;if(!body.accept)acceptedHandoff=null;const handoff=body.accept?acceptedHandoff:null;if(body.accept)opening.role=body.target_role;opening.pending_request_id=null;return response({...opening,handoff})}
 }
 if(url==='/api/v1/guide/sessions')return response(guide)
 if(url.endsWith('/sessions/guide-one')||url.includes('/sessions/guide-one?'))return response(guide)
 if(url.endsWith('/status'))return response({...guide,runs:[]})
 if(url==='/api/v1/mercury/sessions')return response({session_id:'case-one'})
 if(url==='/api/v1/mercury/sessions/case-one')return response({session_id:'case-one',order_id:null,selection_version:0,messages:[],responsibility:'agent',status:'ready'})
 if(url==='/api/v1/mercury/orders')return response({orders:[]})
 if(url.includes('/aftersales'))return response({proposal:null,receipts:[]})
 if(url.includes('/human'))return response(null)
 if(url.endsWith('/turns/stream')){if(failNextBusiness){failNextBusiness=false;return new Response(JSON.stringify({error:{message:'该会话正忙，请重试'}}),{status:409,headers:{'Content-Type':'application/json'}})}acceptedHandoff=null;if(url.includes('/guide/'))return new Response('data: '+JSON.stringify({type:'turn.completed',payload:{...guide,request_id:body.request_id,message:'已保留原购物需求，尚未加购。',messages:[{message_id:'compound-result',content:'已保留原购物需求，尚未加购。'}]}})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});return new Response('event: turn.completed\ndata: '+JSON.stringify({final_text:'已读取一般政策，未提交申请。',status:'completed'})+'\n\n',{headers:{'Content-Type':'text/event-stream'}})}
 throw new Error('Unexpected transport '+url)
}
let root=createRoot(container)
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
const button=text=>[...container.querySelectorAll('button')].find(b=>b.textContent===text)
async function send(text,placeholder='问问可可吧…'){const input=container.querySelector(`input[placeholder="${placeholder}"]`);assert.ok(input);await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,text);input.dispatchEvent(new dom.window.Event('input',{bubbles:true}))});await act(async()=>input.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true})))}
await act(async()=>root.render(createElement(App)))
await click(button('商品'));await click(button('问问可可'));const firstOpening=opening.opening_id
await send('查一下退款资格')
assert.match(container.textContent,/要切换到墨墨吗/)
assert.equal(calls.filter(c=>c.url.endsWith('/turns/stream')).length,0,'No other role may execute before user choice')
assert.equal(opening.prompt_displayed,true)
await click(button('留在这里'))
assert.equal(opening.role,'keke')
await act(async()=>root.unmount());root=createRoot(container);await act(async()=>root.render(createElement(App)))
assert.equal(opening.opening_id,firstOpening);assert.equal(opening.prompt_displayed,true)
await send('查另一笔退款资格')
assert.equal(button('切换并继续原请求'),undefined,'Quota survives refresh')
await click(button('墨墨 · 订单售后'))
assert.equal(calls.filter(c=>c.url.endsWith('/routes')).length,2,'Manual acceptance must not rejudge')
assert.equal(calls.filter(c=>c.url.endsWith('/turns/stream')).length,1,'Original request is resumed once')
assert.equal(calls.find(c=>c.url.endsWith('/turns/stream')).body.message,'查另一笔退款资格')
await click(container.querySelector('[aria-label="关闭聊天"]'))
assert.equal(opening.closed,true)
await click(button('问问墨墨'))
assert.notEqual(opening.opening_id,firstOpening);assert.equal(opening.prompt_displayed,false)
await click(button('可可 · 选购'));mode='unavailable'
await send('帮我选择零食')
assert.match(container.textContent,/职责判断暂时不可用/)
assert.ok(button('墨墨 · 订单售后'));assert.equal(button('墨墨 · 订单售后').disabled,false)
failNextBusiness=true
await click(button('墨墨 · 订单售后'))
assert.equal(calls.filter(c=>c.url.endsWith('/turns/stream')).length,2,'First manual business admission fails visibly')
await click(button('墨墨 · 订单售后'))
const businessCalls=calls.filter(c=>c.url.endsWith('/turns/stream'))
assert.equal(businessCalls.length,3,'Explicit manual retry must not be suppressed by the previous handoff effect')
assert.equal(businessCalls[1].body.request_id,businessCalls[2].body.request_id,'Retry retains original idempotency identity')
assert.equal(calls.filter(c=>c.url.endsWith('/routes')).length,3,'Manual retry never rejudges')
mode='navigation'
const compound='回到购物，来点零食，预算二十元，再告诉我退货政策'
const switchesBefore=calls.filter(c=>c.url.endsWith('/switches')).length
await send(compound,'问问墨墨吧…')
assert.equal(opening.role,'keke')
assert.equal(button('切换并继续原请求'),undefined,'Explicit role choice must not be confirmed again')
assert.equal(calls.filter(c=>c.url.endsWith('/switches')).length,switchesBefore)
const continued=calls.filter(c=>c.url.includes('/guide/')&&c.url.endsWith('/turns/stream'))
assert.equal(continued.length,1,'Compound explicit return continues the shopping goal on Keke')
assert.equal(continued[0].body.message,compound)
assert.equal(calls.filter(c=>c.url.endsWith('/routes')).length,4,'Continuation reuses the single joint judgment')
assert.equal(calls.filter(c=>c.url.endsWith('/confirm')).length,0,'Navigation never authorizes cart writes')
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['visible ACK','decline','refresh quota','manual original request once','explicit close resets','visible provider failure and manual role entry','explicit retry after failed admission retains request identity','compound explicit return preserves full goal without another confirmation or judge']}))

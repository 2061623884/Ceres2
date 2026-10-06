/** Actual App controls with a controlled transport. Public API journey is separate. */
import assert from 'node:assert/strict'
import path from 'node:path'
import {createRequire} from 'node:module'
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'))
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true})
dom.window.HTMLElement.prototype.scrollIntoView=function(){}
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,process.argv[2]??'work/next-experience/03/compiled/package.json'))
compiled.extensions['.css']=()=>{}
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),App=compiled('./App.js').default
const container=document.getElementById('root'),calls=[]
const product={sku_id:'chips',name:'原味薯片',name_zh:'原味薯片',category_id:'snack',price_fen:600,sellable:true,spec_unit:'袋',spec_quantity:1,image_path:null}
const item={sku_id:'chips',name:'原味薯片',quantity:1,unit_price_fen:600,line_total_fen:600,image_path:null,returnable:true,return_policy_source:'demo'}
let cart={version:0,items:[],total_price_fen:0},orders=[],opening=null,after={proposal:null,receipts:[]}
let mercury={session_id:'case',order_id:null,selection_version:0,responsibility:'agent',status:'ready',messages:[]}
const guide={session_id:'guide',task_id:null,state_version:0,session_version:0,task_status:null,entry_context:{page:'home'},available_actions:['send_message'],messages:[],product_cards:[],plan:null,pending_clarifications:[]}
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}})
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;calls.push({url,body,method:options.method??'GET'})
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'})
 if(url.endsWith('/cart/items')){assert.equal(body.expected_cart_version,cart.version);cart={version:cart.version+1,items:[item],total_price_fen:600};return response(cart)}
 if(url.endsWith('/cart'))return response(cart)
 if(url.endsWith('/categories'))return response([{id:'snack',name:'零食'}])
 if(url.includes('/products'))return response({items:[product]})
 if(url.endsWith('/checkout/preview'))return response({preview_id:'checkout-preview',cart_version:cart.version,store_id:'store',items:cart.items,total_fen:600,business_data_mode:'demo'})
 if(url.endsWith('/checkout/confirm')){assert.equal(body.confirmed,true);orders=[{order_id:'new-checkout-order',status:'submitted',version:1,store_id:'store',items:cart.items,total_fen:600,business_data_mode:'demo',created_at:'2026-10-06T09:00:00Z',delivered_at:null}];cart={version:cart.version+1,items:[],total_price_fen:0};return response({receipt_id:'checkout-receipt',order:orders[0],cart_version:cart.version})}
 if(url==='/api/v1/orders')return response({items:orders})
 if(url==='/api/v1/orders/new-checkout-order')return response(orders[0])
 if(url==='/api/v1/mercury/orders')return response({orders:orders.map(o=>({...o,status_text:'模拟已提交',total:'6.00',products:['原味薯片']}))})
 if(url==='/api/v1/mercury/sessions')return response({session_id:'case'})
 if(url==='/api/v1/mercury/sessions/case')return response(mercury)
 if(url.endsWith('/sessions/case/order')){assert.equal(body.order_id,orders[0].order_id);mercury={...mercury,order_id:body.order_id,selection_version:mercury.selection_version+1};return response(mercury)}
 if(url.endsWith('/aftersales'))return response(after)
 if(url.endsWith('/human-ticket'))return response(null)
 if(url.endsWith('/proposals')){assert.equal(body.selection_version,mercury.selection_version);after={...after,proposal:{proposal_id:'proposal',revision:1,order_id:mercury.order_id,kind:body.kind,reason:body.reason,amount_fen:600,policy_id:'P-REF-01',policy:'未发货整单模拟退款；申请不代表到账',items:[{item_id:'chips',name:'原味薯片',quantity:1,amount_fen:600}]}};return response(after.proposal)}
 if(url.endsWith('/sessions/case/confirm')){assert.equal(body.confirmed,true);assert.equal(body.proposal_id,'proposal');const receipt={...after.proposal,receipt_id:'receipt',application_id:'application',status:'requested',message:'模拟申请已提交，尚未审批或退款到账'};after={proposal:null,receipts:[receipt]};return response(receipt)}
 if(url.includes('/navigation/')){
  if(url.endsWith('/opening')){if(!opening)opening={opening_id:'opening',role:body?.role??'momo',prompt_displayed:false,closed:false,pending_request_id:null};return response(opening)}
  if(options.method==='DELETE'){opening=null;return response({closed:true})}
  if(url.endsWith('/switches')){opening.role=body.target_role;return response({...opening,handoff:null})}
  if(url.endsWith('/routes')){opening.role='keke';return response({routing_request_id:body.request_id,original_message:body.message,selected_object:body.selected_object,status:'navigation',target_role:'keke',continue_original:true,show_prompt:false})}
 }
 if(url==='/api/v1/guide/sessions'||url==='/api/v1/guide/sessions/guide'||url.startsWith('/api/v1/guide/sessions/guide?'))return response(guide)
 if(url.endsWith('/status'))return response({...guide,runs:[]})
 if(url.endsWith('/guide/sessions/guide/turns/stream'))return new Response('data: '+JSON.stringify({type:'turn.completed',payload:{...guide,request_id:body.request_id,message:'已重新查看当前零食供给，尚未加购。',messages:[{message_id:'replacement',content:'已重新查看当前零食供给，尚未加购。'}]}})+'\n\n',{headers:{'Content-Type':'text/event-stream'}})
 throw new Error('Unexpected transport '+url)
}
let root=createRoot(container)
const button=text=>[...container.querySelectorAll('button')].find(b=>b.textContent===text)
async function click(el){assert.ok(el);await act(async()=>el.click())}
async function input(el,text){assert.ok(el);await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(el,text);el.dispatchEvent(new dom.window.Event('input',{bubbles:true}))})}
await act(async()=>root.render(createElement(App)))
await click(button('商品'));await click(container.querySelector('[aria-label="添加原味薯片到购物车"]'))
assert.equal(orders.length,0);await click(container.querySelector('[aria-label="购物车"]'));await click(button('模拟结算'))
assert.equal(orders.length,0,'Cart and checkout preview must not create orders')
await click(button('确认模拟结算'));await click(button('查看订单'))
await click(container.querySelector('[aria-label="查看订单 new-checkout-order"]'));await click(button('联系墨墨'))
assert.equal(container.querySelector('[aria-label="选择模拟订单"]').value,'new-checkout-order')
assert.equal(after.receipts.length,0);assert.equal(calls.filter(c=>c.url.endsWith('/turns/stream')).length,0,'Order entry does not query or submit implicitly')
await input(container.querySelector('[aria-label="售后原因"]'),'想换一种零食');await click(button('查看申请提案'))
assert.equal(after.receipts.length,0);assert.ok(container.querySelector('[data-proposal-id="proposal"]'))
await click(button('确认提交此模拟申请'))
assert.ok(container.querySelector('[data-receipt-id="receipt"]'));assert.match(container.textContent,/尚未审批或退款到账/)
const original='回到购物，换一种零食，预算二十元'
const field=container.querySelector('input[placeholder="问问墨墨吧…"]');await input(field,original)
await act(async()=>field.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true})))
const continued=calls.filter(c=>c.url.endsWith('/guide/sessions/guide/turns/stream'))
assert.equal(continued.length,1);assert.equal(continued[0].body.message,original)
assert.equal(continued[0].body.request_id,calls.find(c=>c.url.endsWith('/routes')).body.request_id)
assert.equal(calls.filter(c=>c.url.endsWith('/routes')).length,1)
assert.equal(button('切换并继续原请求'),undefined)
await click(button('墨墨 · 订单售后'))
assert.ok(container.querySelector('[data-receipt-id="receipt"]'))
await click(container.querySelector('[aria-label="关闭聊天"]'));await click(button('问问墨墨'))
assert.ok(container.querySelector('[data-receipt-id="receipt"]'))
assert.equal(calls.filter(c=>c.url.endsWith('/sessions/case/confirm')).length,1,'Navigation and reopening must not resubmit')
assert.equal(cart.items.length,0,'Replacement request is not cart consent')
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['explicit cart','independent checkout','exact new-order contact','concrete proposal','explicit application','compound return with original request identity','receipt restored after switch and close','no repeated application']}))

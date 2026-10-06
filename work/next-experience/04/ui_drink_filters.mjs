/** Actual App clicks over controlled public transport. DOM-only, not real browser. */
import assert from 'node:assert/strict'
import path from 'node:path'
import {createRequire} from 'node:module'
const cwd=process.cwd(), support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'))
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true})
dom.window.HTMLElement.prototype.scrollIntoView=function(){}
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/next-experience/04/compiled/package.json'))
compiled.extensions['.css']=()=>{}
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),App=compiled('./App.js').default,container=document.getElementById('root')
const q1={question_id:'question-type',session_id:'guide-one',task_id:'task-one',state_version:0,session_version:1,kind:'category',question:'想看哪类饮品？',status:'active',selected_option_ids:[],options:[{option_id:'type-chips',label:'茶饮',value:'potato_chips'},{option_id:'type-crackers',label:'饮用水',value:'soda_crackers'}]}
const product=(sku,name,size,price)=>({sku_id:sku,name,name_zh:name,brand:null,spec_quantity:size,spec_unit:'ml',price_fen:price,available_qty:5,sellable:true,offer_version:1,metadata:{packaging:'bottle',pack_count:1,flavor:'桃味'}})
const q2={...q1,question_id:'question-products',state_version:1,kind:'products',question:'请选择商品和销售包装数量，选定后再核对清单。',options:[{option_id:'chips-large',label:'桃味茶330毫升',value:'chips70',product:product('chips70','桃味茶330毫升',330,600)},{option_id:'chips-small',label:'桃味茶500毫升',value:'chips35',product:product('chips35','桃味茶500毫升',500,400)}]}
const q3={...q2,question_id:'question-filtered',state_version:2,filter_options:[{option_id:'clear-flavor',label:'取消口味筛选',attribute:'flavor',value:null}]}
q2.filter_options=[{option_id:'filter-peach',label:'口味：桃味',attribute:'flavor',value:'桃味'}]
const msg=q=>({message_id:q.question_id,session_id:'guide-one',task_id:'task-one',sequence:q.state_version+1,role:'assistant',kind:'question',content:q.question,request_id:q.question_id})
const state={session_id:'guide-one',task_id:'task-one',state_version:0,session_version:1,task_status:'active',entry_context:{page:'home'},available_actions:['send_message'],messages:[msg(q1)],product_cards:[],plan:null,pending_clarifications:[],active_question:q1,question_history:[q1]}
const calls=[];let cart=[]
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}})
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;calls.push({url,body})
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'})
 if(url.endsWith('/cart'))return response({version:cart.length?1:0,items:cart,total_price_fen:cart.length?1000:0})
 if(url.endsWith('/categories'))return response([])
 if(url.includes('/products'))return response({items:[]})
 if(url.includes('/navigation/')&&url.endsWith('/opening'))return response({opening_id:'opening-one',role:'keke',prompt_displayed:false,closed:false,pending_request_id:null})
 if(url.endsWith('/questions/question-type/answers')){
  assert.deepEqual(body.option_ids,['type-chips']);assert.deepEqual(body.quantities,{});assert.equal(body.expected_state_version,0);assert.equal(body.message,undefined)
  q1.status='answered';q1.selected_option_ids=['type-chips'];state.state_version=1;state.active_question=q2;state.question_history=[q1,q2];state.messages.push(msg(q2));return response(state)
 }
 if(url.endsWith('/questions/question-products/answers')){
  assert.deepEqual(body.option_ids,['filter-peach']);assert.deepEqual(body.quantities,{});assert.equal(body.expected_state_version,1)
  q2.status='answered';q2.selected_option_ids=['filter-peach'];state.state_version=2;state.active_question=q3;state.question_history=[q1,q2,q3];state.messages.push(msg(q3));return response(state)
 }
 if(url.endsWith('/questions/question-filtered/answers')){
  assert.deepEqual(new Set(body.option_ids),new Set(['chips-large','chips-small']));assert.deepEqual(body.quantities,{'chips-large':1,'chips-small':1})
  q3.status='answered';q3.selected_option_ids=body.option_ids;state.state_version=3;state.active_question=null;state.plan={plan_id:'plan-snack',plan_version:1,mode:'bundle',items:q2.options.map(o=>({sku_id:o.value,name:o.label,quantity:1,selected:true,added_quantity:0,remaining_quantity:1,unit_price_fen:o.product.price_fen,line_total_fen:o.product.price_fen})),total_price_fen:1000,selected_total_fen:1000,expires_at:null,validation_status:'valid',can_confirm:true};state.available_actions=['send_message','modify','confirm'];return response(state)
 }
 if(url.endsWith('/confirm')){
  assert.equal(body.selected_items.length,2);cart=state.plan.items.map(r=>({...r}));state.state_version=4;state.plan.can_confirm=false;state.plan.items.forEach(r=>{r.added_quantity=1;r.remaining_quantity=0});state.available_actions=['send_message','modify'];return response({operation_id:'op',confirmation_id:'receipt',status:'success',items_added:body.selected_items,cart_version:1,errors:[],task_id:'task-one',state_version:4,session_version:1})
 }
 if(url.endsWith('/status'))return response({...state,runs:[]})
 if(url==='/api/v1/guide/sessions'||url.includes('/sessions/guide-one?')||url.endsWith('/sessions/guide-one'))return response(state)
 throw new Error('Unexpected public request '+url)
}
const root=createRoot(container),button=text=>[...container.querySelectorAll('button')].find(b=>b.textContent===text)
async function click(element){assert.ok(element,'Required visible control exists');await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
async function input(element,text){assert.ok(element);await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(element,text);element.dispatchEvent(new dom.window.Event('input',{bubbles:true}))})}
await act(async()=>root.render(createElement(App)))
await click(button('商品'));await click(button('问问可可'))
await click(button('茶饮'))
assert.equal(button('茶饮').disabled,true,'Answered category remains in history and disabled')
assert.match(container.textContent,/桃味茶330毫升/);assert.match(container.textContent,/品牌：未知/)
await click(button('口味：桃味'))
assert.equal(button('口味：桃味').disabled,true,'Answered filter stays disabled in its original question')
assert.match(container.textContent,/口味：桃味/);assert.match(container.textContent,/库存：5/);assert.match(container.textContent,/瓶装/)
await click([...container.querySelectorAll('[aria-label="选择 桃味茶330毫升"]')].find(e=>!e.disabled))
await click([...container.querySelectorAll('[aria-label="选择 桃味茶500毫升"]')].find(e=>!e.disabled))
await input([...container.querySelectorAll('[aria-label="数量 桃味茶330毫升"]')].find(e=>!e.disabled),'1')
await input([...container.querySelectorAll('[aria-label="数量 桃味茶500毫升"]')].find(e=>!e.disabled),'1')
assert.equal(cart.length,0)
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='生成采购清单'&&!b.disabled))
assert.equal(cart.length,0,'Product selection cannot add to cart')
if(!button('确认加购'))await click(container.querySelector('[aria-label="采购清单 2 件"]'))
await click(button('确认加购'))
assert.equal(cart.length,2)
assert.equal(calls.filter(c=>c.url.includes('/turns/stream')||c.url.endsWith('/routes')).length,0,'Typed choices use no text or Kev route')
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['typed drink category identity','typed factual filter identity','filter history disabled','flavor packaging stock display','answered history disabled','unknown attributes','multiple product selection','separate explicit cart confirmation','zero text routing']}))

/** Actual App clicks over controlled public transport. DOM-only, not real browser. */
import assert from 'node:assert/strict'
import path from 'node:path'
import {createRequire} from 'node:module'
const cwd=process.cwd(), support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'))
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true})
dom.window.HTMLElement.prototype.scrollIntoView=function(){}
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/next-experience/01/compiled/package.json'))
compiled.extensions['.css']=()=>{}
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),App=compiled('./App.js').default,container=document.getElementById('root')
const q1={question_id:'question-type',session_id:'guide-one',task_id:'task-one',state_version:0,session_version:1,kind:'category',question:'想看哪类零食？',status:'active',selected_option_ids:[],options:[{option_id:'type-chips',label:'薯片',value:'potato_chips'},{option_id:'type-crackers',label:'饼干',value:'soda_crackers'}]}
const product=(sku,name,size,price)=>({sku_id:sku,name,name_zh:name,brand:null,spec_quantity:size,spec_unit:'g',price_fen:price,available_qty:5,sellable:true,offer_version:1,metadata:{packaging:'bag',pack_count:1}})
const q2={...q1,question_id:'question-products',state_version:1,kind:'products',question:'请选择商品和销售包装数量，选定后再核对清单。',options:[{option_id:'chips-large',label:'原味薯片70克',value:'chips70',product:product('chips70','原味薯片70克',70,600)},{option_id:'chips-small',label:'原味薯片35克',value:'chips35',product:product('chips35','原味薯片35克',35,400)}]}
const msg=q=>({message_id:q.question_id,session_id:'guide-one',task_id:'task-one',sequence:q.state_version+1,role:'assistant',kind:'question',content:q.question,request_id:q.question_id})
const state={session_id:'guide-one',task_id:'task-one',state_version:0,session_version:1,task_status:'active',entry_context:{page:'home'},available_actions:['send_message'],messages:[msg(q1)],product_cards:[],plan:null,pending_clarifications:[],active_question:q1,question_history:[q1]}
const calls=[];let cart=[];const intros=[];let restoredRuns=[]
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}})
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;calls.push({url,body,headers:options.headers})
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'})
 if(url.endsWith('/cart'))return response({version:cart.length?1:0,items:cart,total_price_fen:cart.length?1000:0})
 if(url.endsWith('/categories'))return response([])
 if(url.includes('/products'))return response({items:[]})
 if(url.includes('/navigation/')&&url.endsWith('/opening'))return response({opening_id:'opening-one',role:'keke',prompt_displayed:false,closed:false,pending_request_id:null})
 if(url.endsWith('/result-introductions')){
  const sourceCall=body.source_kind==='purchase_confirmation'?calls.find(c=>c.url.endsWith('/confirm')):calls.find(c=>c.body?.request_id===body.source_id&&!c.url.endsWith('/result-introductions'))
  assert.ok(sourceCall,'Introduction references a completed business action, never a new key')
  if(intros.length===0){assert.ok(container.querySelector('[aria-label="选择 原味薯片70克"]'),'Cards render before expression admission');assert.equal(container.querySelector('[aria-label="选择 原味薯片70克"]').disabled,false)}
  if(intros.length===1){assert.ok(button('确认加购'),'Prepared plan is visible before expression');assert.equal(button('确认加购').disabled,false)}
  if(body.source_kind==='purchase_confirmation')assert.match(container.textContent,/模拟加购回执/,'Authoritative receipt appears before expression')
  const run={run_id:'intro-'+(intros.length+1),request_id:'intro-request-'+(intros.length+1),session_id:state.session_id,source:body};intros.push(run);return response(run)
 }
 if(url.includes('/runs/intro-')&&url.includes('/stream')){
  const run=intros.find(r=>url.includes('/runs/'+r.run_id+'/'));assert.ok(run,'Restore must not treat unrelated expression runs as business runs')
  run.signal=options.signal;return new Response(new ReadableStream({start(controller){run.controller=controller}}),{headers:{'Content-Type':'text/event-stream'}})
 }
 if(url.endsWith('/turns/stop'))return response({cancelled:true})
 if(url.includes('/navigation/')&&url.endsWith('/routes'))return response({status:'ready',routing_request_id:body.request_id,original_message:body.message,target_role:'keke',show_prompt:false})
 if(options.method==='DELETE'&&url.includes('/navigation/'))return response({closed:true})
 if(url.endsWith('/turns/stream')){
  const result={...state,request_id:body.request_id,runtime_status:'completed',no_matches:true,product_cards:[],message:'本次没有匹配商品。',messages:[{message_id:'no-match-result',content:'本次没有匹配商品。'}]}
  return new Response('data: '+JSON.stringify({type:'turn.completed',payload:result})+'\n\n',{headers:{'Content-Type':'text/event-stream'}})
 }
 if(url.endsWith('/questions/question-type/answers')){
  assert.deepEqual(body.option_ids,['type-chips']);assert.deepEqual(body.quantities,{});assert.equal(body.expected_state_version,0);assert.equal(body.message,undefined)
  q1.status='answered';q1.selected_option_ids=['type-chips'];state.state_version=1;state.active_question=q2;state.question_history=[q1,q2];state.messages.push(msg(q2));return response(state)
 }
 if(url.endsWith('/questions/question-products/answers')){
  assert.deepEqual(new Set(body.option_ids),new Set(['chips-large','chips-small']));assert.deepEqual(body.quantities,{'chips-large':1,'chips-small':1})
  q2.status='answered';q2.selected_option_ids=body.option_ids;state.state_version=2;state.active_question=null;state.plan={plan_id:'plan-snack',plan_version:1,mode:'bundle',items:q2.options.map(o=>({sku_id:o.value,name:o.label,quantity:1,selected:true,added_quantity:0,remaining_quantity:1,unit_price_fen:o.product.price_fen,line_total_fen:o.product.price_fen})),total_price_fen:1000,selected_total_fen:1000,expires_at:null,validation_status:'valid',can_confirm:true};state.available_actions=['send_message','modify','confirm'];return response(state)
 }
 if(url.endsWith('/confirm')){
  assert.equal(body.selected_items.length,2);cart=state.plan.items.map(r=>({...r}));state.state_version=3;state.plan.can_confirm=false;state.plan.items.forEach(r=>{r.added_quantity=1;r.remaining_quantity=0});state.available_actions=['send_message','modify'];return response({operation_id:'op',confirmation_id:'receipt',status:'success',items_added:body.selected_items,cart_version:1,errors:[],task_id:'task-one',state_version:3,session_version:1})
 }
 if(url.endsWith('/status'))return response({...state,runs:restoredRuns})
 if(url==='/api/v1/guide/sessions'||url.includes('/sessions/guide-one?')||url.endsWith('/sessions/guide-one'))return response(state)
 throw new Error('Unexpected public request '+url)
}
let root=createRoot(container);const button=text=>[...container.querySelectorAll('button')].find(b=>b.textContent===text)
async function click(element){assert.ok(element,'Required visible control exists');await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
async function input(element,text){assert.ok(element);await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(element,text);element.dispatchEvent(new dom.window.Event('input',{bubbles:true}))})}
async function expression(run,type,payload,sequence){if(sequence===undefined){run.sequence=(run.sequence??0)+1;sequence=run.sequence}await act(async()=>run.controller.enqueue(new TextEncoder().encode('data: '+JSON.stringify({protocol_version:1,run_id:run.run_id,sequence,session_id:state.session_id,type,payload})+'\n\n')))}
async function finish(run,status){await expression(run,'turn.completed',{...state,answer_kind:'result_introduction',expression_status:status,messages:[]});await act(async()=>run.controller.close())}
await act(async()=>root.render(createElement(App)))
await click(button('商品'));await click(button('问问可可'))
await click(button('薯片'))
assert.equal(intros.length,1,'Post-render expression begins for actual category result')
assert.equal(intros[0].source.source_kind,'question_answer')
assert.equal(container.querySelector('[aria-label="选择 原味薯片70克"]').disabled,false,'Introduction never disables actionable cards')
await expression(intros[0],'answer.delta',{delta:'可以慢慢挑选。',message_id:'intro-text-one',answer_kind:'result_introduction',replace:true})
await expression(intros[0],'answer.delta',{delta:'可以慢慢挑选。',message_id:'intro-text-one',answer_kind:'result_introduction',replace:true},1)
assert.equal(container.textContent.split('可以慢慢挑选。').length-1,1,'Duplicate SSE sequence is not rendered twice')
assert.match(container.textContent,/可以慢慢挑选。/,'A validated fragment is visible before generation ends')
await click(container.querySelector('[aria-label="选择 原味薯片70克"]'))
assert.equal(intros[0].signal.aborted,true,'Newer local selection cancels the older introduction')
assert.ok(calls.some(c=>c.url.endsWith('/turns/stop')&&c.body.request_id===intros[0].request_id))
await expression(intros[0],'answer.delta',{delta:'不应出现的旧介绍',message_id:'intro-text-one'})
await finish(intros[0],'stopped')
assert.doesNotMatch(container.textContent,/不应出现的旧介绍/)
await click(container.querySelector('[aria-label="选择 原味薯片35克"]'))
await input(container.querySelector('[aria-label="数量 原味薯片70克"]'),'1')
await input(container.querySelector('[aria-label="数量 原味薯片35克"]'),'1')
await click(button('生成采购清单'))
assert.equal(intros.length,2)
assert.equal(cart.length,0)
assert.equal(button('确认加购').disabled,false,'Plan confirmation remains usable while introduction is running')
await finish(intros[1],'failed')
assert.match(container.textContent,/介绍未完成/)
assert.equal(container.querySelector('[aria-label="停止结果介绍"]'),null,'Failed expression ends only its own loader')
assert.equal(button('确认加购').disabled,false)
assert.equal(calls.filter(c=>c.url.endsWith('/questions/question-products/answers')).length,1,'Expression failure never repeats business selection')
await click(button('确认加购'))
assert.equal(cart.length,2)
assert.equal(intros.length,3)
assert.equal(intros[2].source.source_kind,'purchase_confirmation')
assert.equal(intros[2].source.source_id,calls.find(c=>c.url.endsWith('/confirm')).headers['Idempotency-Key'])
await click(container.querySelector('[aria-label="停止结果介绍"]'))
assert.equal(intros[2].signal.aborted,true)
await finish(intros[2],'stopped')
assert.equal(cart.length,2)
assert.match(container.textContent,/模拟加购回执/)
assert.equal(calls.filter(c=>c.url.endsWith('/confirm')).length,1)
const chat=container.querySelector('input[placeholder="问问可可吧…"]')
await input(chat,'查找另一种商品')
await act(async()=>chat.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true})))
assert.equal(intros.length,4,'Eligible completed text result also gets expression-only continuation')
assert.equal(intros[3].source.source_kind,'turn')
await click(container.querySelector('[aria-label="关闭聊天"]'))
assert.equal(intros[3].signal.aborted,true,'Leaving view cancels expression transport and exact server run')
await expression(intros[3],'answer.delta',{delta:'离开后不应出现',message_id:'late-view-intro'})
await finish(intros[3],'stopped')
restoredRuns=[{run_id:'intro-old-momo',request_id:'old-momo',status:'completed',input:{kind:'result_introduction',role:'momo'},result:{answer_kind:'result_introduction',messages:[{message_id:'foreign-momo',content:'墨墨专用介绍不应进入可可'}]}},{run_id:'intro-old-keke',request_id:'old-keke',status:'running',input:{kind:'result_introduction',role:'keke'}}]
state.messages.push({message_id:'validated-history',role:'assistant',kind:'introduction',content:'已校验的可可介绍',request_id:'old-keke'})
await act(async()=>root.unmount());root=createRoot(container)
await act(async()=>root.render(createElement(App)))
await click(button('商品'));await click(button('问问可可'))
assert.match(container.textContent,/已校验的可可介绍/)
assert.doesNotMatch(container.textContent,/墨墨专用介绍|离开后不应出现/)
assert.equal(calls.filter(c=>c.url.includes('/runs/intro-old-')).length,0,'Introduction runs never enter business restore/reconnect')
assert.equal(intros.length,4,'History restoration never starts another introduction/action')
assert.equal(cart.length,2)
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['result visible before expression admission','fragment before completion','cards actionable during intro','local interaction and navigation cancellation','failure retains plan and no retry','receipt visible before introduction','exact source keys','explicit expression stop','eligible text result','restored role/run isolation']}))

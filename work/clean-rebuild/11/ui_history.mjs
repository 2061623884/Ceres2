/** Retained App public DOM contract; does not establish real-browser acceptance. */
import assert from 'node:assert/strict';
import path from 'node:path';
import {createRequire} from 'node:module';
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true});
dom.window.HTMLElement.prototype.scrollIntoView=function(){};
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/clean-rebuild/04-purchase/compiled/package.json'));
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),App=compiled('./App.js').default,container=document.getElementById('root');
const state={session_id:'guide-one',task_id:'task-new',state_version:0,session_version:2,entry_context:{page:'home'},available_actions:['send_message'],messages:[],product_cards:[],plan:null,history_reminder:{source_task_id:'old-task',goal:'番茄炒蛋',message:'之前番茄炒蛋还有未完成项，要重新准备吗？'}};
const newPlan={history_source:{task_id:'old-task',plan_id:'old-plan',plan_version:2,goal:'番茄炒蛋'},history_changes:['番茄价格已从6元变为7元。'],plan_kind:'supply_preview',plan_id:'fresh-plan',plan_version:1,mode:'bundle',items:[{sku_id:'tomato',name:'当前番茄',quantity:3,selected:true,added_quantity:0,remaining_quantity:3,unit_price_fen:700,line_total_fen:2100}],total_price_fen:2100,expires_at:null,validation_status:'valid',can_confirm:false,gaps:[{gap_id:'egg',kind:'unavailable',message:'鸡蛋当前缺货。',alternatives:[]}]};
let historyReads=0,turns=[],revisions=[],confirmations=[],cartCount=0,dismissals=[];
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'});
 if(url.endsWith('/cart'))return response({version:1,items:cartCount?[{sku_id:'tomato',name:'当前番茄',quantity:cartCount,unit_price_fen:700,line_total_fen:cartCount*700}]:[],total_price_fen:cartCount*700});
 if(url.includes('/categories'))return response([]);
 if(url.includes('/products'))return response({items:[]});
 if(url.endsWith('/history')){historyReads++;return response({sources:[{task_id:'old-task',goal:'番茄炒蛋',plan:{plan_id:'old-plan',plan_version:2}}]});}
 if(url.endsWith('/history/reminder')){dismissals.push(body);state.history_reminder=null;return response(state);}
 if(url.endsWith('/turns/stream')){turns.push(body);assert.match(body.message,/重新采购历史方案 old-task/);state.task_id='fresh-task';state.session_version++;state.state_version=1;state.plan=structuredClone(newPlan);state.available_actions=['send_message','modify'];state.history_reminder=null;return new Response('data: '+JSON.stringify({type:'turn.completed',payload:{...state,request_id:body.request_id,message:'已按当前条件重算，请核对后另行确认。',messages:[{message_id:'fresh-message',content:'已按当前条件重算，请核对后另行确认。'}]}})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});}
 if(url.endsWith('/plan-revisions')){revisions.push(body);state.state_version++;state.plan.plan_version++;state.plan.plan_kind='partial_purchase';state.plan.can_confirm=true;state.available_actions.push('confirm');return response({...state.plan,state_version:state.state_version,session_version:state.session_version});}
 if(url.endsWith('/confirm')){confirmations.push(body);assert.equal(body.plan_id,'fresh-plan');cartCount+=body.selected_items[0].quantity;state.state_version++;state.plan.items[0].added_quantity=3;state.plan.items[0].remaining_quantity=0;state.plan.can_confirm=false;return response({task_id:state.task_id,state_version:state.state_version,session_version:state.session_version,items_added:[{sku_id:'tomato',quantity:3}]});}
 if(url.endsWith('/status'))return response({...state,runs:[]});
 if(url.includes('/guide/sessions'))return response(state);
 throw new Error('Unexpected fetch '+url);
};
const root=createRoot(container);
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
await act(async()=>root.render(createElement(App)));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));
assert.match(container.textContent,/之前番茄炒蛋还有未完成项/);
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='不再提醒'));
assert.equal(dismissals[0].decision,'decline');assert.equal(turns.length,0);assert.equal(cartCount,0);
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='历史方案'));
assert.equal(historyReads,1);assert.equal(turns.length,0);
await click(container.querySelector('[aria-label="重新采购 old-task"]'));
assert.equal(turns.length,1);assert.equal(cartCount,0);assert.equal(confirmations.length,0);
assert.match(container.textContent,/历史来源：番茄炒蛋/);assert.match(container.textContent,/番茄价格已从6元变为7元/);
assert.ok([...container.querySelectorAll('button')].find(b=>b.textContent==='确认加购').disabled);
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='选择可售部分'));
assert.equal(revisions[0].coverage_intent,'choose_partial');assert.equal(confirmations.length,0);assert.equal(cartCount,0);
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='确认加购'));
assert.equal(confirmations.length,1);assert.equal(cartCount,3);
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['decline reminder without restoration','explicit historical source list and selection','fresh source and current changes visible','supply choice separate from confirmation','exact current three-pack cart count']}));

import {withLegacyNavigationTransport} from '../../next-experience/03/legacy_navigation_transport.mjs';
/** Retained App DOM contract only; not real browser/provider acceptance. */
import assert from 'node:assert/strict';
import path from 'node:path';
import {createRequire} from 'node:module';
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true});
dom.window.HTMLElement.prototype.scrollIntoView=function(){};
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/clean-rebuild/04-purchase/compiled/package.json'));
const React=frontend('react'),{act,createElement}=React,{createRoot}=frontend('react-dom/client');
compiled.extensions['.css']=()=>{};
const App=compiled('./App.js').default,container=document.getElementById('root');
const state={session_id:'guide-one',task_id:'task-one',state_version:1,session_version:1,task_status:'active',entry_context:{page:'home'},available_actions:['send_message','modify','confirm'],messages:[],product_cards:[],plan:{plan_id:'plan-one',plan_version:1,mode:'bundle',items:[{sku_id:'cola',name:'测试可乐',quantity:2,selected:true,added_quantity:0,remaining_quantity:2,unit_price_fen:350,line_total_fen:700}],total_price_fen:700,expires_at:null,validation_status:'valid',can_confirm:true}};
const calls=[];let cartReads=0, cartQuantity=0, staleText=false, confirmations=0;
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'});
 if(url.endsWith('/cart')){cartReads++;return response({version:1,items:cartQuantity?[{sku_id:'cola',name:'测试可乐',quantity:cartQuantity,unit_price_fen:350,line_total_fen:cartQuantity*350}]:[],total_price_fen:cartQuantity*350});}
 if(url.includes('/categories'))return response([]);
 if(url.includes('/products'))return response({items:[]});
 if(url.endsWith('/sessions'))return response(state);
 if(url.endsWith('/status'))return response({...state,runs:[]});
 if(url.includes('/sessions/guide-one?')||url.endsWith('/sessions/guide-one'))return response(state);
 if(url.endsWith('/plan-revisions')){
  calls.push({url,body});state.state_version++;state.plan.plan_version++;state.plan.items[0].selected=body.items[0].selected;state.plan.can_confirm=body.items[0].selected;state.available_actions=['send_message','modify',...(state.plan.can_confirm?['confirm']:[])];
  return response({...state.plan,state_version:state.state_version,session_version:1});
 }
 if(url.endsWith('/turns/stream')){
  calls.push({url,body});assert.equal(body.message,'就按这个加购');if(staleText)return new Response('data: '+JSON.stringify({type:'error',payload:{code:'DISPLAYED_PLAN_STALE',message:'清单已变化，请重新查看并确认'}})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});cartQuantity+=2;state.state_version++;state.plan.items[0].added_quantity=2;state.plan.items[0].remaining_quantity=0;state.plan.can_confirm=false;state.available_actions=['send_message','modify'];
  const receipt={operation_id:'text-op',confirmation_id:'text-confirmed',status:'success',items_added:[{sku_id:'cola',quantity:2}],cart_version:2,errors:[],task_id:'task-one',state_version:state.state_version,session_version:1};
  const result={...state,request_id:body.request_id,message:'已按确认清单加入购物车（模拟业务）。',messages:[{message_id:'text-done',content:'已按确认清单加入购物车（模拟业务）。'}],confirmation_result:receipt};
  return new Response('data: '+JSON.stringify({type:'turn.completed',payload:result})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});
 }
 if(url.endsWith('/confirm')){
  calls.push({url,body,headers:options.headers});confirmations++;
  if(confirmations===1){cartQuantity=2;state.state_version++;state.plan.items[0].added_quantity=2;state.plan.items[0].remaining_quantity=0;state.plan.can_confirm=false;state.available_actions=['send_message','modify'];state.confirmation_result={items_added:[{sku_id:'cola',quantity:2}],cart_version:2};throw new Error('模拟成功响应丢失');}
  return new Response(JSON.stringify({error:{code:'STALE_STATE',message:'清单版本已变化'}}),{status:409,headers:{'Content-Type':'application/json'}});
 }
 throw new Error('Unexpected fetch '+url);
};
globalThis.fetch=withLegacyNavigationTransport(globalThis.fetch);
let root=createRoot(container);
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
await act(async()=>root.render(createElement(App)));
if(sessionStorage.getItem('ceres-chat-visible') !== 'keke'){await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));}else{assert.ok(container.querySelector('[aria-label="角色导航"]'),'Reload restores the explicitly open chat shell');}
if(!container.querySelector('[aria-label="加购 测试可乐"]'))await click(container.querySelector('[aria-label="采购清单 1 件"]'));
const readsBefore=cartReads;
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='确认加购'));
assert.equal(cartQuantity,2,'The simulated server committed despite lost transport response');
assert.match(container.textContent,/模拟成功响应丢失/);
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='确认加购'));
assert.equal(confirmations,2);assert.equal(cartQuantity,2,'Retry must not duplicate committed purchase');
assert.match(container.textContent,/已加购 2 件/,'Authoritative session restores real ledger');
assert.ok(cartReads>readsBefore,'Successful recovery must also refresh authoritative cart, not leave badge stale');
assert.ok(container.querySelector('[aria-label="购物车 2 件"]'),'Recovered cart badge must match exact committed two-item quantity');
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['successful commit then lost response','stale retry does not add twice','receipt ledger recovered','authoritative cart refreshed','badge exactly two items']}));

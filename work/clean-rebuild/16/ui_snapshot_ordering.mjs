/** DOM/client contract only, not browser/layout/provider acceptance. */
import assert from 'node:assert/strict';
import path from 'node:path';
import {createRequire} from 'node:module';
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true});
dom.window.HTMLElement.prototype.scrollIntoView=function(){};
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/clean-rebuild/03/compiled/package.json'));
const React=frontend('react'),{act,createElement}=React,{createRoot}=frontend('react-dom/client');
const App=compiled('./App.js').default,container=document.getElementById('root');
const state={session_id:'guide-one',task_id:'task-one',state_version:0,session_version:1,task_status:'active',entry_context:{page:'home'},available_actions:['send_message'],messages:[],product_cards:[]};
const streams=[],stops=[];
const mode=process.argv[2]??'task';
const card={ref:'candidate-new',sku_id:'new-cola',name:'最新六罐可乐',brand:'真实品牌',image_path:null,packaging:'can',pack_count:6,item_volume_ml:330,total_volume_ml:1980,spec_quantity:1980,spec_unit:'ml',price_fen:1800,price_per_litre_yuan:9.09090909};
let statusRuns=[];
let statusTask={};
let delayedEntry=null, resolveEntry=null, reconnectCalls=0;
let delaySnapshot=false, releaseSnapshot;
const plan=(name, version=1)=>({plan_id:name,plan_version:version,mode:'bundle',items:[{sku_id:name,name,quantity:2,selected:true,added_quantity:0,remaining_quantity:2,unit_price_fen:350,line_total_fen:700}],total_price_fen:700,expires_at:null,validation_status:'valid',can_confirm:true});
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
globalThis.fetch=async(input,options={})=>{
 const url=String(input);
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'});
 if(url.endsWith('/cart'))return response({version:0,items:[],total_price_fen:0});
 if(url.includes('/categories'))return response([]);
 if(url.includes('/products'))return response({items:[]});
 if(url.endsWith('/sessions'))return delayedEntry ?? response(state);
 if(url.includes('/runs/') && url.includes('/stream')){reconnectCalls++;return new Response(new ReadableStream({start(){}}));}
 if(url.includes('/sessions/guide-one/status'))return response({...state,...statusTask,runs:statusRuns});
 if(url.includes('/sessions/guide-one?')||url.endsWith('/sessions/guide-one')){if(delaySnapshot){delaySnapshot=false;const captured=structuredClone(state);return new Promise(resolve=>{releaseSnapshot=()=>resolve(response(captured));});}return response(state);}
 if(url.endsWith('/turns/stop')){stops.push(JSON.parse(options.body));return response({cancelled:true});}
 if(url.endsWith('/tasks/current'))return response({...state,task_id:null,session_version:2,message:'已放弃这个购买任务，购物车里的商品仍保留。'});
 if(url.endsWith('/turns/stream')){
  const body=JSON.parse(options.body);let controller;
  const stream=new ReadableStream({start(c){controller=c;}});
  streams.push({body,controller,signal:options.signal,seq:0});return new Response(stream,{headers:{'Content-Type':'text/event-stream'}});
 }
 throw new Error('Unexpected fetch '+url);
};
let root=createRoot(container);
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
async function enter(text){const input=container.querySelector('input[placeholder="问问可可吧…"]');assert.ok(input);await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,text);input.dispatchEvent(new dom.window.Event('input',{bubbles:true}));});await act(async()=>input.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true})));}
async function event(stream,type,payload){await act(async()=>stream.controller.enqueue(new TextEncoder().encode('data: '+JSON.stringify({protocol_version:1,run_id:stream.body.request_id,sequence:++stream.seq,type,session_id:'guide-one',payload})+'\n\n')));}
await act(async()=>root.render(createElement(App)));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));
await enter('旧采购问题');
await enter('新采购问题');
Object.assign(state,{task_id:'task-old',session_version:2,state_version:5,plan:plan('旧采购商品'),available_actions:['send_message','modify','confirm']});
delaySnapshot=true;
await event(streams[0],'turn.completed',{...state,request_id:streams[0].body.request_id,message:'旧问题已处理',messages:[{message_id:'old-answer',content:'旧问题已处理'}]});
await act(async()=>streams[0].controller.close());
assert.ok(releaseSnapshot,'Old completion GET is deliberately pending');
if(mode==='cards') state.product_cards=[card];
else Object.assign(state,{task_id:'task-new',session_version:3,state_version:1,plan:plan('新采购商品'),available_actions:['send_message','modify','confirm']});
await event(streams[1],'turn.completed',{...state,request_id:streams[1].body.request_id,message:'新问题已处理',messages:[{message_id:'new-answer',content:'新问题已处理'}]});
await act(async()=>streams[1].controller.close());
assert.match(container.textContent,mode==='cards'?/最新六罐可乐/:/新采购商品/,'New state renders before old GET resolves');
await act(async()=>releaseSnapshot());
if(mode==='cards') {
 assert.match(container.textContent,/最新六罐可乐/,'Delayed same-anchor GET must not remove newer comparison cards');
 await enter('选最新候选');
 assert.deepEqual(streams[2].body.displayed_candidate_refs,['candidate-new']);
} else {
 assert.match(container.textContent,/新采购商品/,'Delayed old GET must not replace the newer task plan');
 assert.doesNotMatch(container.textContent,/旧采购商品/,'Old plan cannot regain rendered confirmation authority');
 await enter('就按这个加购');
 assert.equal(streams[2].body.displayed_plan.task_id,'task-new','Confirmation authority remains the actually rendered new task');
 assert.equal(streams[2].body.displayed_plan.session_version,3);
}
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['out-of-order completion GET','new task with lower state version retained','rendered confirmation reference remains newer']}));

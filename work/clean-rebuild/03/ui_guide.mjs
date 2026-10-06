import {withLegacyNavigationTransport} from '../../next-experience/03/legacy_navigation_transport.mjs';
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
compiled.extensions['.css']=()=>{};
const App=compiled('./App.js').default,container=document.getElementById('root');
const state={session_id:'guide-one',task_id:'task-one',state_version:0,session_version:1,task_status:'active',entry_context:{page:'home'},available_actions:['send_message'],messages:[],product_cards:[]};
const streams=[],stops=[];
let statusRuns=[];
let statusTask={};
let delayedEntry=null, resolveEntry=null, reconnectCalls=0;
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
 if(url.includes('/sessions/guide-one?')||url.endsWith('/sessions/guide-one'))return response(state);
 if(url.endsWith('/turns/stop')){stops.push(JSON.parse(options.body));return response({cancelled:true});}
 if(url.endsWith('/tasks/current'))return response({...state,task_id:null,session_version:2,message:'已放弃这个购买任务，购物车里的商品仍保留。'});
 if(url.endsWith('/turns/stream')){
  const body=JSON.parse(options.body);let controller;
  const stream=new ReadableStream({start(c){controller=c;}});
  streams.push({body,controller,signal:options.signal,seq:0});return new Response(stream,{headers:{'Content-Type':'text/event-stream'}});
 }
 throw new Error('Unexpected fetch '+url);
};
globalThis.fetch=withLegacyNavigationTransport(globalThis.fetch);
let root=createRoot(container);
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
async function enter(text){const input=container.querySelector('input[placeholder="问问可可吧…"]');assert.ok(input);await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,text);input.dispatchEvent(new dom.window.Event('input',{bubbles:true}));});await act(async()=>input.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true})));}
async function event(stream,type,payload){await act(async()=>stream.controller.enqueue(new TextEncoder().encode('data: '+JSON.stringify({protocol_version:1,run_id:stream.body.request_id,sequence:++stream.seq,type,session_id:'guide-one',payload})+'\n\n')));}
await act(async()=>root.render(createElement(App)));
if(sessionStorage.getItem('ceres-chat-visible') !== 'keke'){await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));}else{assert.ok(container.querySelector('[aria-label="角色导航"]'),'Reload restores the explicitly open chat shell');}
await enter('查可乐');assert.equal(streams.length,1);
await event(streams[0],'accepted',{request_id:streams[0].body.request_id});
await event(streams[0],'progress',{phase:'retrieve'});
await enter('为什么有彩虹？');assert.equal(streams.length,2,'Must allow another message while shopping runs');
assert.equal(streams[0].signal.aborted,false,'New question must not abort shopping transport');
await event(streams[1],'accepted',{request_id:streams[1].body.request_id});
await event(streams[1],'progress',{phase:'understanding'});
assert.equal(container.querySelectorAll('[data-guide-action-line]').length,1,'Actions replace one gray line');
await event(streams[1],'progress',{phase:'speaking'});
assert.ok(container.querySelector('[aria-label="可可正在输入"]'));
await event(streams[1],'answer.delta',{message_id:'short-one',delta:'彩虹来自折射 🌈',replace:true,answer_kind:'general_explanation'});
await event(streams[1],'answer.delta',{message_id:'short-two',delta:'不同颜色有不同角度。',replace:true});
assert.match(container.textContent,/通用解释/,'General text must be presented separately from merchant facts');assert.match(container.textContent,/彩虹来自折射/);assert.match(container.textContent,/不同颜色有不同角度/);
await event(streams[1],'turn.completed',{...state,request_id:streams[1].body.request_id,message:'彩虹来自折射 🌈\n\n不同颜色有不同角度。',messages:[{message_id:'short-one',content:'彩虹来自折射 🌈'},{message_id:'short-two',content:'不同颜色有不同角度。'}],assistant_message_id:'short-one'});
await act(async()=>streams[1].controller.close());
await click(container.querySelector('[aria-label="停止本次处理"]'));assert.equal(stops[0].request_id,streams[0].body.request_id);
await act(async()=>root.unmount());assert.equal(streams[0].signal.aborted,true,'Leaving page closes only transport');
assert.equal(stops.length,1,'Unmount must not send another stop');
state.task_id=process.env.GUIDE_UI_CASE==='task-abandoned'?'task-one':null;
statusTask={task_id:process.env.GUIDE_UI_CASE==='task-abandoned'?null:'task-restored',state_version:1,session_version:2,task_status:'active'};
statusRuns=[{run_id:'interrupted-old',request_id:'interrupted-old',status:'interrupted',input:{message:'中断前我问的问题'},result:{code:'RUN_INTERRUPTED',message:'服务重启中断了这次处理'}} ,{run_id:'completed-while-opening',request_id:'completed-while-opening',status:'completed',input:{message:'刚才的查询'},result:{...state,message:'刚刚完成的持久结果',messages:[{message_id:'durable-one',content:'刚刚完成的持久结果'}]}}];
root=createRoot(container);
await act(async()=>root.render(createElement(App)));
if(sessionStorage.getItem('ceres-chat-visible') !== 'keke'){await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));}else{assert.ok(container.querySelector('[aria-label="角色导航"]'),'Reload restores the explicitly open chat shell');}
if(!['late-init','interrupted'].includes(process.env.GUIDE_UI_CASE)) assert.match(container.textContent,/刚刚完成的持久结果/,'Reentry must reconcile a run completed after the initial history snapshot');
assert.equal(container.querySelector('[aria-label="放弃购买任务"]').disabled,process.env.GUIDE_UI_CASE==='task-abandoned','Controls must use newer authoritative task snapshot even when every run is terminal');
if(process.env.GUIDE_UI_CASE==='interrupted') { assert.match(container.textContent,/中断前我问的问题/); assert.match(container.textContent,/服务重启中断了这次处理/); }
await act(async()=>root.unmount());
delayedEntry=new Promise(resolve=>{resolveEntry=resolve});
statusRuns=[{run_id:'late-run',request_id:'late-run',status:'running',input:{message:'待恢复'}}];
root=createRoot(container);
await act(async()=>root.render(createElement(App)));
if(sessionStorage.getItem('ceres-chat-visible') !== 'keke'){await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));}else{assert.ok(container.querySelector('[aria-label="角色导航"]'),'Reload restores the explicitly open chat shell');}
await act(async()=>root.unmount());
await act(async()=>resolveEntry(response(state)));
assert.equal(reconnectCalls,0,'Delayed initialization must not start a transport after panel unmount');
dom.window.close();console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['concurrent input','no automatic cancellation','single replacing action line','dots then multi-message stream','explicit run stop','unmount transport only']}));

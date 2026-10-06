import {withLegacyNavigationTransport} from '../../next-experience/03/legacy_navigation_transport.mjs';
/** Actual App: completion order and reconnect may not lose current cards. */
import assert from 'node:assert/strict';
import path from 'node:path';
import {createRequire} from 'node:module';
const mode=process.argv[2]??'error',cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true});dom.window.HTMLElement.prototype.scrollIntoView=function(){};
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/clean-rebuild/04-purchase/compiled/package.json'));
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),App=compiled('./App.js').default,container=document.getElementById('root');
const card={ref:'candidate-new',sku_id:'new-cola',name:'最新六罐可乐',brand:'真实品牌',image_path:null,packaging:'can',pack_count:6,item_volume_ml:330,total_volume_ml:1980,spec_quantity:1980,spec_unit:'ml',price_fen:1800,price_per_litre_yuan:9.09090909};
const state={session_id:'guide-one',task_id:'task-one',state_version:1,session_version:1,task_status:'active',entry_context:{page:'home'},available_actions:['send_message'],messages:[],product_cards:[],plan:null};
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
const event=(type,payload)=>new Response('data: '+JSON.stringify({type,payload})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});
const done=(id,cards,text)=>({...state,request_id:id,message:text,messages:[{message_id:'reply-'+id,content:text}],product_cards:cards});
let releaseOld;const calls=[];
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'});
 if(url.endsWith('/cart'))return response({version:1,items:[],total_price_fen:0});
 if(url.includes('/categories'))return response([]);
 if(url.includes('/products'))return response({items:[]});
 if(url.endsWith('/sessions'))return response(state);
 if(url.endsWith('/status'))return response({...state,runs:mode==='reconnect'?[{run_id:'restored-run',request_id:'restored-request',status:'running',input:{message:'继续比较'}}]:[]});
 if(url.includes('/sessions/guide-one?')||url.endsWith('/sessions/guide-one'))return response(state);
 if(url.includes('/runs/restored-run/stream'))return new Promise(resolve=>{releaseOld=()=>{state.product_cards=[card];resolve(event('turn.completed',done('restored-request',[card],'恢复完成，展示候选。')));};});
 if(url.endsWith('/turns/stream')) {
   calls.push(body);
   if(body.message==='旧请求A')return new Promise(resolve=>{releaseOld=()=>resolve(mode==='error'?event('error',{code:'PI_RUNTIME_ERROR',message:'旧请求失败'}):event('turn.completed',done(body.request_id,[],'这是旧请求的普通回答。')));});
   if(body.message==='新比较B') {state.product_cards=[card];return event('turn.completed',done(body.request_id,[card],'最新比较候选。'));}
   return event('turn.completed',done(body.request_id,[card],'仍然展示最新候选。'));
 }
 throw Error('Unexpected fetch '+url);
};
globalThis.fetch=withLegacyNavigationTransport(globalThis.fetch);
let root=createRoot(container);
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
async function send(text){const input=container.querySelector('input[placeholder="问问可可吧…"]');assert.ok(input);await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,text);input.dispatchEvent(new dom.window.Event('input',{bubbles:true}));});await act(async()=>input.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true})));}
await act(async()=>root.render(createElement(App)));
if(sessionStorage.getItem('ceres-chat-visible') !== 'keke'){await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));}else{assert.ok(container.querySelector('[aria-label="角色导航"]'),'Reload restores the explicitly open chat shell');}
if(mode!=='reconnect') {
 await send('旧请求A');assert.equal(typeof releaseOld,'function');
 await send('新比较B');assert.ok(container.querySelector('[aria-label="商品候选比较"]'));
}
assert.equal(typeof releaseOld,'function');
await act(async()=>{releaseOld();await new Promise(resolve=>setTimeout(resolve,20));});
assert.ok(container.querySelector('[aria-label="商品候选比较"]'),mode==='reconnect'?'Reconnected terminal must render its current cards':`Late older ${mode} must preserve newer comparison cards`);
assert.match(container.textContent,/最新六罐可乐/);
await send('选最新候选');
assert.deepEqual(calls.at(-1).displayed_candidate_refs,['candidate-new'],'Only actually rendered latest candidates become selection evidence');
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'DOM-only',mode,checks:['current cards survive completion order or reconnect','current displayed refs remain selectable']}));

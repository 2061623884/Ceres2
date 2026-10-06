import {withLegacyNavigationTransport} from '../03/legacy_navigation_transport.mjs';
/** Actual React inputs/API adapters under controlled DOM; not browser/live-model acceptance. */
import assert from 'node:assert/strict';
import path from 'node:path';
import {createRequire} from 'node:module';
const cwd=process.cwd();
const support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM}=support('jsdom');
const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,
 localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true});
dom.window.HTMLElement.prototype.scrollIntoView=function(){};
const frontend=createRequire(path.join(cwd,'frontend/package.json'));
const compiled=createRequire(path.join(cwd,'work/next-experience/01/compiled/package.json'));
const {act,createElement}=frontend('react');
const {createRoot}=frontend('react-dom/client');
compiled.extensions['.css']=()=>{};
const App=compiled('./App.js').default;
const container=document.getElementById('root');
const state={session_id:'guide-policy',task_id:'shopping-task',state_version:0,session_version:1,task_status:'active',
 entry_context:{page:'home'},available_actions:['send_message'],messages:[],product_cards:[]};
const mercury={session_id:'mercury-policy',order_id:null,selection_version:0,status:'ready',messages:[]};
const question={question_id:'shopping-question',session_id:'guide-policy',task_id:'shopping-task',state_version:0,session_version:1,kind:'category',question:'想看哪类零食？',status:'active',selected_option_ids:[],options:[{option_id:'chips',label:'薯片',value:'potato_chips'},{option_id:'crackers',label:'饼干',value:'soda_crackers'}]};
const policy='签收后 7 天内，可退货商品仅整行模拟退货；签收时间未知不能确认资格。来源：Ceres 模拟售后规则 P-RET-01（版本 2026-10-06）。具体订单资格尚未核实；未提交任何申请。';
const posts=[];
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
globalThis.fetch=async(input,options={})=>{
 const url=String(input), method=options.method??'GET';
 if(method!=='GET') posts.push({url,method,body:options.body?JSON.parse(options.body):null});
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'});
 if(url.endsWith('/cart'))return response({version:0,items:[],total_price_fen:0});
 if(url.includes('/categories'))return response([]);
 if(url.includes('/products'))return response({items:[]});
 if(url.endsWith('/mercury/orders'))return response({orders:[],simulated:true});
 if(url.endsWith('/mercury/sessions')||url.endsWith('/mercury/sessions/mercury-policy'))return response(mercury);
 if(url.endsWith('/human-ticket'))return response(null);
 if(url.endsWith('/aftersales'))return response({proposal:null,receipts:[],simulated:true});
 if(url.endsWith('/mercury/sessions/mercury-policy/turns/stream')){
  return new Response('event: answer.delta\ndata: '+JSON.stringify({text:policy})+'\n\nevent: turn.completed\ndata: '+JSON.stringify({session_id:mercury.session_id,final_text:policy,status:'completed'})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});
 }
 if(url.endsWith('/sessions'))return response(state);
 if(url.endsWith('/guide-policy/status'))return response({...state,runs:[]});
 if(url.endsWith('/guide-policy')||url.includes('/guide-policy?'))return response(state);
 if(url.endsWith('/guide-policy/turns/stream')){
  const body=JSON.parse(options.body);
  const replies=[{message_id:question.question_id,content:question.question},{message_id:'policy-answer',content:policy}];
  Object.assign(state,{task_id:question.task_id,active_question:question,question_history:[question],messages:replies.map((message,index)=>({...message,session_id:state.session_id,task_id:question.task_id,role:'assistant',kind:index===0?'question':'text',sequence:index+1,request_id:body.request_id}))});
  const payload={...state,request_id:body.request_id,assistant_message_id:question.question_id,message:question.question,messages:replies,products:[],action_results:[]};
  const event={protocol_version:1,run_id:body.request_id,sequence:1,type:'turn.completed',session_id:state.session_id,payload};
  return new Response('data: '+JSON.stringify(event)+'\n\n',{headers:{'Content-Type':'text/event-stream'}});
 }
 throw new Error('Unexpected fetch '+method+' '+url);
};
async function click(button){assert.ok(button);await act(async()=>button.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
async function enter(placeholder){
 const input=container.querySelector(`input[placeholder="${placeholder}"]`);assert.ok(input);assert.equal(input.disabled,false);
 await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,'来点零食，也说明退货政策');input.dispatchEvent(new dom.window.Event('input',{bubbles:true}));});
 await act(async()=>input.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true})));
}
globalThis.fetch=withLegacyNavigationTransport(globalThis.fetch);
let root=createRoot(container);
await act(async()=>root.render(createElement(App)));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));
await enter('问问可可吧…');
assert.equal(posts.filter(p=>p.url.endsWith('/guide-policy/turns/stream')).length,1);
assert.match(container.textContent,/P-RET-01/);assert.match(container.textContent,/具体订单资格尚未核实/);
assert.ok([...container.querySelectorAll('button')].some(b=>b.textContent==='薯片'&&!b.disabled));
assert.ok([...container.querySelectorAll('button')].some(b=>b.textContent==='饼干'&&!b.disabled));
await act(async()=>root.unmount());
root=createRoot(container);await act(async()=>root.render(createElement(App)));
assert.match(container.textContent,/P-RET-01/);assert.match(container.textContent,/未提交任何申请/);
assert.ok([...container.querySelectorAll('button')].some(b=>b.textContent==='薯片'&&!b.disabled),'Refresh retains the same actionable question alongside policy');
assert.equal(posts.filter(p=>p.method==='PUT'||/\/(confirm|proposals|checkout|tasks\/current|human-ticket)$/.test(p.url)).length,0);
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'controlled DOM only',checks:['compound result shows question and policy','policy conditions and source intact','refresh retains both','no business writes']}));

/** Actual retained App under jsdom; explicitly not a real-browser acceptance. */
import assert from 'node:assert/strict';
import path from 'node:path';
import {createRequire} from 'node:module';
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true});
dom.window.HTMLElement.prototype.scrollIntoView=function(){};
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/clean-rebuild/04-purchase/compiled/package.json'));
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),App=compiled('./App.js').default;
const container=document.getElementById('root'),calls=[];
const card={ref:'candidate-shown',sku_id:'six-cola',name:'六罐真实可乐',brand:'真实品牌',image_path:null,packaging:'can',pack_count:6,item_volume_ml:330,total_volume_ml:1980,spec_quantity:1980,spec_unit:'ml',price_fen:1800,price_per_litre_yuan:9.09090909};
const unknown={...card,ref:'candidate-unknown',sku_id:'unknown-cola',name:'未知包装可乐',brand:null,packaging:null,pack_count:null,item_volume_ml:null,price_fen:null,price_per_litre_yuan:null};
const boxed={...card,ref:'candidate-box',sku_id:'boxed-snack',name:'盒装点心',packaging:'box',pack_count:1,item_volume_ml:null,total_volume_ml:null,spec_quantity:200,spec_unit:'g',price_per_litre_yuan:null};
const state={session_id:'guide-one',task_id:'task-one',state_version:1,session_version:1,task_status:'active',entry_context:{page:'home'},available_actions:['send_message'],messages:[{message_id:'comparison-message',role:'assistant',content:'比较候选，选择后准备清单。'}],product_cards:[card,unknown,boxed],plan:null};
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
let mode='select';
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'});
 if(url.endsWith('/cart'))return response({version:1,items:[],total_price_fen:0});
 if(url.includes('/categories'))return response([]);
 if(url.includes('/products'))return response({items:[]});
 if(url.endsWith('/sessions'))return response(state);
 if(url.endsWith('/status'))return response({...state,runs:[]});
 if(url.includes('/sessions/guide-one?')||url.endsWith('/sessions/guide-one'))return response(state);
 if(url.endsWith('/turns/stream')){
   calls.push({url,body});
   if(mode==='error') {
     state.product_cards=[];
     return new Response('data: '+JSON.stringify({type:'error',payload:{code:'PI_RUNTIME_ERROR',message:'查询失败，请重试'}})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});
   }
   state.product_cards=[];
   if(mode==='select') {
     state.state_version++;
     state.plan={plan_id:'selected-plan',plan_version:1,mode:'bundle',items:[{sku_id:'six-cola',name:card.name,quantity:1,selected:true,added_quantity:0,remaining_quantity:1,unit_price_fen:1800,line_total_fen:1800}],total_price_fen:1800,expires_at:null,validation_status:'valid',can_confirm:true};
     state.available_actions=['send_message','modify','confirm'];
   }
   const result={...state,request_id:body.request_id,message:mode==='select'?'已生成采购清单，请核对后确认。':'没有匹配商品。',messages:[{message_id:'new-result',content:mode==='select'?'已生成采购清单，请核对后确认。':'没有匹配商品。'}]};
   return new Response('data: '+JSON.stringify({type:'turn.completed',payload:result})+'\n\n',{headers:{'Content-Type':'text/event-stream'}});
 }
 if(url.endsWith('/confirm')||url.includes('/items/'))throw Error('Comparison selection must never auto-confirm');
 throw Error('Unexpected fetch '+url);
};
let root;
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
async function open(){root=createRoot(container);await act(async()=>root.render(createElement(App)));await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));}
async function send(text){const input=container.querySelector('input[placeholder="问问可可吧…"]');assert.ok(input);await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,text);input.dispatchEvent(new dom.window.Event('input',{bubbles:true}));});await act(async()=>input.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true})));}
await open();
assert.match(container.textContent,/品牌：真实品牌/);
assert.match(container.textContent,/1980ml/);
assert.match(container.textContent,/9.09 元\/升/);
assert.match(container.textContent,/包装：未知/);
assert.match(container.textContent,/报价未知/);
assert.match(container.textContent,/包装：盒/,'Known non-beverage packaging must not be mislabeled unknown');
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='选这款，生成清单'));
assert.match(calls.at(-1).body.message,/candidate-shown/);
assert.deepEqual(calls.at(-1).body.displayed_candidate_refs,['candidate-shown','candidate-unknown','candidate-box']);
assert.match(container.textContent,/已生成采购清单/);
assert.equal(calls.length,1,'Selection sends one turn and never cart or confirmation');
await act(async()=>root.unmount());
for (const kind of ['empty','error']) {
 mode=kind;state.plan=null;state.product_cards=[card,unknown];state.available_actions=['send_message'];
 await open();assert.ok(container.querySelector('[aria-label="商品候选比较"]'));
 await send(kind==='empty'?'比较不存在的品牌':'重新比较');
 assert.equal(container.querySelector('[aria-label="商品候选比较"]'),null,'Old cards must clear on empty/error');
 await send('再试一下');
 assert.deepEqual(calls.at(-1).body.displayed_candidate_refs,[],'Retired cards must not remain selection authority');
 await act(async()=>root.unmount());
}
dom.window.close();console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['source-backed fields and unknown values','restored displayed refs posted with selection','no auto-confirm','empty/error clear old cards and refs']}));

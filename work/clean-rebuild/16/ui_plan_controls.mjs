/** Isolated retained App DOM, not real browser or provider acceptance. */
import assert from 'node:assert/strict';
import path from 'node:path';
import {createRequire} from 'node:module';
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,FormData:dom.window.FormData,IS_REACT_ACT_ENVIRONMENT:true});
dom.window.HTMLElement.prototype.scrollIntoView=function(){};
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/clean-rebuild/04-purchase/compiled/package.json'));
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),App=compiled('./App.js').default,container=document.getElementById('root');
const mode=process.argv[2]??'quantity';
const state={session_id:'guide-one',task_id:'task-one',state_version:1,session_version:1,task_status:'active',entry_context:{page:'home'},available_actions:['send_message','modify','confirm'],messages:[],product_cards:[],plan:{plan_id:'plan-one',plan_version:1,mode:'bundle',dish:{dish_id:'tomato-egg',name:'番茄炒蛋',base_people:2,people:2,people_source:'default'},items:[{sku_id:'tomato',ingredient_id:'tomato',available_specs:[{sku_id:'tomato',name:'番茄500克',spec_quantity:500,spec_unit:'g'},{sku_id:'tomato-1000',name:'番茄1千克',spec_quantity:1000,spec_unit:'g'}],name:'番茄500克',quantity:1,selected:true,role:'required',added_quantity:0,remaining_quantity:1,unit_price_fen:600,line_total_fen:600,spec_quantity:500,spec_unit:'g',requirement:{quantity:300,unit:'g'}},{sku_id:'salt',ingredient_id:'salt',name:'盐500克',quantity:1,selected:false,role:'pantry',added_quantity:0,remaining_quantity:1,unit_price_fen:300,line_total_fen:300,spec_quantity:500,spec_unit:'g',requirement:{quantity:null,unit:null}}],total_price_fen:600,expires_at:null,validation_status:'valid',can_confirm:true}};
state.plan.items.push({sku_id:'eggs',name:'鸡蛋六枚装',ingredient_id:'egg',quantity:1,selected:true,role:'required',added_quantity:0,remaining_quantity:1,unit_price_fen:800,line_total_fen:800,spec_quantity:6,spec_unit:'pc',requirement:{quantity:3,unit:'pc'}});
if(mode==='budget'){state.plan.budget_quote={budget_fen:1000,total_fen:1400};state.plan.total_price_fen=1400;state.plan.can_confirm=false;state.available_actions=['send_message','modify'];}
let revisions=[];
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'});
 if(url.endsWith('/cart'))return response({version:1,items:[],total_price_fen:0});
 if(url.includes('/categories'))return response([]);
 if(url.includes('/products'))return response({items:[]});
 if(url.endsWith('/plan-revisions')){revisions.push(body);state.state_version++;state.plan.plan_version++;if(body.coverage_intent==='accept_quote'){delete state.plan.budget_quote;state.plan.can_confirm=true;}else{for(const item of state.plan.items){const change=body.items.find(row=>row.sku_id===item.sku_id);item.quantity=change.quantity;item.remaining_quantity=change.quantity;}}return response({...state.plan,state_version:state.state_version,session_version:1});}
 if(url.endsWith('/status'))return response({...state,runs:[]});
 if(url.includes('/guide/sessions'))return response(state);
 throw new Error('Unexpected fetch '+url);
};
const root=createRoot(container);
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
await act(async()=>root.render(createElement(App)));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));
if(mode==='budget') {
 assert.match(container.textContent,/当前预算.*10.00/);
 const accept=[...container.querySelectorAll('button')].find(b=>b.textContent==='接受报价 14.00 元，更新预算');
 assert.ok(accept,'Overbudget factual plan exposes explicit budget negotiation');
 assert.equal(container.querySelector('[aria-label="加购 鸡蛋六枚装"]').disabled,true);
 await click(accept);
 assert.equal(revisions.length,1);assert.equal(revisions[0].coverage_intent,'accept_quote');
 assert.equal(revisions[0].base_plan_version,1);
 assert.equal([...container.querySelectorAll('button')].some(b=>b.textContent.includes('接受报价')),false,'Accepted quote is removed from the returned revision');
 assert.equal(container.querySelector('[aria-label="加购 鸡蛋六枚装"]').disabled,false,'Separate confirmation becomes available');
 assert.match(container.textContent,/已加购 0 件/,'Accepting quote does not add to cart');
} else {
 const input=container.querySelector('[aria-label="购买数量 鸡蛋六枚装"]');assert.ok(input,'Dish sale-package quantity is user editable');
 await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,'2');input.dispatchEvent(new dom.window.Event('input',{bubbles:true}));});
 await click(container.querySelector('[aria-label="更新数量 鸡蛋六枚装"]'));
 assert.equal(revisions.length,1);assert.equal(revisions[0].coverage_intent,'selection_only');
 assert.deepEqual(revisions[0].items.map(row=>[row.sku_id,row.quantity]),[['tomato',1],['salt',1],['eggs',2]]);
 assert.match(container.textContent,/番茄炒蛋/,'Dish identity survives quantity-only revision');
 assert.equal(container.querySelector('[aria-label="购买数量 番茄500克"]').value,'1');
 assert.match(container.textContent,/本次选购 2 件/);
}
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'DOM-only',mode}));

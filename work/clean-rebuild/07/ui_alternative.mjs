/** Isolated retained App DOM, not real browser or provider acceptance. */
import assert from 'node:assert/strict';
import path from 'node:path';
import {createRequire} from 'node:module';
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,sessionStorage:dom.window.sessionStorage,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true});
dom.window.HTMLElement.prototype.scrollIntoView=function(){};
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/clean-rebuild/04-purchase/compiled/package.json'));
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),App=compiled('./App.js').default,container=document.getElementById('root');
const state={session_id:'guide-one',task_id:'task-one',state_version:1,session_version:1,task_status:'active',entry_context:{page:'home'},available_actions:['send_message','modify','confirm'],messages:[],product_cards:[],plan:{plan_id:'plan-one',plan_version:1,mode:'bundle',dish:{dish_id:'tomato-egg',name:'番茄炒蛋',base_people:2,people:2,people_source:'default'},items:[{sku_id:'tomato',ingredient_id:'tomato',available_specs:[{sku_id:'tomato',name:'番茄500克',spec_quantity:500,spec_unit:'g'},{sku_id:'tomato-1000',name:'番茄1千克',spec_quantity:1000,spec_unit:'g'}],name:'番茄500克',quantity:1,selected:true,role:'required',added_quantity:0,remaining_quantity:1,unit_price_fen:600,line_total_fen:600,spec_quantity:500,spec_unit:'g',requirement:{quantity:300,unit:'g'}},{sku_id:'salt',ingredient_id:'salt',name:'盐500克',quantity:1,selected:false,role:'pantry',added_quantity:0,remaining_quantity:1,unit_price_fen:300,line_total_fen:300,spec_quantity:500,spec_unit:'g',requirement:{quantity:null,unit:null}}],total_price_fen:600,expires_at:null,validation_status:'valid',can_confirm:true}};

state.plan.plan_kind='supply_preview';state.plan.can_confirm=false;
state.available_actions=['send_message','modify'];
state.plan.gaps=[{gap_id:'supply:egg',kind:'unavailable',ingredient_id:'egg',message:'鸡蛋当前无货，需要明确选择部分采购。',alternatives:[{items:[{sku_id:'egg-10',quantity:1}],total_price_fen:1300,leftover_quantity:7}]}];
let revisions=[],confirmations=[];
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'});
 if(url.endsWith('/cart'))return response({version:1,items:[],total_price_fen:0});
 if(url.includes('/categories'))return response([]);
 if(url.includes('/products'))return response({items:[]});
 if(url.endsWith('/plan-revisions')){revisions.push(body);state.state_version++;state.plan.plan_version++;state.plan.plan_kind='partial_purchase';state.plan.can_confirm=true;state.available_actions.push('confirm');return response({...state.plan,state_version:state.state_version,session_version:1});}
 if(url.endsWith('/confirm')){confirmations.push(body);return response({state_version:state.state_version,session_version:1});}
 if(url.endsWith('/status'))return response({...state,runs:[]});
 if(url.includes('/guide/sessions'))return response(state);
 throw new Error('Unexpected fetch '+url);
};
const root=createRoot(container);
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
await act(async()=>root.render(createElement(App)));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));
if(!container.querySelector('[aria-label="加购 番茄500克"]'))await click(container.querySelector('[aria-label="采购清单 2 件"]'));
assert.match(container.textContent,/供给预览/);
assert.match(container.textContent,/鸡蛋当前无货/);
assert.ok([...container.querySelectorAll('button')].find(b=>b.textContent==='确认加购').disabled);
await click(container.querySelector('[aria-label="选择替代 supply:egg 0"]'));
assert.equal(revisions.length,1);assert.equal(revisions[0].coverage_intent,'choose_alternative');assert.equal(revisions[0].gap_id,'supply:egg');assert.equal(revisions[0].alternative_index,0);assert.deepEqual(revisions[0].items,[]);
assert.equal(confirmations.length,0,'Choosing partial supply never confirms the cart');
assert.match(container.textContent,/部分采购清单/);
assert.ok(![...container.querySelectorAll('button')].find(b=>b.textContent==='确认加购').disabled);
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='确认加购'));
assert.equal(confirmations.length,1);
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['priced remainder alternative','explicit alternative selection','independent cart confirmation']}));

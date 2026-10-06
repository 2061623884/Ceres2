import {withLegacyNavigationTransport} from '../../next-experience/03/legacy_navigation_transport.mjs';
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
let revisions=[];
const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
globalThis.fetch=async(input,options={})=>{
 const url=String(input),body=options.body?JSON.parse(options.body):null;
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store',delivery_zone_id:'zone'});
 if(url.endsWith('/cart'))return response({version:1,items:[],total_price_fen:0});
 if(url.includes('/categories'))return response([]);
 if(url.includes('/products'))return response({items:[]});
 if(url.endsWith('/plan-revisions')){revisions.push(body);state.state_version++;state.plan.plan_version++;if(body.people){state.plan.dish.people=body.people;state.plan.dish.people_source='explicit';}return response({...state.plan,state_version:state.state_version,session_version:1});}
 if(url.endsWith('/status'))return response({...state,runs:[]});
 if(url.includes('/guide/sessions'))return response(state);
 throw new Error('Unexpected fetch '+url);
};
globalThis.fetch=withLegacyNavigationTransport(globalThis.fetch);
const root=createRoot(container);
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})));}
await act(async()=>root.render(createElement(App)));
if(sessionStorage.getItem('ceres-chat-visible') !== 'keke'){await click([...container.querySelectorAll('button')].find(b=>b.textContent==='商品'));
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='问问可可'));}else{assert.ok(container.querySelector('[aria-label="角色导航"]'),'Reload restores the explicitly open chat shell');}
if(!container.querySelector('[aria-label="加购 番茄500克"]'))await click(container.querySelector('[aria-label="采购清单 2 件"]'));
assert.match(container.textContent,/默认基准 2 人用量（非指定人数）/);
assert.match(container.textContent,/需求 300g · 采购覆盖 500g · 包装余量 200g/);
assert.match(container.textContent,/用量未知；未选不代表家中已有/);
const input=container.querySelector('[aria-label="单菜人数"]');assert.ok(input,'Public sheet must let user revise people');
await act(async()=>{Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(input,'3');input.dispatchEvent(new dom.window.Event('input',{bubbles:true}));input.dispatchEvent(new dom.window.Event('change',{bubbles:true}));});
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='更新人数'));
assert.equal(revisions.length,1);assert.equal(revisions[0].people,3);assert.equal(revisions[0].coverage_intent,'dish_update');assert.match(container.textContent,/用户指定 3 人/);
const specification=container.querySelector('[aria-label="规格 番茄500克"]');assert.ok(specification,'Sheet offers compatible SKU selection');
await act(async()=>{specification.value='tomato-1000';specification.dispatchEvent(new dom.window.Event('change',{bubbles:true}));});
assert.equal(revisions.length,2);assert.deepEqual(revisions[1].selections,{tomato:'tomato-1000'});
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['baseline provenance','demand/package/leftover','pantry unknown','people revision request']}));

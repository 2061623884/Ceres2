/** Actual React component and API adapter; controlled DOM, not a browser. */
import assert from 'node:assert/strict';
import path from 'node:path';
import { createRequire } from 'node:module';
const cwd=process.cwd();
const support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM}=support('jsdom');
const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,localStorage:dom.window.localStorage,
 HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true});
const frontend=createRequire(path.join(cwd,'frontend/package.json'));
const compiled=createRequire(path.join(cwd,'work/clean-rebuild/14/compiled/package.json'));
const {act,createElement}=frontend('react');const {createRoot}=frontend('react-dom/client');
const {AfterSalesPanel}=compiled('./AfterSalesPanel.js');
let posts=[],state={proposal:null,receipts:[]}, delay;
const preview={proposal_id:'p-one',revision:1,order_id:'normal',kind:'refund',amount_fen:1234,reason:'不需要',policy_id:'P-REF-01',policy:'未发货整单模拟退款',items:[{item_id:'sku',name:'面粉',quantity:2,amount_fen:1234}]};
const receipt={...preview,receipt_id:'r-one',application_id:'a-one',status:'requested',message:'模拟申请已提交，尚未审批或退款到账'};
function response(data){return new Response(JSON.stringify(data),{headers:{'Content-Type':'application/json'}})}
globalThis.fetch=async(input,options)=>{
 const url=String(input);
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store-demo-01'});
 if(url.endsWith('/aftersales'))return response(state);
 if(url.includes('/orders/'))return response({items:[{sku_id:'sku',name:'面粉',quantity:2}]});
 if(url.endsWith('/proposals')){posts.push(JSON.parse(options.body));state={...state,proposal:preview};return response(preview)}
 if(url.endsWith('/confirm')){posts.push(JSON.parse(options.body));if(delay)return delay;state={proposal:null,receipts:[receipt]};return response(receipt)}
 throw new Error('unexpected fetch '+url);
};
const container=document.getElementById('root');let root=createRoot(container);
const props={caseId:'case',orderId:'normal',selectionVersion:1,refreshKey:0,disabled:false};
async function render(overrides={}){await act(async()=>root.render(createElement(AfterSalesPanel,{...props,...overrides})))}
async function click(text){const button=[...container.querySelectorAll('button')].find(b=>b.textContent===text);assert.ok(button);await act(async()=>button.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
async function input(text){const el=container.querySelector('[aria-label="售后原因"]');await act(async()=>{
 Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype,'value').set.call(el,text);
 el.dispatchEvent(new dom.window.Event('input',{bubbles:true}));
})}
await render();assert.equal(posts.length,0);
await input('不需要');await click('查看申请提案');
assert.equal(posts.length,1);assert.equal(posts[0].selection_version,1);
assert.match(container.textContent,/12\.34/);assert.match(container.textContent,/面粉 × 2/);
assert.match(container.textContent,/P-REF-01/);assert.equal(posts.filter(p=>p.confirmed).length,0);
await click('确认提交此模拟申请');assert.equal(posts[1].confirmed,true);assert.equal(posts[1].idempotency_key,'p-one');
assert.ok(container.querySelector('[data-receipt-id="r-one"]'));assert.match(container.textContent,/尚未审批或退款到账/);
await act(async()=>root.unmount());root=createRoot(container);await render();
assert.ok(container.querySelector('[data-receipt-id="r-one"]'),'receipt restored');
// Editing proposed terms hides the old confirmation until a new proposal is shown.
state={proposal:preview,receipts:[]};await render({refreshKey:1});
await input('改变原因');assert.equal(container.querySelector('[data-proposal-id]'),null);
// A result from the prior order must never overwrite the newly selected order.
state={proposal:preview,receipts:[]};await render({refreshKey:2});
let resolve;delay=new Promise(r=>resolve=r);
await click('确认提交此模拟申请');state={proposal:null,receipts:[]};
await render({orderId:'other',selectionVersion:2,refreshKey:3});
await act(async()=>resolve(response(receipt)));assert.equal(container.querySelector('[data-receipt-id]'),null);
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['concrete preview','no first-intent submission','explicit confirmation exact key','receipt restore','changed terms hide confirmation','late old-order response fenced']}));

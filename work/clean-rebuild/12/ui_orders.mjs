/** DOM-only component/client evidence; no browser/layout or live HTTP claim. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const cwd = process.cwd();
const support = createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'));
const {JSDOM} = support('jsdom');
const dom = new JSDOM('<div id="root"></div>',{url:'http://localhost/'});
Object.assign(globalThis,{window:dom.window,document:dom.window.document,localStorage:dom.window.localStorage,
  HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true});
const frontend = createRequire(path.join(cwd,'frontend/package.json'));
const compiled = createRequire(path.join(cwd,'work/clean-rebuild/12/compiled/package.json'));
const React = frontend('react');
const {act,createElement} = React;
const {createRoot} = frontend('react-dom/client');
const {SimulatedOrdersScreen,SimulatedCheckout} = compiled('./SimulatedOrders.js');
const order = JSON.parse(fs.readFileSync(path.join(cwd,'work/clean-rebuild/12/order-projection.json'),'utf8'));
let confirmations = 0;
const contacted = [];
const preview = {...order,preview_id:'checkout-dom',cart_version:2};
function response(data){return new Response(JSON.stringify(data),{headers:{'Content-Type':'application/json'}})}
globalThis.fetch = async (input, options) => {
  const url=String(input);
  if(url.endsWith('/bootstrap'))return response({owner_id:'owner-old',store_id:'store-demo-01'});
  if(url.endsWith('/orders'))return response({items:[order]});
  if(url.endsWith('/orders/'+order.order_id))return response(order);
  if(url.endsWith('/cart'))return response({version:2,items:order.items,total_price_fen:order.total_fen});
  if(url.endsWith('/checkout/preview'))return response(preview);
  if(url.endsWith('/checkout/confirm')){
    const body=JSON.parse(options.body);
    assert.equal(body.confirmed,true);assert.equal(body.preview_id,preview.preview_id);
    assert.ok(body.idempotency_key);confirmations++;
    return response({receipt_id:'receipt-dom',order,cart_version:3});
  }
  throw new Error('Unexpected fetch '+url);
};
const container=document.getElementById('root');
let root=createRoot(container);
async function click(element){assert.ok(element);await act(async()=>element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
await act(async()=>root.render(createElement(SimulatedOrdersScreen,{onContactOrder(orderId){contacted.push(orderId)}})));
await click(container.querySelector('[aria-label="查看订单 '+order.order_id+'"]'));
assert.match(container.textContent,/旧订单杯子 × 2/);
assert.match(container.textContent,/24\.68/);
assert.doesNotMatch(container.textContent,/NaN|undefined/);
await click(container.querySelector('[data-contact-order-id="'+order.order_id+'"]'));
assert.deepEqual(contacted,[order.order_id]);
await act(async()=>root.unmount());
root=createRoot(container);
await act(async()=>root.render(createElement(SimulatedCheckout,{onClose(){},onCartChange(){},onViewOrders(){}})));
assert.equal(confirmations,0,'Preview must not auto-confirm');
assert.match(container.textContent,/24\.68/);
await click([...container.querySelectorAll('button')].find(b=>b.textContent==='确认模拟结算'));
assert.equal(confirmations,1);
assert.match(container.textContent,/模拟订单已保存/);
await act(async()=>root.unmount());dom.window.close();
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['nonempty migrated public projection renders finite total','exact order contact control','preview read does not confirm','explicit confirmation preserves target and key','receipt screen']}));

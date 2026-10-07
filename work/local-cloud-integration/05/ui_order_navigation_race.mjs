/** Public DOM delayed demo-state response; dedicated Tester executes. */
import assert from 'node:assert/strict'
import {createRequire} from 'node:module'
import path from 'node:path'
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'))
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,localStorage:dom.window.localStorage,IS_REACT_ACT_ENVIRONMENT:true})
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/local-cloud-integration/05/compiled/package.json'))
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),{SimulatedOrdersScreen}=compiled('./SimulatedOrders.js')
const orders=['A','B'].map(order_id=>({order_id,version:1,status:'submitted',items:[],total_fen:500,created_at:'2026-10-07T12:00:00Z'}))
let finish,contact='';const calls=[];const response=data=>new Response(JSON.stringify(data))
globalThis.fetch=async(url,options={})=>{
 calls.push({url,options})
 if(url.endsWith('/bootstrap'))return response({owner_id:'synthetic',store_id:'demo',delivery_zone_id:'demo'})
 if(url.endsWith('/orders'))return response({items:orders})
 if(url.endsWith('/orders/A'))return response(orders[0])
 if(url.endsWith('/orders/B'))return response(orders[1])
 if(url.endsWith('/orders/A/demo-state'))return new Promise(resolve=>{finish=()=>resolve(process.argv[2]==='failure'?new Response(JSON.stringify({error:{message:'delayed failure'}}),{status:409}):response({...orders[0],status:'shipped',version:2}))})
 throw new Error('Unexpected '+url)
}
const root=createRoot(document.getElementById('root')),buttons=()=>[...document.querySelectorAll('button')]
const button=text=>buttons().find(row=>row.textContent===text)
async function click(el){assert.ok(el);await act(async()=>el.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
await act(async()=>root.render(createElement(SimulatedOrdersScreen,{onContactOrder:id=>{contact=id}})))
await click(document.querySelector('[aria-label="查看订单 A"]'))
await click(button('模拟推进至配送中'))
await click(button('← 返回订单列表'))
await click(document.querySelector('[aria-label="查看订单 B"]'))
await act(async()=>finish())
assert.equal(document.querySelector('[data-order-id]')?.getAttribute('data-order-id'),'B','Late A result must preserve newer B detail')
await click(button('联系墨墨'));assert.equal(contact,'B','Contact follows displayed B, not stale A result')
assert.equal(calls.filter(row=>row.url.endsWith('/demo-state')).length,1,'Authorized A transition is not retried or cancelled')
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,mode:process.argv[2]??'success',level:'public-DOM-controlled-transport'}))

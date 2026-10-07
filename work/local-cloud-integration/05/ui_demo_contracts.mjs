/** Retained components + real client modules over controlled HTTP responses. DOM, not browser. */
import assert from 'node:assert/strict'
import path from 'node:path'
import {createRequire} from 'node:module'
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'))
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,localStorage:dom.window.localStorage,sessionStorage:dom.window.sessionStorage,IS_REACT_ACT_ENVIRONMENT:true})
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,'work/local-cloud-integration/05/compiled/package.json'))
const React=frontend('react'),{act,createElement:h,useState}=React,{createRoot}=frontend('react-dom/client')
const root=createRoot(document.getElementById('root')),calls=[],mode=process.argv[2]
const response=(value,status=200)=>new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json'}})
const btn=text=>[...document.querySelectorAll('button')].find(node=>node.textContent===text)
async function click(node){assert.ok(node);await act(async()=>node.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
async function change(label,value){const node=document.querySelector(`[aria-label="${label}"]`);assert.ok(node);await act(async()=>{const proto=node.tagName==='SELECT'?dom.window.HTMLSelectElement.prototype:dom.window.HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(proto,'value').set.call(node,value);node.dispatchEvent(new dom.window.Event(node.tagName==='SELECT'?'change':'input',{bubbles:true}))})}
const product={sku_id:'demo-sku',name:'模拟饮品',name_zh:'模拟饮品',category_id:'beverage',price_fen:650,brand:'演示',spec_quantity:330,spec_unit:'ml',available_qty:8,sellable:true}
let handler
// Unexpected calls are failures, not permissive fallback responses.
globalThis.fetch=async(url,options={})=>{const call={url:String(url),method:options.method??'GET',body:options.body?JSON.parse(options.body):null,headers:options.headers};calls.push(call);if(call.url.endsWith('/bootstrap'))return response({owner_id:'synthetic',store_id:'demo',delivery_zone_id:'demo'});return handler(call)}
if(mode==='product'){
 const ProductDetail=compiled('./ProductDetail.js').default,{addCartItem}=compiled('./lib/saleGuide.js')
 let release,failRead=false,failAdd=false
 handler=async call=>{if(call.url==='/api/v1/products/unavailable')return response({...product,sku_id:'unavailable',sellable:false,price_fen:null});if(call.url==='/api/v1/products/demo-sku')return failRead?response({error:{message:'详情暂不可读'}},503):response(product);if(call.url==='/api/v1/cart/items'){assert.deepEqual(call.body,{sku_id:'demo-sku',quantity:1,expected_cart_version:7});return new Promise(resolve=>{release=()=>resolve(failAdd?response({error:{message:'当前报价已失效',code:'STALE_STATE'}},409):response({version:8,items:[{sku_id:'demo-sku',quantity:1}],total_price_fen:650}))})}throw new Error(call.url)}
 function Harness(){const [busy,setBusy]=useState(false),[error,setError]=useState('');async function add(id){setBusy(true);try{await addCartItem(id,1,7)}catch(e){setError(e.message)}finally{setBusy(false)}}return h(React.Fragment,null,h(ProductDetail,{skuId:'demo-sku',onClose(){},onAdd:add,adding:busy}),h('p',{'data-error':true},error))}
 await act(async()=>root.render(h(Harness)));assert.match(document.body.textContent,/6.50 元/);assert.match(document.body.textContent,/模拟数据/);assert.equal(calls.filter(c=>c.method==='POST').length,0)
 await click(btn('添加一件到购物车'));assert.equal(btn('正在添加…').disabled,true);await click(btn('正在添加…'));assert.equal(calls.filter(c=>c.url==='/api/v1/cart/items').length,1)
 await act(async()=>release());assert.equal(btn('添加一件到购物车').disabled,false)
 failAdd=true;await click(btn('添加一件到购物车'));await act(async()=>release());assert.match(document.body.textContent,/当前报价已失效/);assert.equal(calls.filter(c=>c.url==='/api/v1/cart/items').length,2)
 await act(async()=>root.render(h(ProductDetail,{skuId:'unavailable',onClose(){},onAdd(){throw new Error('Unavailable add')},adding:false})));assert.equal(btn('添加一件到购物车').disabled,true);assert.match(document.body.textContent,/当前价格未知/);assert.match(document.body.textContent,/当前不可售/)
 failRead=true;await act(async()=>root.render(h(ProductDetail,{skuId:'demo-sku',onClose(){},onAdd(){throw new Error('Unreadable add')},adding:false})));assert.match(document.body.textContent,/详情暂不可读/);assert.equal(btn('添加一件到购物车'),undefined)
}
if(mode==='aftersales'){
 const {AfterSalesPanel}=compiled('./AfterSalesPanel.js'),{HumanCasePanel}=compiled('./HumanCasePanel.js')
 let state={proposal:null,receipts:[]},human=null,releaseConfirm,failUpload=true
 const proposal={proposal_id:'proposal-one',revision:1,order_id:'order-a',kind:'quality',problem_quantity:1,photo_ids:['photo-one'],amount_fen:650,reason:'包装破损',policy_id:'demo-policy',policy:'模拟人工核对',items:[{item_id:'demo-sku',name:'模拟饮品',quantity:1,amount_fen:650}]}
 const receipt={...proposal,receipt_id:'receipt-one',application_id:'application-one',status:'requested',message:'等待人工核对，尚未退款'}
 const revoked=[];URL.createObjectURL=()=> 'blob:synthetic-photo';URL.revokeObjectURL=url=>revoked.push(url)
 handler=async call=>{
  if(call.url.endsWith('/aftersales'))return response(state)
  if(call.url==='/api/v1/orders/order-a')return response({items:[{sku_id:'demo-sku',name:'模拟饮品',quantity:2}]})
  if(call.url.endsWith('/human-ticket'))return response(human)
  if(call.url.endsWith('/photos')&&call.method==='POST'){assert.equal(call.body.selection_version,4);assert.equal(call.body.content_type,'image/png');assert.ok(call.body.data_base64);return failUpload?response({error:{message:'照片格式校验失败'}},422):response({photo_id:'photo-one',order_id:'order-a'})}
  if(call.url.endsWith('/photos/photo-one'))return new Response(new Uint8Array([1,2,3]),{headers:{'Content-Type':'image/png'}})
  if(call.url.endsWith('/proposals')){assert.deepEqual(call.body,{kind:'quality',item_id:'demo-sku',reason:'包装破损',selection_version:4,problem_quantity:1,photo_ids:['photo-one']});state={...state,proposal};return response(proposal)}
  if(call.url.endsWith('/confirm')){assert.deepEqual(call.body,{proposal_id:'proposal-one',idempotency_key:'proposal-one',confirmed:true});return new Promise(resolve=>{releaseConfirm=()=>{state={proposal:null,receipts:[receipt]};human={ticket_id:'ticket-one',case_id:'case-one',status:'open',summary:'质量问题',photos:[{photo_id:'photo-one',content_type:'image/png'}],applications:[receipt],messages:[]};resolve(response(receipt))}})}
  throw new Error(call.url)
 }
 function Harness(){const [refresh,setRefresh]=useState(0);return h(React.Fragment,null,h(AfterSalesPanel,{caseId:'case-one',orderId:'order-a',selectionVersion:4,refreshKey:0,disabled:false,onCaseChange:()=>setRefresh(n=>n+1)}),h(HumanCasePanel,{caseId:'case-one',refreshKey:refresh}))}
 await act(async()=>root.render(h(Harness)));await change('售后类型','quality');await change('退货商品','demo-sku');assert.equal(btn('查看申请提案').disabled,true);await change('问题销售包装数','1');await change('售后原因','包装破损')
 async function upload(){const input=document.querySelector('[aria-label="质量问题照片"]');Object.defineProperty(input,'files',{configurable:true,value:[{type:'image/png',arrayBuffer:async()=>new Uint8Array([1,2,3]).buffer}]});await act(async()=>input.dispatchEvent(new dom.window.Event('change',{bubbles:true})))}
 await upload();assert.match(document.body.textContent,/照片格式校验失败/);assert.equal(document.querySelectorAll('img').length,0)
 failUpload=false;await upload();assert.equal(document.querySelectorAll('img[alt="待人工核对的照片"]').length,1)
 await click(btn('查看申请提案'));assert.equal(calls.filter(c=>c.url.endsWith('/confirm')).length,0);assert.match(document.querySelector('[data-proposal-id]').textContent,/质量问题登记/)
 await click(btn('确认提交此模拟申请'));assert.equal(btn('确认提交此模拟申请').disabled,true);await click(btn('确认提交此模拟申请'));assert.equal(calls.filter(c=>c.url.endsWith('/confirm')).length,1)
 await act(async()=>releaseConfirm());assert.ok(document.querySelector('[data-receipt-id="receipt-one"]'));assert.equal(document.querySelectorAll('img[alt="待核对的问题照片"]').length,1);assert.match(document.body.textContent,/尚未退款/)
 assert.equal(calls.filter(c=>c.url.includes('/receipt-introductions')).length,0)
 await act(async()=>root.render(h('div')));assert.deepEqual(revoked,['blob:synthetic-photo'])
}
if(mode==='orders'){
 const {SimulatedOrdersScreen}=compiled('./SimulatedOrders.js');let order={order_id:'order-a',version:1,status:'submitted',total_fen:650,created_at:'2026-10-07T12:00:00Z',items:[{sku_id:'demo-sku',name:'模拟饮品',quantity:1,unit_price_fen:650,line_total_fen:650}]},release,fail=false
 const snapshot=structuredClone(order.items)
 handler=async call=>{if(call.url==='/api/v1/orders')return response({items:[order]});if(call.url==='/api/v1/orders/order-a')return response(order);if(call.url.endsWith('/demo-state')){assert.equal(call.body.expected_version,order.version);assert.equal(call.body.status,order.status==='submitted'?'shipped':'delivered');return new Promise(resolve=>{release=()=>{if(fail)return resolve(response({error:{message:'状态版本冲突'}},409));order={...order,status:call.body.status,version:order.version+1};resolve(response(order))}})}throw new Error(call.url)}
 await act(async()=>root.render(h(SimulatedOrdersScreen,{onContactOrder(){}})));await click(document.querySelector('[aria-label="查看订单 order-a"]'))
 await click(btn('模拟推进至配送中'));await click(btn('模拟推进至配送中'));assert.equal(calls.filter(c=>c.url.endsWith('/demo-state')).length,1);await act(async()=>release());assert.ok(btn('模拟签收'))
 fail=true;await click(btn('模拟签收'));await act(async()=>release());assert.match(document.body.textContent,/状态版本冲突/);assert.equal(order.status,'shipped');assert.equal(calls.filter(c=>c.url.endsWith('/demo-state')).length,2)
 await click(document.querySelector('[aria-label="查看订单 order-a"]'));fail=false;await click(btn('模拟签收'));await act(async()=>release());assert.equal(order.status,'delivered');assert.deepEqual(order.items,snapshot);assert.equal(order.total_fen,650);assert.equal(btn('模拟签收'),undefined)
}
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,mode,level:'controlled-DOM-real-client-modules'}))

/** Public component interactions, controlled DOM; no browser claim. */
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import path from 'node:path'
const cwd=process.cwd()
const support=createRequire(path.join(process.env.MERCURY_TEST_SUPPORT!, 'package.json'))
const {JSDOM}=support('jsdom')
const dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
dom.window.HTMLElement.prototype.scrollIntoView=()=>{}
Object.assign(globalThis,{window:dom.window,document:dom.window.document,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,IS_REACT_ACT_ENVIRONMENT:true})
const frontend=createRequire(path.join(cwd,'frontend/package.json'))
const compiled=createRequire(path.join(process.env.MERCURY_COMPILED_DIR!,'package.json'))
const React=frontend('react')
const {createRoot}=frontend('react-dom/client')
const {MercuryChat}=compiled('./MercuryChat.js')
const {SimulatedOrdersScreen}=compiled('./SimulatedOrders.js')
const {act,createElement}=React
const container=document.getElementById('root')!
let root=createRoot(container)
let streams=0
let deferNextSelection=false
let finishOldSelection: (()=>void) | undefined
let selections:string[]=[]
let caseValue={session_id:'case-1',order_id:null as string|null,selection_version:0,status:'ready',messages:[]}
const orders=['ORDER-A','ORDER-B'].map(order_id=>({order_id,status_text:'模拟已提交',total:'5.00',products:['面粉'],store_id:'store-1',version:1,created_at:'2026-10-05T12:00:00',status:'submitted',total_fen:500,items:[]}))
function response(value:unknown){return new Response(JSON.stringify(value))}
globalThis.fetch=async(input,options)=>{
 const url=String(input)
 if(url.endsWith('/aftersales'))return response({proposal:null,receipts:[],simulated:true})
 if(url.endsWith('/api/v1/orders/ORDER-A'))return response(orders[0])
 if(url.endsWith('/human-ticket'))return response(null)
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner-a',store_id:'store-1',delivery_zone_id:'zone-1',business_data_mode:'demo'})
 if(url.endsWith('/sessions')&&options?.method==='POST')return response({session_id:'case-1'})
 if(url.endsWith('/mercury/orders'))return response({orders})
 if(url.endsWith('/api/v1/orders'))return response({items:orders})
 if(url.endsWith('/api/v1/orders/ORDER-B'))return response(orders[1])
 if(url.endsWith('/order')){
  const body=JSON.parse(String(options!.body));selections.push(body.order_id)
  const commit=()=>{
   if(body.selection_version!==caseValue.selection_version)return new Response('{}',{status:409})
   caseValue={...caseValue,order_id:body.order_id,selection_version:caseValue.selection_version+1};return response(caseValue)
  }
  if(deferNextSelection){deferNextSelection=false;return new Promise(resolve=>{finishOldSelection=()=>resolve(commit())})}
  return commit()
 }
 if(url.endsWith('/turns/stream')){streams++;throw new Error('No implicit query permitted')}
 if(url.endsWith('/sessions/case-1'))return response(caseValue)
 throw new Error(`Unexpected ${url}`)
}
async function click(el:Element){await act(async()=>el.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true})))}
let contacted=''
await act(async()=>root.render(createElement(SimulatedOrdersScreen,{onContactOrder:(id:string)=>{contacted=id}})))
await click(container.querySelector('[aria-label="查看订单 ORDER-B"]')!)
await click(container.querySelector('[data-contact-order-id="ORDER-B"]')!)
assert.equal(contacted,'ORDER-B','Contact must carry exact persisted order ID')
await act(async()=>root.unmount());root=createRoot(container)
await act(async()=>root.render(createElement(React.StrictMode,null,createElement(MercuryChat,{initialOrderId:contacted,entrySequence:1,visible:true}))))
assert.equal(container.querySelector('select')!.value,'ORDER-B')
assert.deepEqual(selections,['ORDER-B'])
assert.equal(streams,0)
await act(async()=>{const select=container.querySelector('select')!;select.value='ORDER-A';select.dispatchEvent(new dom.window.Event('change',{bubbles:true}))})
assert.equal(container.querySelector('select')!.value,'ORDER-A')
await act(async()=>root.render(createElement(React.StrictMode,null,createElement(MercuryChat,{initialOrderId:'ORDER-B',entrySequence:2,visible:true}))))
assert.equal(container.querySelector('select')!.value,'ORDER-B')
assert.deepEqual(selections,['ORDER-B','ORDER-A','ORDER-B'])
await act(async()=>root.render(createElement(React.StrictMode,null,createElement(MercuryChat,{initialOrderId:'ORDER-B',entrySequence:2,visible:false}))))
await act(async()=>root.render(createElement(React.StrictMode,null,createElement(MercuryChat,{initialOrderId:'ORDER-B',entrySequence:2,visible:true}))))
assert.equal(container.querySelector('select')!.value,'ORDER-B')
assert.equal(streams,0)
// An older delayed selection must not silently become authoritative after a newer
// contact for the order that is still shown in the current canonical read.
deferNextSelection=true
await act(async()=>root.render(createElement(React.StrictMode,null,createElement(MercuryChat,{initialOrderId:'ORDER-A',entrySequence:3,visible:true}))))
await act(async()=>root.render(createElement(React.StrictMode,null,createElement(MercuryChat,{initialOrderId:'ORDER-B',entrySequence:4,visible:true}))))
await act(async()=>finishOldSelection!())
assert.equal(container.querySelector('select')!.value,'ORDER-B')
assert.equal(caseValue.order_id,'ORDER-B','New contact must fence the earlier in-flight different selection')
assert.equal(streams,0)
await act(async()=>root.unmount());root=createRoot(container)
// Model App's conditional mount and keep the explicit entry intent in its parent.
function EntryParent(){
 const [shown,setShown]=React.useState(true)
 const [entry,setEntry]=React.useState({orderId:'ORDER-B' as string|undefined,sequence:5})
 const consumed=React.useCallback((sequence:number)=>setEntry((current:any)=>current.sequence===sequence?{...current,orderId:undefined}:current),[])
 return createElement(React.Fragment,null,
  createElement('button',{'data-toggle-mercury':true,onClick:()=>setShown((value:boolean)=>!value)},'切换页面'),
  shown?createElement(MercuryChat,{initialOrderId:entry.orderId,entrySequence:entry.sequence,onOrderEntryConsumed:consumed,visible:true}):null)
}
await act(async()=>root.render(createElement(React.StrictMode,null,createElement(EntryParent))))
await act(async()=>{const select=container.querySelector('select')!;select.value='ORDER-A';select.dispatchEvent(new dom.window.Event('change',{bubbles:true}))})
assert.equal(container.querySelector('select')!.value,'ORDER-A')
await click(container.querySelector('[data-toggle-mercury]')!)
assert.equal(container.querySelector('select'),null,'Leaving page must fully unmount Mercury')
await click(container.querySelector('[data-toggle-mercury]')!)
assert.equal(container.querySelector('select')!.value,'ORDER-A','Reopening must restore manual selection, not replay consumed contact')
assert.equal(caseValue.order_id,'ORDER-A')
assert.equal(streams,0)
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,level:'controlled-DOM',checks:['exact contact','canonical selection before query','repeat same contact','close and resume','no implicit stream']}))

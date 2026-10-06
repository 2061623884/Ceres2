/** Current canonical proposal/receipt after failure; controlled DOM, not browser proof. */
import assert from 'node:assert/strict'
import path from 'node:path'
import {createRequire} from 'node:module'
const cwd=process.cwd(),support=createRequire(path.join(cwd,'work/clean-rebuild/02/test-support/package.json'))
const {JSDOM}=support('jsdom'),dom=new JSDOM('<div id="root"></div>',{url:'http://localhost/'})
Object.assign(globalThis,{window:dom.window,document:dom.window.document,localStorage:dom.window.localStorage,HTMLElement:dom.window.HTMLElement,MouseEvent:dom.window.MouseEvent,IS_REACT_ACT_ENVIRONMENT:true})
const frontend=createRequire(path.join(cwd,'frontend/package.json')),compiled=createRequire(path.join(cwd,process.argv[2]??'work/clean-rebuild/14/compiled/package.json'))
const {act,createElement}=frontend('react'),{createRoot}=frontend('react-dom/client'),{AfterSalesPanel}=compiled('./AfterSalesPanel.js')
const preview={proposal_id:'p',revision:1,order_id:'o',kind:'refund',amount_fen:600,reason:'更换',policy_id:'P-REF-01',policy:'模拟退款',items:[{item_id:'sku',name:'薯片',quantity:1,amount_fen:600}]}
const receipt={...preview,receipt_id:'r',application_id:'a',status:'requested',message:'模拟申请已提交，尚未审批或退款到账'}
let state={proposal:preview,receipts:[]},mode='lost-response',writes=0
const response=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}})
globalThis.fetch=async(input,options={})=>{
 const url=String(input)
 if(url.endsWith('/bootstrap'))return response({owner_id:'owner',store_id:'store'})
 if(url.endsWith('/aftersales'))return response(state)
 if(url.includes('/orders/'))return response({items:[{sku_id:'sku',name:'薯片',quantity:1}]})
 if(url.endsWith('/confirm')){writes++;state=mode==='lost-response'?{proposal:null,receipts:[receipt]}:{proposal:preview,receipts:[]};return response({error:{message:'提交响应暂时失败，请查看当前回执'}},503)}
 throw new Error('Unexpected '+url)
}
const container=document.getElementById('root');let root=createRoot(container)
async function render(refreshKey=0){await act(async()=>root.render(createElement(AfterSalesPanel,{caseId:'case',orderId:'o',selectionVersion:1,refreshKey,disabled:false})))}
async function confirm(){const button=[...container.querySelectorAll('button')].find(b=>b.textContent==='确认提交此模拟申请');assert.ok(button);await act(async()=>button.click())}
await render();await confirm()
assert.ok(container.querySelector('[data-receipt-id="r"]'),'A lost confirmation response must requery and show the canonical committed receipt')
assert.equal(container.querySelector('[data-proposal-id]'),null,'Committed proposal must not remain actionable')
assert.equal(writes,1,'Recovery must not repeat submission')
await act(async()=>root.unmount());root=createRoot(container);await render()
assert.ok(container.querySelector('[data-receipt-id="r"]'))
mode='precommit';state={proposal:preview,receipts:[]};await render(1);await confirm()
assert.ok(container.querySelector('[data-proposal-id="p"]'),'An unrelated/transient failure must not erase a still-valid canonical proposal')
assert.equal(container.querySelector('[data-receipt-id]'),null)
assert.match(container.textContent,/提交响应暂时失败/)
assert.equal(writes,2)
await act(async()=>root.unmount());dom.window.close()
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['failure requery','committed receipt after response loss','no automatic submission retry','valid proposal retained on transient failure','remount receipt']}))

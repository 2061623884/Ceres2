/** Controlled DOM behavior evidence; not a real browser/layout test. */
import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import path from 'node:path'
const cwd = process.cwd()
const support = createRequire(path.join(process.env.MERCURY_TEST_SUPPORT!, 'package.json'))
const { JSDOM } = support('jsdom')
const dom = new JSDOM('<div id="root"></div>', {url:'http://localhost/'})
dom.window.HTMLElement.prototype.scrollIntoView = () => {}
Object.assign(globalThis, {window:dom.window, document:dom.window.document, localStorage:dom.window.localStorage,
  HTMLElement:dom.window.HTMLElement, MouseEvent:dom.window.MouseEvent, IS_REACT_ACT_ENVIRONMENT:true})
const frontend = createRequire(path.join(cwd,'frontend/package.json'))
const compiled = createRequire(path.join(process.env.MERCURY_COMPILED_DIR!, 'package.json'))
const React = frontend('react')
const {createRoot} = frontend('react-dom/client')
const {MercuryChat} = compiled('./MercuryChat.js')
const {act, createElement} = React
const container = document.getElementById('root')!
let root = createRoot(container)
let created = 0
let finishSelection: (value: Response) => void
let streamController: ReadableStreamDefaultController
function response(data:unknown) { return new Response(JSON.stringify(data), {headers:{'Content-Type':'application/json'}}) }
function caseData(id:string) { return {session_id:id,order_id:null,selection_version:0,status:'ready',messages:[]} }
globalThis.fetch = async (input, options) => {
  const url = String(input)
  if (url.endsWith('/bootstrap')) return response({owner_id:'owner-a',store_id:'store-1',delivery_zone_id:'zone-1',llm_mode:'live',business_data_mode:'demo'})
  if (url.endsWith('/aftersales')) return response({proposal:null,receipts:[],simulated:true})
  if (url.includes('/api/v1/orders/')) return response({items:[]})
  if (url.endsWith('/human-ticket')) return response(null)
  if (url.endsWith('/sessions') && options?.method === 'POST') return response({session_id:`case-${++created}`})
  if (url.endsWith('/orders')) return response({orders:[{order_id:'ORDER-A',status_text:'已支付',total:'5.00',products:[]}]})
  if (url.endsWith('/order')) return new Promise(resolve => {finishSelection = resolve})
  if (url.endsWith('/turns/stream')) return new Response(new ReadableStream({start(controller){streamController=controller}}))
  if (/\/sessions\/case-\d+$/.test(url)) return response(caseData(url.split('/').at(-1)!))
  throw new Error(`Unexpected request ${url}`)
}
async function click(element:Element) { await act(async()=>{element.dispatchEvent(new dom.window.MouseEvent('click',{bubbles:true}))}) }
async function mount() { await act(async()=>root.render(createElement(MercuryChat,{visible:true}))) }
await mount()
await act(async()=>{
  const select = container.querySelector('select')!
  select.value = 'ORDER-A'
  select.dispatchEvent(new dom.window.Event('change',{bubbles:true}))
})
await click(container.querySelector('[aria-label="发起新对话"]')!)
assert.equal(localStorage.getItem('ceres-mercury-case'),'case-2')
await act(async()=>finishSelection(response({...caseData('case-1'),order_id:'ORDER-A',selection_version:1})))
assert.equal(container.querySelector('select')!.value,'','Late old selection must not overwrite new case')
await act(async()=>root.unmount())
root=createRoot(container)
localStorage.clear()
created=0
await mount()
const suggestion = [...container.querySelectorAll('button')].find(button=>button.textContent?.includes('查订单'))!
await click(suggestion)
await click(container.querySelector('[aria-label="发起新对话"]')!)
await act(async()=>{
  streamController.enqueue(new TextEncoder().encode('event: answer.delta\ndata: {"text":"old-case-answer"}\n\nevent: error\ndata: {"message":"old-case-error"}\n\n'))
  streamController.close()
})
assert.equal(localStorage.getItem('ceres-mercury-case'),'case-2')
assert.doesNotMatch(container.textContent!, /old-case-error|old-case-answer/)
await act(async()=>root.unmount())
dom.window.close()
console.log(JSON.stringify({ok:true,level:'DOM-only',checks:['late old selection ignored','late old SSE/error ignored']}))

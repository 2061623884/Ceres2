/** Public clients must share the in-flight trusted identity bootstrap. */
import assert from 'node:assert/strict'
import {createRequire} from 'node:module'
import path from 'node:path'
const compiled=createRequire(path.join(process.env.MERCURY_COMPILED_DIR,'package.json'))
globalThis.window={}
const {ensureIdentity}=compiled('./lib/saleGuide.js')
const {listMercuryOrders}=compiled('./lib/mercury.js')
let finishBootstrap
let mercuryReads=0
let bootstrapReads=0
globalThis.fetch=async(url)=>{
 if(String(url).endsWith('/bootstrap')){bootstrapReads++;return new Promise(resolve=>finishBootstrap=resolve)}
 if(String(url).endsWith('/mercury/orders')){mercuryReads++;return new Response(JSON.stringify({orders:[]}))}
 throw new Error(String(url))
}
const identity=ensureIdentity()
const orders=listMercuryOrders()
await Promise.resolve()
assert.equal(mercuryReads,0,'Mercury must await in-flight owner bootstrap, not create a racing owner')
finishBootstrap(new Response(JSON.stringify({owner_id:'owner-a',store_id:'store-1',delivery_zone_id:'zone-1',llm_mode:'live',business_data_mode:'demo'})))
await identity
assert.deepEqual(await orders,[])
assert.equal(bootstrapReads,1)
assert.equal(mercuryReads,1)
console.log(JSON.stringify({ok:true,checks:['one shared bootstrap','Mercury waits for trusted owner']}))

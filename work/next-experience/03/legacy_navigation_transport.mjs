/** Explicit inherited UI fixture: current-role Kev result, no routing acceptance claim.
 * Only the new navigation API is handled here. All business/unknown requests still
 * reach each original harness's strict transport and its unchanged assertions.
 */
import assert from 'node:assert/strict'
export function withLegacyNavigationTransport(original) {
 let opening=null, sequence=0
 const response=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}})
 return async(input, options={})=>{
  const url=String(input)
  if(!url.startsWith('/api/v1/navigation/sessions/'))return original(input,options)
  const body=options.body?JSON.parse(options.body):null
  if(url.endsWith('/opening')){
   if(!opening||opening.closed)opening={opening_id:'legacy-opening-'+(++sequence),role:body?.role??'keke',closed:false,prompt_displayed:false,pending_request_id:null,handoff:null}
   return response(opening)
  }
  if(options.method==='DELETE'){assert.ok(url.endsWith('/opening/'+opening.opening_id));opening.closed=true;return response(opening)}
  if(url.endsWith('/routes')){
   assert.equal(body.opening_id,opening.opening_id)
   assert.equal(body.role,opening.role)
   return response({status:'ready',routing_request_id:body.request_id,original_message:body.message,target_role:body.role,selected_object:body.selected_object,show_prompt:false})
  }
  if(url.endsWith('/switches')){assert.equal(body.opening_id,opening.opening_id);if(body.accept)opening.role=body.target_role;return response({...opening,handoff:null})}
  throw new Error('Unexpected legacy navigation fixture request '+url)
 }
}

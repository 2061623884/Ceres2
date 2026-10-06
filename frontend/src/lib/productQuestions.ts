import {fetchApi, type SessionResponse} from './saleGuide'

export interface QuestionProduct {
  sku_id: string
  name: string
  name_zh: string | null
  brand: string | null
  spec_quantity: number | null
  spec_unit: string | null
  price_fen: number | null
  available_qty: number | null
  sellable: boolean
  offer_version: number | null
  metadata: {flavor?: string; packaging?: string; pack_count?: number; attribute_evidence?: Record<string, unknown>}
}
export interface GuideQuestion {
  question_id: string
  session_id: string
  task_id: string
  state_version: number
  session_version: number
  kind: 'category' | 'products' | 'quantity'
  question: string
  status: 'active' | 'answered' | 'stale'
  selected_option_ids: string[]
  known_quantities?: Record<string,number>
  known_total_quantity?: number
  answered_quantities?: Record<string,number>
  filter_options?: Array<{option_id: string; label: string; attribute: 'brand' | 'flavor' | 'packaging' | 'spec'; value: string | {quantity:number; unit:string} | null}>
  options: Array<{option_id: string; label: string; value: string; product?: QuestionProduct}>
}
export function answerGuideQuestion(sessionId: string, question: GuideQuestion, optionIds: string[], quantities: Record<string, number>, requestId: string) {
  return fetchApi<SessionResponse>(`/api/v1/guide/sessions/${encodeURIComponent(sessionId)}/questions/${encodeURIComponent(question.question_id)}/answers`, {
    method:'POST', body:JSON.stringify({request_id:requestId,option_ids:optionIds,quantities,
      expected_task_id:question.task_id,expected_state_version:question.state_version,expected_session_version:question.session_version}),
  })
}

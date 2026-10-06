import {fetchApi, type SessionResponse} from './saleGuide'

export function enterLightMealActivity(snapshot: SessionResponse, requestId: string) {
  return fetchApi<SessionResponse>(`/api/v1/guide/sessions/${encodeURIComponent(snapshot.session_id)}/activities/light-meal`, {
    method: 'POST',
    body: JSON.stringify({
      request_id: requestId,
      expected_task_id: snapshot.task_id,
      expected_state_version: snapshot.state_version,
      expected_session_version: snapshot.session_version,
    }),
  })
}

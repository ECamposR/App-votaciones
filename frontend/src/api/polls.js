import { downloadFile, request } from './client'

export function listPolls() {
  return request('/api/polls')
}

export function getPoll(id) {
  return request(`/api/polls/${id}`)
}

export function createPoll(payload) {
  return request('/api/polls', { method: 'POST', json: payload })
}

export function updatePoll(id, payload) {
  return request(`/api/polls/${id}`, { method: 'PATCH', json: payload })
}

export function deletePoll(id) {
  return request(`/api/polls/${id}`, { method: 'DELETE' })
}

export function transitionPollStatus(id, status) {
  return request(`/api/polls/${id}/status`, { method: 'POST', json: { status } })
}

export function listVoterGroups(id) {
  return request(`/api/polls/${id}/voter-groups`)
}

export function createVoterGroup(id, payload) {
  return request(`/api/polls/${id}/voter-groups`, { method: 'POST', json: payload })
}

export function updateVoterGroup(id, groupId, payload) {
  return request(`/api/polls/${id}/voter-groups/${groupId}`, { method: 'PATCH', json: payload })
}

export function deleteVoterGroup(id, groupId) {
  return request(`/api/polls/${id}/voter-groups/${groupId}`, { method: 'DELETE' })
}

export function listCategories(id) {
  return request(`/api/polls/${id}/categories`)
}

export function createCategory(id, payload) {
  return request(`/api/polls/${id}/categories`, { method: 'POST', json: payload })
}

export function updateCategory(id, categoryId, payload) {
  return request(`/api/polls/${id}/categories/${categoryId}`, { method: 'PATCH', json: payload })
}

export function deleteCategory(id, categoryId) {
  return request(`/api/polls/${id}/categories/${categoryId}`, { method: 'DELETE' })
}

export function importOptions(id, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request(`/api/polls/${id}/options/import`, { method: 'POST', json: formData })
}

export async function downloadReport(id) {
  return downloadFile(`/api/polls/${id}/report.xlsx`)
}

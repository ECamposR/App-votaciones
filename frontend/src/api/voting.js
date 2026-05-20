import { request } from './client'

export function getVotingData(token) {
  return request(`/v/${token}/data`)
}

export function submitVote(token, payload) {
  return request(`/v/${token}/vote`, { method: 'POST', json: payload })
}

export function streamDashboard(pollId) {
  return `/api/dashboard/${pollId}/stream`
}

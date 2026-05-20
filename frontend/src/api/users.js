import { request } from './client'

export function listUsers() {
  return request('/api/users')
}

export function createUser(payload) {
  return request('/api/users', { method: 'POST', json: payload })
}

export function updateUser(id, payload) {
  return request(`/api/users/${id}`, { method: 'PATCH', json: payload })
}

export function deleteUser(id) {
  return request(`/api/users/${id}`, { method: 'DELETE' })
}

export function changePassword(id, payload) {
  return request(`/api/users/${id}/change-password`, { method: 'POST', json: payload })
}

import { request } from './client'

export function getSetupStatus() {
  return request('/setup')
}

export function createInitialAdmin(payload) {
  return request('/setup', { method: 'POST', json: payload })
}

export function login(payload) {
  return request('/auth/login', { method: 'POST', json: payload })
}

export function logout() {
  return request('/auth/logout', { method: 'POST' })
}

export function getCurrentUser() {
  return request('/auth/me')
}

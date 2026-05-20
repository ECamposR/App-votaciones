import { defineStore } from 'pinia'
import {
  createInitialAdmin as createInitialAdminRequest,
  getCurrentUser,
  getSetupStatus,
  login as loginRequest,
  logout as logoutRequest,
} from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    hasSetup: null,
    loading: false,
    error: null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
  },
  actions: {
    async loadSetupStatus() {
      const data = await getSetupStatus()
      this.hasSetup = data.has_admin
      return data.has_admin
    },
    async fetchMe() {
      try {
        this.user = await getCurrentUser()
      } catch (error) {
        if (error.status === 401) {
          this.user = null
          return null
        }
        throw error
      }
      return this.user
    },
    async bootstrap() {
      this.loading = true
      this.error = null
      try {
        await this.loadSetupStatus()
        if (this.hasSetup) {
          await this.fetchMe()
        }
      } catch (error) {
        this.error = error.message
      } finally {
        this.loading = false
      }
    },
    async login(payload) {
      const user = await loginRequest(payload)
      this.user = user
      return user
    },
    async createInitialAdmin(payload) {
      const user = await createInitialAdminRequest(payload)
      this.hasSetup = true
      return user
    },
    async logout() {
      await logoutRequest()
      this.user = null
    },
  },
})

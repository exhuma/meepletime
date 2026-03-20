import { defineStore } from 'pinia'
import api from '../api'
import router from '../router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,   // decoded JWT payload + id from /auth/me
    token: null,
  }),
  getters: {
    isLoggedIn: (state) => state.token !== null,
  },
  actions: {
    async login(email, password) {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)
      const response = await api.post('/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      this.token = response.data.access_token
      localStorage.setItem('meepletime_token', this.token)
      this._decodeToken()
      await this._fetchMe()
      router.push('/circles')
    },
    async register(email, password) {
      await api.post('/auth/register', { email, password })
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('meepletime_token')
      router.push('/login')
    },
    async loadFromStorage() {
      const token = localStorage.getItem('meepletime_token')
      if (token) {
        this.token = token
        this._decodeToken()
        try {
          await this._fetchMe()
        } catch {
          // token may be expired; interceptor will handle redirect
        }
      }
    },
    async _fetchMe() {
      const res = await api.get('/auth/me')
      // merge UUID id into user object
      this.user = { ...this.user, ...res.data }
    },
    _decodeToken() {
      try {
        const parts = this.token.split('.')
        if (parts.length === 3) {
          const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
          this.user = payload
        }
      } catch {
        this.user = null
      }
    },
  },
})

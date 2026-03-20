import axios, { type AxiosInstance } from 'axios'
import type { Router } from 'vue-router'

let _router: Router | null = null

/** Call once during app bootstrap to give the API client access to the router for 401 redirects. */
export function setRouter(router: Router): void {
  _router = router
}

const api: AxiosInstance = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('meepletime_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('meepletime_token')
      _router?.push('/login')
    }
    return Promise.reject(error)
  },
)

export default api

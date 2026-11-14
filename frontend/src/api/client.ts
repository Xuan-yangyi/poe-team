import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8333',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor: attach JWT
api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

// Response interceptor: handle 401 refresh
api.interceptors.response.use(
  (resp) => resp,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const auth = useAuthStore()
      if (auth.refreshToken) {
        try {
          const resp = await axios.post(
            `${api.defaults.baseURL}/auth/refresh`,
            { refresh_token: auth.refreshToken }
          )
          const data = resp.data.data
          auth.accessToken = data.access_token
          localStorage.setItem('access_token', data.access_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          auth.logout()
        }
      } else {
        auth.logout()
      }
    }
    return Promise.reject(error)
  }
)

export default api
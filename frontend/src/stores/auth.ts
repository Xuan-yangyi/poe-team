import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

export interface UserInfo {
  user_id: string
  username: string
  role: string
  tenant_id: string
  display_name?: string
  idh_id?: string
}

function parseJwtPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split('.')
    if (parts.length < 2) return null
    const base64 = parts[1]!
    const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json)
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const userInfo = ref<UserInfo | null>(
    JSON.parse(localStorage.getItem('user_info') || 'null')
  )

  const isLoggedIn = computed(() => !!accessToken.value)

  async function login(username: string, password: string) {
    const resp = await api.post('/auth/login', { username, password })
    const data = resp.data.data
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token

    // User info comes from response; fall back to JWT payload
    const jwtPayload = parseJwtPayload(data.access_token)
    userInfo.value = data.user || {
      user_id: jwtPayload?.sub || '',
      username,
      role: jwtPayload?.role || 'unknown',
      tenant_id: jwtPayload?.tenant_id || '',
    }

    localStorage.setItem('access_token', accessToken.value)
    localStorage.setItem('refresh_token', refreshToken.value)
    localStorage.setItem('user_info', JSON.stringify(userInfo.value))
  }

  function logout() {
    accessToken.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  return { accessToken, refreshToken, userInfo, isLoggedIn, login, logout }
})
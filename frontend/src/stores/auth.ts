import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/client'

export interface UserInfo {
  username: string
  role: string
  tenant_id: string
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
    userInfo.value = {
      username: data.username,
      role: data.role,
      tenant_id: data.tenant_id,
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
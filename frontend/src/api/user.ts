import api from './client'

export function getMyProfile() {
  return api.get('/users/me')
}

export function updateProfile(data: {
  display_name?: string
  avatar_emoji?: string
  avatar_url?: string
  email?: string
}) {
  return api.put('/users/me', data)
}

export function changePassword(data: { current_password: string; new_password: string }) {
  return api.put('/users/me/password', data)
}

export function uploadFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
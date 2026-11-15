import api from './client'

export function getPresets() {
  return api.get('/llm-config/presets')
}

export function listConfigs() {
  return api.get('/llm-config')
}

export function createConfig(data: Record<string, any>) {
  return api.post('/llm-config', data)
}

export function updateConfig(id: string, data: Record<string, any>) {
  return api.put(`/llm-config/${id}`, data)
}

export function deleteConfig(id: string) {
  return api.delete(`/llm-config/${id}`)
}

export function testConfig(id: string, message?: string) {
  return api.post(`/llm-config/${id}/test`, { message: message || 'Hello, respond OK.' })
}
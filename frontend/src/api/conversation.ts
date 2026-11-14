import api from './client'

export function listConversations(params?: Record<string, any>) {
  return api.get('/conversations', { params })
}

export function getConversation(id: string) {
  return api.get(`/conversations/${id}`)
}

export function createConversation(data: Record<string, any>) {
  return api.post('/conversations', data)
}

export function getMessages(convId: string, params?: Record<string, any>) {
  return api.get(`/conversations/${convId}/messages`, { params })
}

export function postMessage(convId: string, data: Record<string, any>) {
  return api.post(`/conversations/${convId}/messages`, data)
}

export function addTag(data: Record<string, any>) {
  return api.post('/conversations/tags', data)
}
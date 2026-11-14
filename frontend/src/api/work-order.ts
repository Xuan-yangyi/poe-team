import api from './client'

export function listWorkOrders(params?: Record<string, any>) {
  return api.get('/work-orders', { params })
}

export function getWorkOrder(woId: string) {
  return api.get(`/work-orders/${woId}`)
}

export function createWorkOrder(data: Record<string, any>) {
  return api.post('/work-orders', data)
}

export function issueWorkOrder(woId: string) {
  return api.post(`/work-orders/${woId}/issue`)
}

export function acceptWorkOrder(woId: string) {
  return api.post(`/work-orders/${woId}/accept`)
}

export function changeWorkOrder(woId: string, data: Record<string, any>) {
  return api.post(`/work-orders/${woId}/change`, data)
}
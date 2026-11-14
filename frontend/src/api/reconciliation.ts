import api from './client'

export function createPeriod(data: Record<string, any>) {
  return api.post('/reconciliation/periods', data)
}

export function getPeriod(id: number) {
  return api.get(`/reconciliation/periods/${id}`)
}

export function getItems(periodId: number, params?: Record<string, any>) {
  return api.get(`/reconciliation/periods/${periodId}/items`, { params })
}

export function disputeItem(id: number, data: Record<string, any>) {
  return api.put(`/reconciliation/items/${id}/dispute`, data)
}

export function createAdjustment(data: Record<string, any>) {
  return api.post('/reconciliation/adjustments', data)
}

export function approveAdjustment(id: number, data: Record<string, any>) {
  return api.post(`/reconciliation/adjustments/${id}/approve`, data)
}
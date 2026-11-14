import api from './client'

export function listAlerts(params?: Record<string, any>) {
  return api.get('/alerts', { params })
}

export function acknowledgeAlert(alertId: string, data: Record<string, any>) {
  return api.post(`/alerts/${alertId}/acknowledge`, data)
}

export function resolveAlert(alertId: string, data: Record<string, any>) {
  return api.post(`/alerts/${alertId}/resolve`, data)
}
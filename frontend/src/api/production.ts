import api from './client'

export function createIssue(data: Record<string, any>) {
  return api.post('/issues', data)
}

export function createWipReport(data: Record<string, any>) {
  return api.post('/wip-reports', data)
}

export function createFgReceipt(data: Record<string, any>) {
  return api.post('/fg-receipts', data)
}
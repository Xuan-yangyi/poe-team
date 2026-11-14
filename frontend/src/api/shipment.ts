import api from './client'

export function listShipments(params?: Record<string, any>) {
  return api.get('/shipments', { params })
}

export function getShipment(shipmentId: string) {
  return api.get(`/shipments/${shipmentId}`)
}

export function createShipment(data: Record<string, any>) {
  return api.post('/shipments', data)
}

export function confirmShipment(shipmentId: string) {
  return api.post(`/shipments/${shipmentId}/confirm`)
}

export function createGoodsReceipt(data: Record<string, any>) {
  return api.post('/goods-receipts', data)
}
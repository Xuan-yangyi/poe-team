import api from './client'

export function getStock(params?: Record<string, any>) {
  return api.get('/inventory/stock', { params })
}

export function getStockLedger(lotId: string) {
  return api.get('/inventory/stock-ledger', { params: { lot_id: lotId } })
}
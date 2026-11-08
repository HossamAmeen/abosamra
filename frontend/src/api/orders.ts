import { api } from './client'
import type { CreateOrderPayload, Order, Paginated } from '@/types/api'

export const createOrder = (body: CreateOrderPayload) =>
  api.post<Order>('/orders/', body).then((r) => r.data)
export const getMyOrders = (page = 1) =>
  api.get<Paginated<Order>>('/orders/mine/', { params: { page } }).then((r) => r.data)
export const getOrder = (id: number | string) =>
  api.get<Order>(`/orders/${id}/`).then((r) => r.data)

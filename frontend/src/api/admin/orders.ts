import { api } from '../client'
import type { AdminOrder, OrderCounts, OrderStatus, Paginated } from '@/types/api'

export const listAdminOrders = (params: { status?: OrderStatus; q?: string; page?: number } = {}) =>
  api.get<Paginated<AdminOrder>>('/admin/orders/', { params }).then((r) => r.data)
export const getAdminOrder = (id: number) =>
  api.get<AdminOrder>(`/admin/orders/${id}/`).then((r) => r.data)
export const setOrderStatus = (id: number, status: OrderStatus) =>
  api.patch<AdminOrder>(`/admin/orders/${id}/`, { status }).then((r) => r.data)
export const getOrderCounts = () =>
  api.get<OrderCounts>('/admin/orders/counts/').then((r) => r.data)

import { api } from '../client'
import type { AdminCustomer, AdminOrder, Paginated } from '@/types/api'

export const listAdminCustomers = (q?: string, page = 1) =>
  api
    .get<Paginated<AdminCustomer>>('/admin/customers/', { params: { ...(q ? { q } : {}), page } })
    .then((r) => r.data)
export const getCustomerOrders = (id: number) =>
  api.get<Paginated<AdminOrder>>(`/admin/customers/${id}/orders/`).then((r) => r.data)

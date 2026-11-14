import { api } from '../client'
import type { AdminStaff, AdminStaffInput, Paginated } from '@/types/api'

export const listAdminStaff = (page = 1) =>
  api.get<Paginated<AdminStaff>>('/admin/staff/', { params: { page } }).then((r) => r.data)
export const createAdminStaff = (body: AdminStaffInput) =>
  api.post<AdminStaff>('/admin/staff/', body).then((r) => r.data)

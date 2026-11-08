import { api } from '../client'
import type { AdminOffer, AdminOfferInput } from '@/types/api'

export const listAdminOffers = () => api.get<AdminOffer[]>('/admin/offers/').then((r) => r.data)
export const createAdminOffer = (input: AdminOfferInput) =>
  api.post<AdminOffer>('/admin/offers/', input).then((r) => r.data)
export const updateAdminOffer = (id: number, input: Partial<AdminOfferInput>) =>
  api.patch<AdminOffer>(`/admin/offers/${id}/`, input).then((r) => r.data)
export const setOfferActive = (id: number, is_active: boolean) =>
  api.patch<AdminOffer>(`/admin/offers/${id}/`, { is_active }).then((r) => r.data)
export const deleteAdminOffer = (id: number) => api.delete(`/admin/offers/${id}/`)

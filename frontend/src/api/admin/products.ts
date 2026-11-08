import { api } from '../client'
import type { AdminProduct, AdminProductInput, Paginated } from '@/types/api'

/** Multipart so an image can be sent; variants are nested as a JSON string field. */
export function toProductFormData(input: Partial<AdminProductInput>): FormData {
  const fd = new FormData()
  for (const [key, value] of Object.entries(input)) {
    if (value === undefined) continue
    if (value === null) {
      // null clears nullable decimals; DRF reads '' in multipart as null.
      if (key === 'stock_qty' || key === 'low_stock_threshold') fd.append(key, '')
      continue
    }
    if (key === 'image') {
      if (value instanceof File) fd.append('image', value)
    } else if (key === 'variants') {
      fd.append('variants', JSON.stringify(value))
    } else {
      fd.append(key, String(value))
    }
  }
  return fd
}

export const listAdminProducts = (
  params: { category?: string; q?: string; is_available?: boolean; page?: number } = {},
) => api.get<Paginated<AdminProduct>>('/admin/products/', { params }).then((r) => r.data)
export const getAdminProduct = (id: number) =>
  api.get<AdminProduct>(`/admin/products/${id}/`).then((r) => r.data)
export const createAdminProduct = (input: AdminProductInput) =>
  api.post<AdminProduct>('/admin/products/', toProductFormData(input)).then((r) => r.data)
export const updateAdminProduct = (id: number, input: Partial<AdminProductInput>) =>
  api.patch<AdminProduct>(`/admin/products/${id}/`, toProductFormData(input)).then((r) => r.data)
export const setProductAvailability = (id: number, is_available: boolean) =>
  api.patch<AdminProduct>(`/admin/products/${id}/`, { is_available }).then((r) => r.data)
export const deleteAdminProduct = (id: number) => api.delete(`/admin/products/${id}/`)

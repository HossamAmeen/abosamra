import { api } from './client'
import type { AuthResponse, RegisterPayload, User } from '@/types/api'

export const register = (body: RegisterPayload) =>
  api.post<AuthResponse>('/auth/register/', body).then((r) => r.data)
export const login = (phone: string) =>
  api.post<AuthResponse>('/auth/login/', { phone }).then((r) => r.data)
export const adminLogin = (phone: string, password: string) =>
  api.post<AuthResponse>('/auth/admin/login/', { phone, password }).then((r) => r.data)
export const logout = (refresh: string) => api.post('/auth/logout/', { refresh })
export const getMe = () => api.get<User>('/me/').then((r) => r.data)
export const updateMe = (
  body: Partial<Pick<User, 'name' | 'email' | 'default_address' | 'area'>>,
) => api.patch<User>('/me/', body).then((r) => r.data)

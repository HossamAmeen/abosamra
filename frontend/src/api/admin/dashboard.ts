import { api } from '../client'
import type { Dashboard } from '@/types/api'

export const getDashboard = () => api.get<Dashboard>('/admin/dashboard/').then((r) => r.data)

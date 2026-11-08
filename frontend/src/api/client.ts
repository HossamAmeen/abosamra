import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { tokens } from './tokens'
import type { ApiErrorBody } from '@/types/api'

export const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const api = axios.create({ baseURL, timeout: 20000 })

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean }

api.interceptors.request.use((config) => {
  const access = tokens().getAccess()
  if (access && !config.headers.has('Authorization')) {
    config.headers.set('Authorization', `Bearer ${access}`)
  }
  return config
})

let refreshing: Promise<string> | null = null

/** Single in-flight refresh shared by all concurrent 401s. */
function refreshAccess(): Promise<string> {
  if (!refreshing) {
    const refresh = tokens().getRefresh()
    if (!refresh) return Promise.reject(new Error('no refresh token'))
    refreshing = axios
      .post<{ access: string; refresh?: string }>(`${baseURL}/auth/token/refresh/`, { refresh })
      .then((res) => {
        tokens().setTokens(res.data.access, res.data.refresh)
        return res.data.access
      })
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    const isAuthCall = original?.url?.includes('/auth/') ?? false
    if (error.response?.status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true
      try {
        const access = await refreshAccess()
        original.headers.set('Authorization', `Bearer ${access}`)
        return api(original)
      } catch {
        tokens().onAuthFailure()
      }
    }
    return Promise.reject(error)
  },
)

export function apiError(e: unknown): { status: number; body: ApiErrorBody } {
  if (axios.isAxiosError(e)) {
    return { status: e.response?.status ?? 0, body: (e.response?.data ?? {}) as ApiErrorBody }
  }
  return { status: 0, body: { detail: e instanceof Error ? e.message : undefined } }
}

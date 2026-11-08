import { HttpResponse } from 'msw'
import { baseURL } from '@/api/client'
import { db, type DbUser } from '../db'

export const url = (path: string) => `${baseURL.replace(/\/$/, '')}${path}`

export const PAGE_SIZE = 20

export function paginate<T>(request: Request, items: T[]) {
  const u = new URL(request.url)
  const page = Math.max(1, Number(u.searchParams.get('page') ?? 1))
  const start = (page - 1) * PAGE_SIZE
  const link = (p: number) => {
    const n = new URL(request.url)
    n.searchParams.set('page', String(p))
    return n.toString()
  }
  return {
    count: items.length,
    next: start + PAGE_SIZE < items.length ? link(page + 1) : null,
    previous: page > 1 ? link(page - 1) : null,
    results: items.slice(start, start + PAGE_SIZE),
  }
}

export const detail = (status: number, detailText: string, code?: string, extra: object = {}) =>
  HttpResponse.json({ detail: detailText, ...(code ? { code } : {}), ...extra }, { status })

export function authUser(request: Request): DbUser | null {
  const header = request.headers.get('authorization') ?? ''
  const m = /^Bearer mock-access-(\d+)(-expired)?/.exec(header)
  if (!m || m[2]) return null
  return db.users.find((u) => u.id === Number(m[1])) ?? null
}

export const UNAUTH = () => detail(401, 'لازم تسجّل دخول الأول', 'not_authenticated')
export const FORBIDDEN = () => detail(403, 'مش مسموحلك تعمل كده', 'permission_denied')

/** Returns the staff user, or an error response. */
export function requireStaff(request: Request): { user: DbUser } | { error: Response } {
  const user = authUser(request)
  if (!user) return { error: UNAUTH() }
  if (!user.is_staff) return { error: FORBIDDEN() }
  return { user }
}

let tokenCounter = 0
export function issueTokens(user: DbUser) {
  tokenCounter += 1
  return { access: `mock-access-${user.id}-${tokenCounter}`, refresh: `mock-refresh-${user.id}` }
}

export function publicUser(u: DbUser) {
  const { id, name, phone, email, default_address, area, is_staff } = u
  return { id, name, phone, email, default_address, area, is_staff }
}

import { http, HttpResponse } from 'msw'
import { normalizePhone, isValidPhone, PHONE_ERROR } from '@/utils/phone'
import { db } from '../db'
import { authUser, detail, issueTokens, publicUser, UNAUTH, url } from './util'

export const authHandlers = [
  http.post(url('/auth/register/'), async ({ request }) => {
    const body = (await request.json()) as { name?: string; phone?: string; email?: string }
    const errors: Record<string, string[]> = {}
    const name = (body.name ?? '').trim()
    if (name.length < 2 || name.length > 80) errors.name = ['الاسم لازم يكون من 2 لـ 80 حرف']
    if (!isValidPhone(body.phone ?? '')) errors.phone = [PHONE_ERROR]
    if (body.email && !/^\S+@\S+\.\S+$/.test(body.email)) errors.email = ['اكتب إيميل صحيح']
    if (Object.keys(errors).length) return HttpResponse.json(errors, { status: 400 })
    const phone = normalizePhone(body.phone!)
    if (db.users.some((u) => u.phone === phone)) {
      return detail(409, 'الرقم ده عنده حساب، ادخل بيه', 'phone_exists')
    }
    const user = {
      id: db.nextId('user'),
      name,
      phone,
      email: body.email ?? '',
      default_address: '',
      area: '',
      is_staff: false,
      created_at: new Date().toISOString(),
    }
    db.users.push(user)
    return HttpResponse.json({ ...issueTokens(user), user: publicUser(user) }, { status: 201 })
  }),

  http.post(url('/auth/login/'), async ({ request }) => {
    const body = (await request.json()) as { phone?: string }
    if (!isValidPhone(body.phone ?? ''))
      return HttpResponse.json({ phone: [PHONE_ERROR] }, { status: 400 })
    const user = db.users.find((u) => u.phone === normalizePhone(body.phone!) && !u.is_staff)
    if (!user) return detail(404, 'مفيش حساب بالرقم ده', 'not_found')
    return HttpResponse.json({ ...issueTokens(user), user: publicUser(user) })
  }),

  http.post(url('/auth/admin/login/'), async ({ request }) => {
    const body = (await request.json()) as { phone?: string; password?: string }
    const user = db.users.find((u) => u.is_staff && u.phone === normalizePhone(body.phone ?? ''))
    if (!user || user.password !== body.password)
      return detail(401, 'الرقم أو الباسورد غلط', 'invalid_credentials')
    return HttpResponse.json({ ...issueTokens(user), user: publicUser(user) })
  }),

  http.post(url('/auth/token/refresh/'), async ({ request }) => {
    const body = (await request.json()) as { refresh?: string }
    const m = /^mock-refresh-(\d+)$/.exec(body.refresh ?? '')
    const user = m ? db.users.find((u) => u.id === Number(m[1])) : undefined
    if (!user) return detail(401, 'الجلسة انتهت، سجّل دخول تاني', 'token_not_valid')
    return HttpResponse.json(issueTokens(user))
  }),

  http.post(url('/auth/logout/'), () => new HttpResponse(null, { status: 204 })),

  http.get(url('/me/'), ({ request }) => {
    const user = authUser(request)
    return user ? HttpResponse.json(publicUser(user)) : UNAUTH()
  }),

  http.patch(url('/me/'), async ({ request }) => {
    const user = authUser(request)
    if (!user) return UNAUTH()
    const body = (await request.json()) as Record<string, string>
    for (const k of ['name', 'email', 'default_address', 'area'] as const) {
      if (typeof body[k] === 'string') user[k] = body[k]
    }
    return HttpResponse.json(publicUser(user))
  }),
]

import { http, HttpResponse } from 'msw'
import type { CreateOrderPayload } from '@/types/api'
import { db } from '../db'
import { authUser, detail, paginate, UNAUTH, url } from './util'

export const orderHandlers = [
  http.post(url('/orders/'), async ({ request }) => {
    const user = authUser(request)
    if (!user) return UNAUTH()
    if (!db.settings.is_accepting_orders)
      return detail(503, 'المحل مش بياخد طلبات دلوقتي', 'closed')
    const body = (await request.json()) as CreateOrderPayload
    if ((body.address ?? '').trim().length < 10) {
      return HttpResponse.json(
        { address: ['اكتب العنوان بالتفصيل (10 حروف على الأقل)'] },
        { status: 400 },
      )
    }
    const quote = db.computeQuote({ items: body.items ?? [], bundles: body.bundles ?? [] })
    if (quote.warnings.length > 0 || quote.lines.length === 0) {
      return detail(409, 'فيه حاجات في السلة اتغيرت', 'cart_changed', { quote })
    }
    const itemNotes: Record<number, string> = {}
    for (const it of body.items ?? []) if (it.note) itemNotes[it.variant_id] = it.note
    const order = db.buildOrder(
      user,
      quote,
      body.address.trim(),
      body.area ?? '',
      body.notes ?? '',
      itemNotes,
    )
    user.default_address = body.address.trim()
    user.area = body.area ?? user.area
    return HttpResponse.json(db.serializeOrder(order), { status: 201 })
  }),

  http.get(url('/orders/mine/'), ({ request }) => {
    const user = authUser(request)
    if (!user) return UNAUTH()
    const own = db.orders
      .filter((o) => o.userId === user.id)
      .sort((a, b) => b.created_at.localeCompare(a.created_at))
    return HttpResponse.json(
      paginate(
        request,
        own.map((o) => db.serializeOrder(o)),
      ),
    )
  }),

  http.get(url('/orders/:id/'), ({ request, params }) => {
    const user = authUser(request)
    if (!user) return UNAUTH()
    const order = db.orders.find((o) => o.id === Number(params.id) && o.userId === user.id)
    return order
      ? HttpResponse.json(db.serializeOrder(order))
      : detail(404, 'الطلب ده مش موجود', 'not_found')
  }),
]

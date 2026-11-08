import { http, HttpResponse } from 'msw'
import { categories } from '../data'
import { db } from '../db'
import { detail, paginate, url } from './util'

export const publicHandlers = [
  http.get(url('/settings/'), () => HttpResponse.json(db.settings)),
  http.get(url('/categories/'), () =>
    HttpResponse.json([...categories].sort((a, b) => a.order - b.order)),
  ),

  http.get(url('/products/'), ({ request }) => {
    const sp = new URL(request.url).searchParams
    const category = sp.get('category')
    const q = sp.get('q')?.trim().toLowerCase()
    let list = db.products.filter((p) => !p.isArchived)
    if (category && category !== 'all') list = list.filter((p) => p.categorySlug === category)
    if (q) list = list.filter((p) => (p.name + ' ' + p.description).toLowerCase().includes(q))
    if (sp.get('featured') === 'true') list = list.filter((p) => p.isFeatured)
    if (sp.get('discounted') === 'true') {
      list = list.filter(
        (p) => p.variants.some((v) => v.compare != null) || db.bestPercentageOffer(p),
      )
    }
    return HttpResponse.json(
      paginate(
        request,
        list.map((p) => db.serializeProduct(p)),
      ),
    )
  }),

  http.get(url('/products/:slug/'), ({ params }) => {
    const slug = decodeURIComponent(String(params.slug))
    const p = db.products.find((x) => x.slug === slug && !x.isArchived)
    return p
      ? HttpResponse.json(db.serializeProduct(p))
      : detail(404, 'المنتج ده مش موجود', 'not_found')
  }),

  http.get(url('/offers/active/'), () => {
    const live = db.liveOffers().sort((a, b) => Number(b.is_featured) - Number(a.is_featured))
    return HttpResponse.json(live.map((o) => db.serializeOffer(o)))
  }),

  http.post(url('/cart/quote/'), async ({ request }) => {
    const body = (await request.json()) as {
      items?: { variant_id: number; qty: number }[]
      bundles?: { offer_id: number; qty: number }[]
    }
    const items = body.items ?? []
    const bundles = body.bundles ?? []
    const bad = [...items, ...bundles].some(
      (l) => !Number.isInteger(l.qty) || l.qty < 1 || l.qty > 50,
    )
    if (bad) return HttpResponse.json({ items: ['الكمية لازم تكون من 1 لـ 50'] }, { status: 400 })
    return HttpResponse.json(db.computeQuote({ items, bundles }))
  }),
]

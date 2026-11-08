import type { BrowserContext } from '@playwright/test'

// Minimal API double for the production-build (real service worker) project.
const category = (id: number, slug: string, name: string, color: string, icon: string) => ({
  id,
  slug,
  name,
  color,
  icon,
  order: id,
})
export const categories = [
  category(1, 'spices', 'بهارات', '#F6D9B8', 'soup'),
  category(2, 'herbs', 'أعشاب ومشروبات', '#DCEBCF', 'leaf'),
]
const product = (id: number, slug: string, name: string, cat: number, price: number) => ({
  id,
  slug,
  name,
  description: `وصف ${name}`,
  category: {
    slug: categories[cat].slug,
    name: categories[cat].name,
    color: categories[cat].color,
    icon: categories[cat].icon,
  },
  image: null,
  is_available: true,
  is_featured: true,
  variants: [{ id: id * 10, label: 'ربع كيلو', price, old_price: null, is_default: true }],
  active_offer: null,
})
export const products = [
  product(1, 'cumin', 'كمون مطحون', 0, 60),
  product(2, 'turmeric', 'كركم', 0, 45),
  product(3, 'anise', 'ينسون', 1, 50),
]
export const settings = {
  shop_name: 'أبو سمرة',
  phone: '01000000000',
  whatsapp: '201000000000',
  delivery_fee: 30,
  free_delivery_threshold: 500,
  currency: 'EGP',
  is_accepting_orders: true,
}

const cors = {
  'access-control-allow-origin': '*',
  'access-control-allow-headers': '*',
  'access-control-allow-methods': '*',
}

export const apiHits: string[] = []

/** Routes /api/v1/* for the whole context, including requests issued by the service worker. */
export async function mockApi(context: BrowserContext) {
  await context.route('**/api/v1/**', async (route) => {
    const req = route.request()
    const url = new URL(req.url())
    const path = url.pathname.replace(/^\/api\/v1/, '')
    if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors })
    const json = (body: unknown, status = 200) =>
      route.fulfill({
        status,
        headers: cors,
        contentType: 'application/json',
        body: JSON.stringify(body),
      })
    if (path === '/settings/') return json(settings)
    if (path === '/categories/') return json(categories)
    if (path === '/offers/active/') return json([])
    if (path === '/products/') {
      const cat = url.searchParams.get('category')
      const list = cat && cat !== 'all' ? products.filter((p) => p.category.slug === cat) : products
      return json({ count: list.length, next: null, previous: null, results: list })
    }
    const m = /^\/products\/([^/]+)\/$/.exec(path)
    if (m) {
      const p = products.find((x) => x.slug === decodeURIComponent(m[1]))
      return p ? json(p) : json({ detail: 'مش موجود', code: 'not_found' }, 404)
    }
    if (path === '/cart/quote/') {
      const body = req.postDataJSON() as { items: { variant_id: number; qty: number }[] }
      const lines = body.items.map((i) => {
        const p = products.find((x) => x.variants[0].id === i.variant_id)!
        const unit = p.variants[0].price
        return {
          variant_id: i.variant_id,
          offer_id: null,
          name: p.name,
          unit_label: 'ربع كيلو',
          qty: i.qty,
          unit_price: unit,
          line_total: unit * i.qty,
        }
      })
      const subtotal = lines.reduce((s, l) => s + l.line_total, 0)
      return json({
        lines,
        subtotal,
        discounts: [],
        discount_total: 0,
        delivery_fee: 30,
        total: subtotal + 30,
        free_delivery_threshold: 500,
        free_delivery_remaining: Math.max(0, 500 - subtotal),
        warnings: [],
      })
    }
    return json({ detail: 'غير مدعوم في الاختبار', code: 'not_mocked' }, 404)
  })
}

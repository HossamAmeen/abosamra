import { http, HttpResponse } from 'msw'
import { categories } from '../data'
import type { AdminOfferInput, OrderStatus } from '@/types/api'
import { isValidPhone, normalizePhone } from '@/utils/phone'
import { db, type DbOffer, type DbProduct } from '../db'
import { detail, paginate, requireStaff, url } from './util'

const TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
  new: ['preparing', 'cancelled'],
  preparing: ['out_for_delivery', 'cancelled'],
  out_for_delivery: ['delivered', 'cancelled'],
  delivered: [],
  cancelled: [],
}
const STATUS_AR: Record<OrderStatus, string> = {
  new: 'جديد',
  preparing: 'بيتجهز',
  out_for_delivery: 'في الطريق',
  delivered: 'اتسلم',
  cancelled: 'اتلغى',
}

const sameDay = (iso: string) => new Date(iso).toDateString() === new Date().toDateString()

interface VariantIn {
  id?: number
  label: string
  price: number | string
  old_price?: number | string | null
  stock_factor?: number
  is_default?: boolean
}

async function readBody(request: Request): Promise<Record<string, unknown>> {
  const type = request.headers.get('content-type') ?? ''
  if (type.includes('multipart/form-data')) {
    const fd = await request.formData()
    const out: Record<string, unknown> = {}
    fd.forEach((v, k) => {
      out[k] = typeof v === 'string' ? v : '[file]'
    })
    if (typeof out.variants === 'string') out.variants = JSON.parse(out.variants)
    for (const k of ['is_available', 'is_featured']) if (k in out) out[k] = out[k] === 'true'
    for (const k of ['stock_qty', 'low_stock_threshold']) if (k in out) out[k] = Number(out[k])
    if (out.image === '[file]') out.image = `https://mock.local/media/${Date.now()}.webp`
    return out
  }
  return (await request.json()) as Record<string, unknown>
}

/** The API accepts a category id or slug. */
function resolveCategory(value: unknown): string | null {
  const hit = categories.find((c) => String(c.id) === String(value) || c.slug === String(value))
  return hit?.slug ?? null
}

function applyVariants(product: DbProduct, incoming: VariantIn[]): void {
  const next = incoming.map((v) => {
    const existing = v.id ? product.variants.find((x) => x.id === v.id) : undefined
    return {
      id: existing?.id ?? db.nextId('variant'),
      label: v.label,
      price: Number(v.price),
      compare: v.old_price != null && v.old_price !== '' ? Number(v.old_price) : null,
      isDefault: !!v.is_default,
      stockFactor: v.stock_factor ?? existing?.stockFactor ?? 1,
    }
  })
  const firstDefault = next.findIndex((v) => v.isDefault)
  next.forEach((v, i) => (v.isDefault = i === (firstDefault === -1 ? 0 : firstDefault)))
  product.variants = next
}

function validateOffer(o: Partial<AdminOfferInput>): Record<string, string[]> {
  const e: Record<string, string[]> = {}
  if (!o.name?.trim()) e.name = ['اكتب اسم العرض']
  if (o.type === 'percentage') {
    if (!o.value || o.value < 1 || o.value > 90) e.value = ['نسبة الخصم لازم تكون من 1 لـ 90']
    if (!o.target) e.target = ['اختار الخصم على إيه']
  }
  if (o.type === 'bundle') {
    if (!o.bundle_items || o.bundle_items.length < 2)
      e.bundle_items = ['الباكدج لازم فيه منتجين على الأقل']
    if (!o.bundle_price || o.bundle_price <= 0) e.bundle_price = ['اكتب سعر الباكدج']
  }
  if (o.type === 'free_delivery' && (!o.min_order || o.min_order <= 0)) {
    e.min_order = ['اكتب أقل قيمة للطلب']
  }
  return e
}

function applyOffer(target: DbOffer, o: Partial<AdminOfferInput>): void {
  if (o.name !== undefined) target.name = o.name
  if (o.description !== undefined) target.description = o.description
  if (o.value !== undefined) target.value = o.value ?? 0
  if (o.target !== undefined) {
    target.target = { kind: o.target.kind, slug: o.target.slug ?? null, ids: o.target.ids ?? [] }
  }
  if (o.bundle_items !== undefined) {
    target.bundle_items = o.bundle_items.map((bi) => ({
      variant_id: bi.variant_id,
      qty: bi.qty,
      name: db.variantById(bi.variant_id)?.product.name ?? '',
    }))
    target.old_price = target.bundle_items.reduce(
      (s, bi) => s + (db.variantById(bi.variant_id)?.variant.price ?? 0) * bi.qty,
      0,
    )
  }
  if (o.bundle_price !== undefined) target.bundle_price = o.bundle_price
  if (o.min_order !== undefined) target.min_order = o.min_order
  if (o.starts_at !== undefined) target.starts_at = o.starts_at
  if (o.ends_at !== undefined) target.ends_at = o.ends_at
  if (o.is_featured !== undefined) target.is_featured = o.is_featured
  if (o.is_active !== undefined) target.is_active = o.is_active
}

export const adminHandlers = [
  http.get(url('/admin/dashboard/'), ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const today = db.orders.filter((o) => sameDay(o.created_at))
    const weekAgo = Date.now() - 7 * 86400000
    return HttpResponse.json({
      orders_today: today.length,
      sales_today: today.filter((o) => o.status !== 'cancelled').reduce((s, o) => s + o.total, 0),
      pending_count: db.orders.filter((o) => o.status === 'new').length,
      new_customers_week: db.users.filter(
        (u) => !u.is_staff && new Date(u.created_at).getTime() >= weekAgo,
      ).length,
      low_stock: db.products
        .filter((p) => p.stockQty != null && p.lowStock != null && p.stockQty <= p.lowStock)
        .map((p) => ({ id: p.id, name: p.name, stock_qty: p.stockQty, stock_unit: p.stockUnit })),
    })
  }),

  http.get(url('/admin/orders/counts/'), ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const counts = { new: 0, preparing: 0, out_for_delivery: 0, delivered: 0, cancelled: 0 }
    db.orders.forEach((o) => (counts[o.status] += 1))
    return HttpResponse.json(counts)
  }),

  http.get(url('/admin/orders/'), ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const sp = new URL(request.url).searchParams
    const status = sp.get('status')
    const q = sp.get('q')?.trim()
    let list = [...db.orders].sort((a, b) => b.created_at.localeCompare(a.created_at))
    if (status) list = list.filter((o) => o.status === status)
    if (q) {
      const phone = normalizePhone(q)
      list = list.filter(
        (o) =>
          String(o.number) === q.replace('#', '') ||
          o.customer.name.includes(q) ||
          (phone.length > 3 && o.customer.phone.includes(phone)),
      )
    }
    return HttpResponse.json(
      paginate(
        request,
        list.map((o) => db.serializeAdminOrder(o)),
      ),
    )
  }),

  http.get(url('/admin/orders/:id/'), ({ request, params }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const o = db.orders.find((x) => x.id === Number(params.id))
    return o
      ? HttpResponse.json(db.serializeAdminOrder(o))
      : detail(404, 'الطلب ده مش موجود', 'not_found')
  }),

  http.patch(url('/admin/orders/:id/'), async ({ request, params }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const o = db.orders.find((x) => x.id === Number(params.id))
    if (!o) return detail(404, 'الطلب ده مش موجود', 'not_found')
    const { status } = (await request.json()) as { status: OrderStatus }
    if (!TRANSITIONS[o.status].includes(status)) {
      return detail(
        400,
        `مينفعش تغيّر الحالة من ${STATUS_AR[o.status]} لـ ${STATUS_AR[status] ?? status}`,
        'invalid_transition',
      )
    }
    if (status === 'cancelled') db.restoreStock(o)
    o.status = status
    return HttpResponse.json(db.serializeAdminOrder(o))
  }),

  // ---- products ----
  http.get(url('/admin/products/'), ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const sp = new URL(request.url).searchParams
    let list = db.products.filter((p) => !p.isArchived)
    const category = sp.get('category')
    if (category && category !== 'all') list = list.filter((p) => p.categorySlug === category)
    const q = sp.get('q')?.trim()
    if (q) list = list.filter((p) => p.name.includes(q))
    const avail = sp.get('is_available')
    if (avail) list = list.filter((p) => p.isAvailable === (avail === 'true'))
    return HttpResponse.json(
      paginate(
        request,
        list.map((p) => db.serializeAdminProduct(p)),
      ),
    )
  }),

  http.post(url('/admin/products/'), async ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const b = await readBody(request)
    const errors: Record<string, string[]> = {}
    if (!String(b.name ?? '').trim()) errors.name = ['اكتب اسم المنتج']
    const categorySlug = resolveCategory(b.category)
    if (!categorySlug) errors.category = ['اختار القسم']
    const variants = (b.variants ?? []) as VariantIn[]
    if (variants.length < 1) errors.variants = ['ضيف وزن واحد على الأقل']
    if (Object.keys(errors).length) return HttpResponse.json(errors, { status: 400 })
    const name = String(b.name).trim()
    const p: DbProduct = {
      id: db.nextId('product'),
      slug: name.replace(/\s+/g, '-'),
      name,
      categorySlug: categorySlug!,
      description: String(b.description ?? ''),
      image: (b.image as string) ?? null,
      isAvailable: b.is_available !== false,
      isFeatured: !!b.is_featured,
      isArchived: false,
      stockQty: b.stock_qty != null ? Number(b.stock_qty) : null,
      lowStock: b.low_stock_threshold != null ? Number(b.low_stock_threshold) : null,
      stockUnit: '',
      variants: [],
    }
    applyVariants(p, variants)
    db.products.push(p)
    return HttpResponse.json(db.serializeAdminProduct(p), { status: 201 })
  }),

  http.get(url('/admin/products/:id/'), ({ request, params }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const p = db.products.find((x) => x.id === Number(params.id))
    return p
      ? HttpResponse.json(db.serializeAdminProduct(p))
      : detail(404, 'المنتج ده مش موجود', 'not_found')
  }),

  http.patch(url('/admin/products/:id/'), async ({ request, params }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const p = db.products.find((x) => x.id === Number(params.id))
    if (!p) return detail(404, 'المنتج ده مش موجود', 'not_found')
    const b = await readBody(request)
    if (b.name !== undefined) p.name = String(b.name)
    if (b.category !== undefined) {
      const slug = resolveCategory(b.category)
      if (!slug) return HttpResponse.json({ category: ['القسم ده مش موجود'] }, { status: 400 })
      p.categorySlug = slug
    }
    if (b.description !== undefined) p.description = String(b.description)
    if (b.is_available !== undefined) p.isAvailable = !!b.is_available
    if (b.is_featured !== undefined) p.isFeatured = !!b.is_featured
    if (b.stock_qty !== undefined) p.stockQty = b.stock_qty as number | null
    if (b.low_stock_threshold !== undefined) p.lowStock = b.low_stock_threshold as number | null
    if (typeof b.image === 'string') p.image = b.image
    if (b.variants !== undefined) {
      if ((b.variants as VariantIn[]).length < 1) {
        return HttpResponse.json({ variants: ['ضيف وزن واحد على الأقل'] }, { status: 400 })
      }
      applyVariants(p, b.variants as VariantIn[])
    }
    return HttpResponse.json(db.serializeAdminProduct(p))
  }),

  http.delete(url('/admin/products/:id/'), ({ request, params }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const p = db.products.find((x) => x.id === Number(params.id))
    if (!p) return detail(404, 'المنتج ده مش موجود', 'not_found')
    if (db.orders.some((o) => o.lines.some((l) => l.name === p.name))) {
      p.isAvailable = false
      p.isArchived = true
    } else {
      db.products = db.products.filter((x) => x.id !== p.id)
    }
    return new HttpResponse(null, { status: 204 })
  }),

  // ---- offers ----
  http.get(url('/admin/offers/'), ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    return HttpResponse.json(db.offers.map((o) => db.serializeAdminOffer(o)))
  }),

  http.post(url('/admin/offers/'), async ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const b = (await request.json()) as AdminOfferInput
    const errors = validateOffer(b)
    if (Object.keys(errors).length) return HttpResponse.json(errors, { status: 400 })
    const offer: DbOffer = {
      id: db.nextId('offer'),
      type: b.type,
      name: b.name,
      description: '',
      value: 0,
      target: null,
      bundle_items: [],
      bundle_price: null,
      old_price: null,
      min_order: null,
      starts_at: new Date().toISOString(),
      ends_at: null,
      is_featured: false,
      is_active: true,
    }
    applyOffer(offer, b)
    db.offers.push(offer)
    return HttpResponse.json(db.serializeAdminOffer(offer), { status: 201 })
  }),

  http.patch(url('/admin/offers/:id/'), async ({ request, params }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const offer = db.offers.find((o) => o.id === Number(params.id))
    if (!offer) return detail(404, 'العرض ده مش موجود', 'not_found')
    const b = (await request.json()) as Partial<AdminOfferInput>
    applyOffer(offer, b)
    return HttpResponse.json(db.serializeAdminOffer(offer))
  }),

  http.delete(url('/admin/offers/:id/'), ({ request, params }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    db.offers = db.offers.filter((o) => o.id !== Number(params.id))
    return new HttpResponse(null, { status: 204 })
  }),

  // ---- customers ----
  http.get(url('/admin/customers/'), ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    return HttpResponse.json(
      paginate(request, db.customers(new URL(request.url).searchParams.get('q') ?? undefined)),
    )
  }),

  http.get(url('/admin/customers/:id/orders/'), ({ request, params }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const own = db.orders
      .filter((o) => o.userId === Number(params.id))
      .sort((a, b) => b.created_at.localeCompare(a.created_at))
    return HttpResponse.json(
      paginate(
        request,
        own.map((o) => db.serializeAdminOrder(o)),
      ),
    )
  }),

  // ---- staff ----
  http.get(url('/admin/staff/'), ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const staff = db.users
      .filter((u) => u.is_staff)
      .map((u) => ({ id: u.id, name: u.name, phone: u.phone, date_joined: u.created_at }))
    return HttpResponse.json(paginate(request, staff))
  }),

  http.post(url('/admin/staff/'), async ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const b = (await request.json()) as { name?: string; phone?: string; password?: string }
    const errors: Record<string, string[]> = {}
    const name = (b.name ?? '').trim()
    const password = b.password ?? ''
    if (name.length < 2 || name.length > 80) errors.name = ['الاسم لازم يكون حرفين على الأقل']
    if (!isValidPhone(b.phone ?? ''))
      errors.phone = ['اكتب رقم موبايل مصري صحيح (11 رقم يبدأ بـ 01)']
    if (password.length < 8) errors.password = ['كلمة السر لازم تكون 8 حروف على الأقل']
    else if (/^\d+$/.test(password)) errors.password = ['كلمة السر مينفعش تكون أرقام بس']
    if (Object.keys(errors).length) return HttpResponse.json(errors, { status: 400 })
    const phone = normalizePhone(b.phone!)
    if (db.users.some((u) => u.phone === phone)) {
      return detail(409, 'الرقم ده مسجل قبل كده', 'phone_exists')
    }
    const user = {
      id: db.nextId('user'),
      name,
      phone,
      email: '',
      default_address: '',
      area: '',
      is_staff: true,
      password,
      created_at: new Date().toISOString(),
    }
    db.users.push(user)
    return HttpResponse.json(
      { id: user.id, name, phone, date_joined: user.created_at },
      { status: 201 },
    )
  }),

  http.post(url('/admin/me/password/'), async ({ request }) => {
    const auth = requireStaff(request)
    if ('error' in auth) return auth.error
    const b = (await request.json()) as { current_password?: string; new_password?: string }
    const next = b.new_password ?? ''
    if (b.current_password !== auth.user.password) {
      return HttpResponse.json({ current_password: ['كلمة السر الحالية غلط'] }, { status: 400 })
    }
    let err = ''
    if (next.length < 8) err = 'كلمة السر لازم تكون 8 حروف على الأقل'
    else if (/^\d+$/.test(next)) err = 'كلمة السر مينفعش تكون أرقام بس'
    else if (next === b.current_password) err = 'كلمة السر الجديدة لازم تكون مختلفة عن الحالية'
    if (err) return HttpResponse.json({ new_password: [err] }, { status: 400 })
    auth.user.password = next
    return new HttpResponse(null, { status: 204 })
  }),
]

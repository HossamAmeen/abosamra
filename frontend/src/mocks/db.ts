import type {
  AdminCustomer,
  AdminOffer,
  AdminOrder,
  AdminProduct,
  Offer,
  Order,
  OrderStatus,
  Product,
  Quote,
  QuoteRequest,
  QuoteWarning,
  ShopSettings,
  User,
  Variant,
} from '@/types/api'
import { normalizePhone } from '@/utils/phone'
import { previewTotals, type PreviewLine } from '@/utils/pricing'
import { categories, seedOffers, seedProducts, settings as seedSettings } from './data'

interface DbVariant {
  id: number
  label: string
  price: number
  compare: number | null
  isDefault: boolean
  stockFactor?: number
}
export interface DbProduct {
  id: number
  slug: string
  name: string
  categorySlug: string
  description: string
  image: string | null
  isAvailable: boolean
  isFeatured: boolean
  isArchived: boolean
  stockQty: number | null
  lowStock: number | null
  stockUnit: string
  variants: DbVariant[]
}
export interface DbUser extends User {
  password?: string
  created_at: string
}
export interface DbOrder extends Order {
  userId: number
  stockUsage: { productId: number; qty: number }[]
}
export interface DbOffer extends Offer {
  is_active: boolean
}

export const MOCK_ADMIN = { phone: '01099999999', password: 'admin123' }

class MockDb {
  settings!: ShopSettings
  products!: DbProduct[]
  offers!: DbOffer[]
  users!: DbUser[]
  orders!: DbOrder[]
  nextIds!: Record<string, number>

  constructor() {
    this.reset()
  }

  nextId(key: string): number {
    return this.nextIds[key]++
  }

  reset(now = new Date()): void {
    this.settings = { ...seedSettings }
    this.nextIds = { product: 1, variant: 1, offer: 4, user: 102, order: 1001, orderRow: 1 }
    this.products = seedProducts.map((sp) => {
      const id = this.nextId('product')
      return {
        id,
        slug: sp.slug,
        name: sp.name,
        categorySlug: sp.category,
        description: sp.description,
        image: null,
        isAvailable: true,
        isFeatured: !!sp.featured,
        isArchived: false,
        stockQty: sp.stock?.qty ?? null,
        lowStock: sp.stock?.low ?? null,
        stockUnit: sp.stock?.unit ?? '',
        variants: sp.variants.map((v, i) => ({
          id: this.nextId('variant'),
          label: v.label,
          price: v.price,
          compare: v.compare ?? null,
          isDefault: i === 0,
        })),
      }
    })
    this.offers = seedOffers(now).map((o) => ({ ...o, is_active: true }))
    const bundle = this.offers.find((o) => o.id === 2)!
    bundle.bundle_items = ['ينسون', 'كركديه', 'عسل نحل طبيعي'].map((name) => {
      const p = this.products.find((x) => x.name === name)!
      return {
        variant_id: p.variants[0].id,
        name: name === 'عسل نحل طبيعي' ? 'عسل نحل' : name,
        qty: 1,
      }
    })
    bundle.old_price = bundle.bundle_items.reduce(
      (s, i) => s + (this.variantById(i.variant_id)?.variant.price ?? 0) * i.qty,
      0,
    )
    const mk = (id: number, name: string, phone: string, email: string, addr: string): DbUser => ({
      id,
      name,
      phone,
      email,
      default_address: addr,
      area: '',
      is_staff: false,
      created_at: new Date(now.getTime() - 3 * 86400000).toISOString(),
    })
    this.users = [
      {
        id: 1,
        name: 'أبو سمرة',
        phone: MOCK_ADMIN.phone,
        email: '',
        default_address: '',
        area: '',
        is_staff: true,
        password: MOCK_ADMIN.password,
        created_at: now.toISOString(),
      },
      mk(
        100,
        'محمد أحمد',
        '01012345678',
        'mohamed@example.com',
        'المعادي، شارع 9، عمارة 12 الدور 3',
      ),
      mk(101, 'سارة علي', '01123456789', '', 'مدينة نصر، شارع عباس العقاد، عمارة 5'),
    ]
    this.orders = []
    const seed: [number, number, OrderStatus, number, number][] = [
      [100, 1, 'new', 6, 1],
      [101, 9, 'preparing', 45, 2],
      [100, 10, 'delivered', 26 * 60, 1],
    ]
    for (const [userId, variantId, status, minutesAgo, qty] of seed) {
      const q = this.computeQuote({ items: [{ variant_id: variantId, qty }], bundles: [] })
      const o = this.buildOrder(
        this.users.find((u) => u.id === userId)!,
        q,
        this.users.find((u) => u.id === userId)!.default_address,
        '',
        '',
      )
      o.status = status
      o.created_at = new Date(now.getTime() - minutesAgo * 60000).toISOString()
    }
  }

  // ---- lookups ----
  variantById(id: number): { product: DbProduct; variant: DbVariant } | null {
    for (const product of this.products) {
      const variant = product.variants.find((v) => v.id === id)
      if (variant) return { product, variant }
    }
    return null
  }
  categoryBySlug(slug: string) {
    return categories.find((c) => c.slug === slug)
  }

  isLive(o: DbOffer, now = new Date()): boolean {
    return (
      o.is_active &&
      new Date(o.starts_at) <= now &&
      (o.ends_at == null || new Date(o.ends_at) >= now)
    )
  }
  liveOffers(now = new Date()): DbOffer[] {
    return this.offers.filter((o) => this.isLive(o, now))
  }

  // ---- serializers ----
  serializeVariant(v: DbVariant): Variant {
    return {
      id: v.id,
      label: v.label,
      price: v.price,
      old_price: v.compare,
      is_default: v.isDefault,
    }
  }
  serializeOffer(o: DbOffer): Offer {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { is_active, ...rest } = o
    return rest
  }
  serializeProduct(p: DbProduct): Product {
    const cat = this.categoryBySlug(p.categorySlug)!
    const best = this.bestPercentageOffer(p)
    const variants = [...p.variants].sort((a, b) => Number(b.isDefault) - Number(a.isDefault))
    return {
      id: p.id,
      slug: p.slug,
      name: p.name,
      description: p.description,
      category: { slug: cat.slug, name: cat.name, color: cat.color, icon: cat.icon },
      image: p.image,
      is_available: p.isAvailable,
      is_featured: p.isFeatured,
      variants: variants.map((v) => this.serializeVariant(v)),
      active_offer: best
        ? { id: best.id, name: best.name, type: best.type, value: best.value }
        : null,
    }
  }
  serializeAdminProduct(p: DbProduct): AdminProduct {
    const cat = this.categoryBySlug(p.categorySlug)!
    const ordered = [...p.variants].sort((a, b) => Number(b.isDefault) - Number(a.isDefault))
    return {
      id: p.id,
      slug: p.slug,
      name: p.name,
      description: p.description,
      image: p.image,
      category: { id: cat.id, slug: cat.slug, name: cat.name, color: cat.color, icon: cat.icon },
      is_available: p.isAvailable,
      is_featured: p.isFeatured,
      // DRF serializes model decimals as strings.
      stock_qty: p.stockQty == null ? null : p.stockQty.toFixed(3),
      low_stock_threshold: p.lowStock == null ? null : p.lowStock.toFixed(3),
      stock_unit: p.stockUnit,
      variants: ordered.map((v, i) => ({
        id: v.id,
        label: v.label,
        price: v.price,
        old_price: v.compare,
        stock_factor: v.stockFactor ?? 1,
        is_default: v.isDefault,
        order: i,
      })),
      created_at: '2026-11-01T09:00:00Z',
      updated_at: '2026-11-01T09:00:00Z',
    }
  }
  serializeAdminOffer(o: DbOffer): AdminOffer {
    return {
      ...o,
      value: o.type === 'percentage' ? o.value : null,
      created_at: o.starts_at,
    }
  }
  serializeOrder(o: DbOrder): Order {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { userId, stockUsage, ...rest } = o
    return rest
  }
  serializeAdminOrder(o: DbOrder): AdminOrder {
    return {
      ...this.serializeOrder(o),
      items_summary: o.lines.map((l) => (l.qty > 1 ? `${l.name} ×${l.qty}` : l.name)).join('، '),
    }
  }

  bestPercentageOffer(p: DbProduct): DbOffer | null {
    let best: DbOffer | null = null
    for (const o of this.liveOffers()) {
      if (o.type !== 'percentage' || !o.target) continue
      const hit =
        o.target.kind === 'all' ||
        (o.target.kind === 'category' && o.target.slug === p.categorySlug) ||
        (o.target.kind === 'products' && o.target.ids.includes(p.id))
      if (hit && (!best || o.value > best.value)) best = o
    }
    return best
  }

  // ---- pricing (BSPEC 4.3) ----
  computeQuote(req: QuoteRequest, now = new Date()): Quote {
    const warnings: QuoteWarning[] = []
    const lines: Quote['lines'] = []
    const preview: PreviewLine[] = []

    const checkVariant = (variantId: number, qty: number) => {
      const hit = this.variantById(variantId)
      if (!hit) {
        warnings.push({ variant_id: variantId, code: 'not_found', detail: 'المنتج ده مش موجود' })
        return null
      }
      const { product } = hit
      const inactiveCat = !this.categoryBySlug(product.categorySlug)
      if (!product.isAvailable || product.isArchived || inactiveCat) {
        warnings.push({
          variant_id: variantId,
          code: 'unavailable',
          detail: `${product.name} خلصان حالياً`,
        })
        return null
      }
      if (product.stockQty != null && qty > product.stockQty) {
        warnings.push({
          variant_id: variantId,
          code: 'insufficient_stock',
          detail: `${product.name} المتاح منه ${product.stockQty} بس`,
        })
        return null
      }
      return hit
    }

    for (const it of req.items) {
      const hit = checkVariant(it.variant_id, it.qty)
      if (!hit) continue
      const { product, variant } = hit
      lines.push({
        variant_id: variant.id,
        offer_id: null,
        name: product.name,
        unit_label: variant.label,
        qty: it.qty,
        unit_price: variant.price,
        line_total: variant.price * it.qty,
      })
      preview.push({
        variantId: variant.id,
        productId: product.id,
        categorySlug: product.categorySlug,
        unitPrice: variant.price,
        qty: it.qty,
      })
    }

    for (const b of req.bundles) {
      const offer = this.offers.find((o) => o.id === b.offer_id && o.type === 'bundle')
      if (!offer || !this.isLive(offer, now)) {
        warnings.push({
          variant_id: null,
          offer_id: b.offer_id,
          code: 'offer_expired',
          detail: 'العرض ده خلص',
        })
        continue
      }
      let ok = true
      for (const bi of offer.bundle_items) {
        if (!checkVariant(bi.variant_id, bi.qty * b.qty)) ok = false
      }
      if (!ok) continue
      const price = offer.bundle_price ?? 0
      lines.push({
        variant_id: null,
        offer_id: offer.id,
        name: offer.name,
        unit_label: 'باكدج',
        qty: b.qty,
        unit_price: price,
        line_total: price * b.qty,
      })
      preview.push({
        variantId: null,
        productId: null,
        unitPrice: price,
        qty: b.qty,
        bundleOfferId: offer.id,
      })
    }

    const totals = previewTotals(
      preview,
      this.liveOffers(now).map((o) => this.serializeOffer(o)),
      this.settings,
    )
    return { lines, ...totals, warnings }
  }

  // ---- orders ----
  buildOrder(
    user: User,
    quote: Quote,
    address: string,
    area: string,
    notes: string,
    itemNotes: Record<number, string> = {},
  ): DbOrder {
    const stockUsage: DbOrder['stockUsage'] = []
    const useStock = (variantId: number, qty: number) => {
      const hit = this.variantById(variantId)
      if (hit && hit.product.stockQty != null) {
        hit.product.stockQty -= qty
        stockUsage.push({ productId: hit.product.id, qty })
      }
    }
    for (const l of quote.lines) {
      if (l.variant_id != null) useStock(l.variant_id, l.qty)
      else {
        const offer = this.offers.find((o) => o.id === l.offer_id)
        offer?.bundle_items.forEach((bi) => useStock(bi.variant_id, bi.qty * l.qty))
      }
    }
    const order: DbOrder = {
      id: this.nextId('orderRow'),
      number: this.nextId('order'),
      status: 'new',
      created_at: new Date().toISOString(),
      customer: { name: user.name, phone: user.phone },
      address,
      area,
      notes,
      lines: quote.lines.map((l) => ({
        name: l.name,
        unit_label: l.unit_label,
        qty: l.qty,
        unit_price: l.unit_price,
        line_total: l.line_total,
        note: (l.variant_id != null ? itemNotes[l.variant_id] : '') ?? '',
      })),
      subtotal: quote.subtotal,
      discounts: quote.discounts,
      discount_total: quote.discount_total,
      delivery_fee: quote.delivery_fee,
      total: quote.total,
      payment_method: 'cod',
      userId: user.id,
      stockUsage,
    }
    this.orders.unshift(order)
    return order
  }

  restoreStock(order: DbOrder): void {
    for (const u of order.stockUsage) {
      const p = this.products.find((x) => x.id === u.productId)
      if (p && p.stockQty != null) p.stockQty += u.qty
    }
    order.stockUsage = []
  }

  customers(q?: string): AdminCustomer[] {
    const needle = q?.trim().toLowerCase() ?? ''
    const phoneNeedle = needle ? normalizePhone(needle) : ''
    return this.users
      .filter((u) => !u.is_staff)
      .filter(
        (u) =>
          !needle ||
          u.name.toLowerCase().includes(needle) ||
          (phoneNeedle && u.phone.includes(phoneNeedle)),
      )
      .map((u) => {
        const own = this.orders.filter((o) => o.userId === u.id)
        const paid = own.filter((o) => o.status !== 'cancelled')
        return {
          id: u.id,
          name: u.name,
          phone: u.phone,
          email: u.email,
          default_address: u.default_address,
          area: u.area,
          date_joined: u.created_at,
          orders_count: own.length,
          total_spent: paid.reduce((s, o) => s + o.total, 0),
          last_order_at:
            own
              .map((o) => o.created_at)
              .sort()
              .reverse()[0] ?? null,
        }
      })
      .sort((a, b) => (b.last_order_at ?? '').localeCompare(a.last_order_at ?? ''))
  }
}

export const db = new MockDb()

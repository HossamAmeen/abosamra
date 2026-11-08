import { describe, expect, it } from 'vitest'
import { getCategories, getOffers, getProducts } from '@/api/catalog'
import { quoteCart } from '@/api/cart'
import { createOrder, getMyOrders } from '@/api/orders'
import { adminLogin, login, register } from '@/api/auth'
import { setOrderStatus } from '@/api/admin/orders'
import { getDashboard } from '@/api/admin/dashboard'
import { listAdminCustomers } from '@/api/admin/customers'
import { listAdminOffers } from '@/api/admin/offers'
import { apiError } from '@/api/client'
import { registerTokenBridge } from '@/api/tokens'
import { db, MOCK_ADMIN } from './db'

function as(token: string) {
  registerTokenBridge({
    getAccess: () => token,
    getRefresh: () => null,
    setTokens: () => {},
    onAuthFailure: () => {},
  })
}

async function ids() {
  const { results } = await getProducts()
  const v = (name: string, label?: string) => {
    const p = results.find((x) => x.name === name)!
    return (label ? p.variants.find((x) => x.label === label) : p.variants[0])!.id
  }
  return {
    kumun: v('كمون مطحون', 'ربع كيلو'),
    pepper: v('فلفل أسود حب'),
    honey: v('عسل نحل طبيعي'),
  }
}

describe('mock catalog', () => {
  it('serves 16 products, 6 categories, 3 offers', async () => {
    expect((await getProducts()).count).toBe(16)
    expect(await getCategories()).toHaveLength(6)
    expect(await getOffers()).toHaveLength(3)
  })
  it('filters by category, q, featured, discounted', async () => {
    expect((await getProducts({ category: 'spices' })).count).toBe(5)
    expect((await getProducts({ category: 'all' })).count).toBe(16)
    expect((await getProducts({ q: 'كمون' })).count).toBe(1)
    expect((await getProducts({ featured: true })).count).toBe(4)
    expect((await getProducts({ discounted: true })).count).toBeGreaterThan(5)
  })
  it('spices products carry the active 15% offer; default variant first', async () => {
    const { results } = await getProducts({ category: 'spices' })
    expect(results.every((p) => p.active_offer?.value === 15)).toBe(true)
    expect(results[0].variants[0].is_default).toBe(true)
  })
})

describe('mock quote (reference case)', () => {
  it('435 / 32 / 30 / 433 / 97', async () => {
    const i = await ids()
    const q = await quoteCart({
      items: [
        { variant_id: i.kumun, qty: 2 },
        { variant_id: i.pepper, qty: 1 },
        { variant_id: i.honey, qty: 1 },
      ],
      bundles: [],
    })
    expect(q.subtotal).toBe(435)
    expect(q.discount_total).toBe(32)
    expect(q.delivery_fee).toBe(30)
    expect(q.total).toBe(433)
    expect(q.free_delivery_remaining).toBe(97)
    expect(q.warnings).toEqual([])
  })
  it('warnings: not_found, unavailable, offer_expired', async () => {
    const i = await ids()
    db.products.find((p) => p.name === 'كمون مطحون')!.isAvailable = false
    const q = await quoteCart({
      items: [
        { variant_id: i.kumun, qty: 1 },
        { variant_id: 9999, qty: 1 },
      ],
      bundles: [{ offer_id: 99, qty: 1 }],
    })
    expect(q.warnings.map((w) => w.code).sort()).toEqual([
      'not_found',
      'offer_expired',
      'unavailable',
    ])
    expect(q.lines).toHaveLength(0)
  })
})

describe('mock auth + orders', () => {
  it('register 201, duplicate 409 phone_exists, login 404 not_found, staff login 404', async () => {
    const res = await register({ name: 'علي حسن', phone: '٠١٠٠٠٠٠٠٠٠١' })
    expect(res.user.phone).toBe('01000000001')
    const dup = await register({ name: 'علي حسن', phone: '01000000001' }).catch(apiError)
    expect(dup).toMatchObject({ status: 409, body: { code: 'phone_exists' } })
    expect(await login('01000000009').catch(apiError)).toMatchObject({
      status: 404,
      body: { code: 'not_found' },
    })
    expect(await login(MOCK_ADMIN.phone).catch(apiError)).toMatchObject({ status: 404 })
  })
  it('admin login needs the password', async () => {
    expect(await adminLogin(MOCK_ADMIN.phone, 'x').catch(apiError)).toMatchObject({ status: 401 })
    expect((await adminLogin(MOCK_ADMIN.phone, MOCK_ADMIN.password)).user.is_staff).toBe(true)
  })
  it('orders: guest 401, 409 cart_changed with fresh quote, success returns number', async () => {
    const i = await ids()
    as('')
    expect(
      await createOrder({ items: [], bundles: [], address: 'x'.repeat(12) }).catch(apiError),
    ).toMatchObject({ status: 401 })
    const { access } = await login('01012345678')
    as(access)
    db.products.find((p) => p.name === 'فلفل أسود حب')!.isAvailable = false
    const err = await createOrder({
      items: [{ variant_id: i.pepper, qty: 1 }],
      bundles: [],
      address: 'المعادي شارع 9 عمارة 1',
    }).catch(apiError)
    expect(err).toMatchObject({ status: 409, body: { code: 'cart_changed' } })
    expect((err as { body: { quote: { warnings: unknown[] } } }).body.quote.warnings).toHaveLength(
      1,
    )
    const order = await createOrder({
      items: [{ variant_id: i.kumun, qty: 2 }],
      bundles: [],
      address: 'المعادي شارع 9 عمارة 1',
    })
    expect(order.number).toBe(1004)
    expect(order.total).toBe(Math.round(order.subtotal - order.discount_total + order.delivery_fee))
    expect((await getMyOrders()).results[0].number).toBe(1004)
  })
  it('admin: transitions, invalid jump 400, cancel restores stock, dashboard', async () => {
    const i = await ids()
    const token = (await adminLogin(MOCK_ADMIN.phone, MOCK_ADMIN.password)).access
    as(token)
    const dash = await getDashboard()
    expect(dash.pending_count).toBe(1)
    const stock = () => db.products.find((p) => p.name === 'كمون مطحون')!.stockQty
    const before = stock()
    const cust = (await login('01012345678')).access
    as(cust)
    const order = await createOrder({
      items: [{ variant_id: i.kumun, qty: 3 }],
      bundles: [],
      address: 'المعادي شارع 9 عمارة 1',
    })
    expect(stock()).toBe(before! - 3)
    as(token)
    expect(await setOrderStatus(order.id, 'delivered').catch(apiError)).toMatchObject({
      status: 400,
    })
    expect((await setOrderStatus(order.id, 'preparing')).status).toBe('preparing')
    await setOrderStatus(order.id, 'cancelled')
    expect(stock()).toBe(before)
    as(cust)
    expect(await getDashboard().catch(apiError)).toMatchObject({ status: 403 })
  })

  it('admin lists: customers paginated envelope, offers plain array', async () => {
    as((await adminLogin(MOCK_ADMIN.phone, MOCK_ADMIN.password)).access)
    const customers = await listAdminCustomers()
    expect(customers).toMatchObject({ count: 2, next: null, previous: null })
    expect(customers.results[0]).toHaveProperty('orders_count')
    expect((await listAdminCustomers('سارة')).results).toHaveLength(1)
    const offers = await listAdminOffers()
    expect(Array.isArray(offers)).toBe(true)
  })
})

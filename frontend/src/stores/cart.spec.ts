import { beforeEach, describe, expect, it } from 'vitest'
import { createApp, nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import { getProducts } from '@/api/catalog'
import { useCartStore, lineKey } from './cart'
import { useCatalogStore } from './catalog'
import { useSettingsStore } from './settings'

beforeEach(() => setActivePinia(createPinia()))

async function setup() {
  const cart = useCartStore()
  const catalog = useCatalogStore()
  await Promise.all([catalog.loadOffers(), useSettingsStore().load()])
  const { results } = await getProducts()
  return { cart, catalog, results }
}

describe('cart store', () => {
  it('adds default variant, merges duplicates, counts qty', async () => {
    const { cart, results } = await setup()
    const kumun = results.find((p) => p.name === 'كمون مطحون')!
    cart.addProduct(kumun)
    cart.addProduct(kumun)
    expect(cart.lines).toHaveLength(1)
    expect(cart.count).toBe(2)
    expect(cart.qtyOfVariant(kumun.variants[0].id)).toBe(2)
  })

  it('setQty(0) removes the line; qty capped at 50', async () => {
    const { cart, results } = await setup()
    cart.addProduct(results[0])
    const key = lineKey(cart.lines[0])
    cart.setQty(key, 999)
    expect(cart.lines[0].qty).toBe(50)
    cart.decrement(key)
    expect(cart.lines[0].qty).toBe(49)
    cart.setQty(key, 0)
    expect(cart.isEmpty).toBe(true)
  })

  it('stores per-line note', async () => {
    const { cart, results } = await setup()
    cart.addProduct(results[0], undefined, 1, 'مطحون ناعم')
    expect(cart.lines[0].note).toBe('مطحون ناعم')
  })

  it('bundle is a single line keyed by offer', async () => {
    const { cart, catalog } = await setup()
    const bundle = catalog.bundleOffers[0]
    cart.addBundle(bundle)
    cart.addBundle(bundle)
    expect(cart.lines).toHaveLength(1)
    expect(cart.lines[0].qty).toBe(2)
    expect(cart.requestBody().bundles).toEqual([{ offer_id: bundle.id, qty: 2 }])
    expect(cart.requestBody().items).toEqual([])
  })

  it('client preview and server quote agree on the reference cart', async () => {
    const { cart, results } = await setup()
    const by = (n: string) => results.find((p) => p.name === n)!
    cart.addProduct(by('كمون مطحون'), by('كمون مطحون').variants[0].id, 2)
    cart.addProduct(by('فلفل أسود حب'))
    cart.addProduct(by('عسل نحل طبيعي'))
    expect(cart.preview).toMatchObject({
      subtotal: 435,
      discount_total: 32,
      delivery_fee: 30,
      total: 433,
      free_delivery_remaining: 97,
    })
    const q = await cart.revalidate()
    expect(q).toMatchObject({
      subtotal: 435,
      discount_total: 32,
      delivery_fee: 30,
      total: 433,
      free_delivery_remaining: 97,
    })
    expect(cart.totals.total).toBe(433)
    cart.increment(lineKey(cart.lines[0]))
    expect(cart.quote).toBeNull() // invalidated by edits
  })

  it('revalidate syncs changed prices and records notices for unavailable lines', async () => {
    const { cart, results } = await setup()
    const kumun = results.find((p) => p.name === 'كمون مطحون')!
    cart.addLine({
      variantId: kumun.variants[0].id,
      productId: kumun.id,
      name: kumun.name,
      unitLabel: 'ربع كيلو',
      unitPrice: 1,
      qty: 1,
    })
    cart.addLine({
      variantId: 9999,
      productId: 0,
      name: 'مجهول',
      unitLabel: 'x',
      unitPrice: 5,
      qty: 1,
    })
    await cart.revalidate()
    expect(cart.lines[0].unitPrice).toBe(60)
    expect(cart.notices.some((n) => n.includes('اتغيّر'))).toBe(true)
    expect(cart.hasBlockingWarnings).toBe(true)
  })

  it('persists only lines to localStorage (survives reload)', async () => {
    const pinia = createPinia()
    pinia.use(piniaPluginPersistedstate)
    createApp({}).use(pinia)
    setActivePinia(pinia)
    const cart = useCartStore()
    const { results } = await getProducts()
    cart.addProduct(results[0])
    await cart.revalidate()
    await nextTick()
    const saved = JSON.parse(localStorage.getItem('cart') ?? 'null')
    expect(Object.keys(saved)).toEqual(['lines'])
    expect(saved.lines[0].qty).toBe(1)
  })
})

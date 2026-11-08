import { describe, expect, it } from 'vitest'
import type { Offer } from '@/types/api'
import { previewTotals, type PreviewLine } from './pricing'

const base = {
  description: '',
  bundle_items: [],
  bundle_price: null,
  old_price: null,
  min_order: null,
  starts_at: '',
  ends_at: null,
  is_featured: false,
}
const pct = (id: number, value: number, target: Offer['target']): Offer => ({
  ...base,
  id,
  type: 'percentage',
  name: `خصم ${value}`,
  value,
  target,
})
const spices15 = pct(1, 15, { kind: 'category', slug: 'spices', ids: [] })
const settings = { delivery_fee: 30, free_delivery_threshold: 500 }
const line = (over: Partial<PreviewLine>): PreviewLine => ({
  variantId: 1,
  productId: 1,
  categorySlug: 'spices',
  unitPrice: 100,
  qty: 1,
  ...over,
})

describe('previewTotals', () => {
  it('reference case 435 / 32 / 30 / 433 / 97', () => {
    const t = previewTotals(
      [
        line({ variantId: 1, productId: 1, unitPrice: 60, qty: 2 }),
        line({ variantId: 4, productId: 2, unitPrice: 95 }),
        line({ variantId: 12, productId: 10, categorySlug: 'honey', unitPrice: 220 }),
      ],
      [spices15],
      settings,
    )
    expect(t.subtotal).toBe(435)
    expect(t.discount_total).toBe(32)
    expect(t.discounts).toEqual([{ offer_id: 1, label: 'خصم 15', amount: 32 }])
    expect(t.delivery_fee).toBe(30)
    expect(t.total).toBe(433)
    expect(t.free_delivery_remaining).toBe(97)
  })

  it('best single percentage wins (no stacking)', () => {
    const t = previewTotals(
      [line({ unitPrice: 200 })],
      [spices15, pct(2, 25, { kind: 'all', slug: null, ids: [] })],
      settings,
    )
    expect(t.discounts).toHaveLength(1)
    expect(t.discounts[0].offer_id).toBe(2)
    expect(t.discount_total).toBe(50)
  })

  it('bundle lines never get percentage discounts', () => {
    const t = previewTotals(
      [line({ variantId: null, productId: null, bundleOfferId: 9, unitPrice: 290 })],
      [spices15],
      settings,
    )
    expect(t.discount_total).toBe(0)
    expect(t.total).toBe(320)
  })

  it('free delivery exactly at threshold, remaining 0', () => {
    const t = previewTotals([line({ categorySlug: 'honey', unitPrice: 500 })], [], settings)
    expect(t.delivery_fee).toBe(0)
    expect(t.free_delivery_remaining).toBe(0)
    expect(t.total).toBe(500)
  })

  it('free_delivery offer lowers the threshold', () => {
    const fd: Offer = {
      ...base,
      id: 3,
      type: 'free_delivery',
      name: 'x',
      value: 0,
      target: null,
      min_order: 300,
    }
    const t = previewTotals([line({ categorySlug: 'honey', unitPrice: 300 })], [fd], settings)
    expect(t.free_delivery_threshold).toBe(300)
    expect(t.delivery_fee).toBe(0)
  })

  it('product-targeted offers only match listed ids', () => {
    const o = pct(4, 10, { kind: 'products', slug: null, ids: [7] })
    const t = previewTotals(
      [
        line({ productId: 7, unitPrice: 100 }),
        line({ variantId: 2, productId: 8, unitPrice: 100 }),
      ],
      [o],
      settings,
    )
    expect(t.discount_total).toBe(10)
  })
})

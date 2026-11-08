import type { Offer, Quote, QuoteDiscount } from '@/types/api'
import { roundPounds } from './money'

export interface PreviewLine {
  variantId: number | null
  productId: number | null
  categorySlug?: string | null
  unitPrice: number
  qty: number
  bundleOfferId?: number | null
}

export interface PreviewSettings {
  delivery_fee: number
  free_delivery_threshold: number
}

export type PreviewTotals = Pick<
  Quote,
  | 'subtotal'
  | 'discounts'
  | 'discount_total'
  | 'delivery_fee'
  | 'free_delivery_threshold'
  | 'free_delivery_remaining'
  | 'total'
>

function offerMatches(offer: Offer, line: PreviewLine): boolean {
  const t = offer.target
  if (!t) return false
  if (t.kind === 'all') return true
  if (t.kind === 'category') return !!line.categorySlug && t.slug === line.categorySlug
  return line.productId != null && t.ids.includes(line.productId)
}

/** Client-side preview mirroring BSPEC 4.3. The server quote is always the source of truth. */
export function previewTotals(
  lines: PreviewLine[],
  liveOffers: Offer[],
  settings: PreviewSettings,
): PreviewTotals {
  const subtotal = lines.reduce((s, l) => s + l.unitPrice * l.qty, 0)
  const percentage = liveOffers.filter((o) => o.type === 'percentage')
  const perOffer = new Map<number, number>()
  for (const line of lines) {
    if (line.bundleOfferId) continue
    let best: Offer | null = null
    for (const o of percentage) {
      if (offerMatches(o, line) && (!best || o.value > best.value)) best = o
    }
    if (best) {
      const raw = (line.unitPrice * line.qty * best.value) / 100
      perOffer.set(best.id, (perOffer.get(best.id) ?? 0) + raw)
    }
  }
  const discounts: QuoteDiscount[] = []
  for (const [offerId, raw] of perOffer) {
    const offer = percentage.find((o) => o.id === offerId)!
    discounts.push({ offer_id: offerId, label: offer.name, amount: roundPounds(raw) })
  }
  const discount_total = discounts.reduce((s, d) => s + d.amount, 0)
  const minOrders = liveOffers
    .filter((o) => o.type === 'free_delivery' && o.min_order != null)
    .map((o) => o.min_order as number)
  const threshold = Math.min(settings.free_delivery_threshold, ...minOrders)
  const after = subtotal - discount_total
  const delivery_fee = lines.length > 0 && after >= threshold ? 0 : settings.delivery_fee
  return {
    subtotal,
    discounts,
    discount_total,
    delivery_fee,
    free_delivery_threshold: threshold,
    free_delivery_remaining: Math.max(0, threshold - after),
    total: subtotal - discount_total + delivery_fee,
  }
}

import type { Product, Variant } from '@/types/api'

export const defaultVariant = (p: Product): Variant | undefined =>
  p.variants.find((v) => v.is_default) ?? p.variants[0]

/**
 * Card badge percent, derived from the variant's old price (design: only products with a
 * struck-through old price carry a badge; the offer % is shown on the product page itself).
 */
/** Offer-only caption percent (e.g. 15 for a "15% on spices" offer); 0 when none applies. */
export function offerPercent(p: Product): number {
  return p.active_offer?.type === 'percentage' ? Math.round(p.active_offer.value) : 0
}

/** True for products listed under "عروض النهاردة": old price on the variant or an active offer. */
export const isDiscounted = (p: Product): boolean => discountPercent(p) > 0 || !!p.active_offer

export function discountPercent(p: Product, v: Variant | undefined = defaultVariant(p)): number {
  if (v?.old_price && v.old_price > v.price) {
    return Math.round(((v.old_price - v.price) / v.old_price) * 100)
  }
  return 0
}

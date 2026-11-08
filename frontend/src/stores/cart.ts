import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { quoteCart } from '@/api/cart'
import type { Product, Quote, QuoteWarning, Offer } from '@/types/api'
import { previewTotals, type PreviewLine } from '@/utils/pricing'
import { useCatalogStore } from './catalog'
import { useSettingsStore } from './settings'

export interface CartLine {
  variantId: number | null
  productId: number | null
  categorySlug?: string | null
  name: string
  unitLabel: string
  unitPrice: number
  qty: number
  note: string
  bundleOfferId?: number | null
}

export const MAX_QTY = 50

export const lineKey = (l: Pick<CartLine, 'variantId' | 'bundleOfferId'>) =>
  l.bundleOfferId ? `b:${l.bundleOfferId}` : `v:${l.variantId}`

export const useCartStore = defineStore(
  'cart',
  () => {
    const lines = ref<CartLine[]>([])
    const quote = ref<Quote | null>(null)
    const quoting = ref(false)
    const quoteError = ref(false)
    /** Human-readable notices produced by the last re-validation (price change, unavailable...). */
    const notices = ref<string[]>([])

    const count = computed(() => lines.value.reduce((s, l) => s + l.qty, 0))
    const isEmpty = computed(() => lines.value.length === 0)
    const warnings = computed<QuoteWarning[]>(() => quote.value?.warnings ?? [])
    const hasBlockingWarnings = computed(() => warnings.value.length > 0)

    /** Client-side preview. UI should prefer `quote` once available. */
    const preview = computed(() => {
      const settings = useSettingsStore()
      const catalog = useCatalogStore()
      return previewTotals(lines.value as PreviewLine[], catalog.offers, {
        delivery_fee: settings.deliveryFee,
        free_delivery_threshold: settings.freeDeliveryThreshold,
      })
    })
    /** Server quote if present and fresh, else the preview. */
    const totals = computed(() => quote.value ?? { ...preview.value, lines: [], warnings: [] })

    function find(key: string) {
      return lines.value.find((l) => lineKey(l) === key)
    }
    function qtyOfVariant(variantId: number): number {
      return lines.value.find((l) => l.bundleOfferId == null && l.variantId === variantId)?.qty ?? 0
    }

    function invalidate() {
      quote.value = null
    }

    function addLine(input: Omit<CartLine, 'qty' | 'note'> & { qty?: number; note?: string }) {
      const qty = input.qty ?? 1
      const existing = find(lineKey(input))
      if (existing) {
        existing.qty = Math.min(MAX_QTY, existing.qty + qty)
        if (input.note) existing.note = input.note
      } else {
        lines.value.push({ ...input, qty: Math.min(MAX_QTY, qty), note: input.note ?? '' })
      }
      invalidate()
    }

    function addProduct(product: Product, variantId?: number, qty = 1, note = '') {
      const variant =
        product.variants.find((v) => v.id === variantId) ??
        product.variants.find((v) => v.is_default) ??
        product.variants[0]
      if (!variant) return
      addLine({
        variantId: variant.id,
        productId: product.id,
        categorySlug: product.category.slug,
        name: product.name,
        unitLabel: variant.label,
        unitPrice: variant.price,
        qty,
        note,
      })
    }

    function addBundle(offer: Offer, qty = 1) {
      addLine({
        variantId: null,
        productId: null,
        name: offer.name,
        unitLabel: 'باكدج',
        unitPrice: offer.bundle_price ?? 0,
        qty,
        bundleOfferId: offer.id,
      })
    }

    /** qty <= 0 removes the line. */
    function setQty(key: string, qty: number) {
      const l = find(key)
      if (!l) return
      if (qty <= 0) return remove(key)
      l.qty = Math.min(MAX_QTY, Math.floor(qty))
      invalidate()
    }
    function increment(key: string) {
      const l = find(key)
      if (l) setQty(key, l.qty + 1)
    }
    function decrement(key: string) {
      const l = find(key)
      if (l) setQty(key, l.qty - 1)
    }
    function remove(key: string) {
      lines.value = lines.value.filter((l) => lineKey(l) !== key)
      invalidate()
    }
    function setNote(key: string, note: string) {
      const l = find(key)
      if (l) l.note = note
    }
    function clear() {
      lines.value = []
      quote.value = null
      notices.value = []
    }

    /** POST /orders/ body: same as the quote body plus the optional per-line `note` (max 200). */
    function orderBody() {
      const body = requestBody()
      return {
        ...body,
        items: body.items.map((it) => {
          const note = lines.value.find((l) => l.variantId === it.variant_id)?.note.trim()
          return note ? { ...it, note: note.slice(0, 200) } : it
        }),
      }
    }

    function requestBody() {
      return {
        items: lines.value
          .filter((l) => l.bundleOfferId == null && l.variantId != null)
          .map((l) => ({ variant_id: l.variantId as number, qty: l.qty })),
        bundles: lines.value
          .filter((l) => l.bundleOfferId != null)
          .map((l) => ({ offer_id: l.bundleOfferId as number, qty: l.qty })),
      }
    }

    /**
     * Re-validate against POST /cart/quote/ (on cart open and before checkout).
     * Syncs changed unit prices into the lines and records notices.
     */
    async function revalidate(): Promise<Quote | null> {
      if (lines.value.length === 0) {
        quote.value = null
        notices.value = []
        return null
      }
      quoting.value = true
      quoteError.value = false
      try {
        const q = await quoteCart(requestBody())
        const next: string[] = []
        for (const l of lines.value) {
          const ql = q.lines.find((x) =>
            l.bundleOfferId ? x.offer_id === l.bundleOfferId : x.variant_id === l.variantId,
          )
          if (ql && ql.unit_price !== l.unitPrice) {
            next.push(`سعر ${l.name} اتغيّر`)
            l.unitPrice = ql.unit_price
          }
        }
        for (const w of q.warnings) next.push(w.detail)
        notices.value = next
        quote.value = q
        return q
      } catch {
        quoteError.value = true
        return null
      } finally {
        quoting.value = false
      }
    }

    /** Accept a fresh quote returned with a 409 cart_changed. */
    function applyQuote(q: Quote) {
      for (const l of lines.value) {
        const ql = q.lines.find((x) =>
          l.bundleOfferId ? x.offer_id === l.bundleOfferId : x.variant_id === l.variantId,
        )
        if (ql) l.unitPrice = ql.unit_price
      }
      quote.value = q
      notices.value = q.warnings.map((w) => w.detail)
    }

    return {
      lines,
      quote,
      quoting,
      quoteError,
      notices,
      count,
      isEmpty,
      warnings,
      hasBlockingWarnings,
      preview,
      totals,
      qtyOfVariant,
      addLine,
      addProduct,
      addBundle,
      setQty,
      increment,
      decrement,
      remove,
      setNote,
      orderBody,
      clear,
      requestBody,
      revalidate,
      applyQuote,
    }
  },
  { persist: { pick: ['lines'] } },
)

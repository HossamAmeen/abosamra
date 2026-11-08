<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import DiscountBadge from '@/components/ui/DiscountBadge.vue'
import PriceTag from '@/components/ui/PriceTag.vue'
import ProductThumb from '@/components/ui/ProductThumb.vue'
import QtyStepper from '@/components/ui/QtyStepper.vue'
import { useToast } from '@/composables/useToast'
import { useCartStore } from '@/stores/cart'
import type { Product } from '@/types/api'
import { defaultVariant, discountPercent, offerPercent } from '@/utils/product'

const props = withDefaults(defineProps<{ product: Product; mode?: 'round' | 'stepper' }>(), {
  mode: 'round',
})
const cart = useCartStore()
const toast = useToast()

const variant = computed(() => defaultVariant(props.product))
const percent = computed(() => discountPercent(props.product, variant.value))
const offerOnly = computed(() => (percent.value > 0 ? 0 : offerPercent(props.product)))
const qty = computed({
  get: () => (variant.value ? cart.qtyOfVariant(variant.value.id) : 0),
  set: (q: number) => {
    if (!variant.value) return
    const key = `v:${variant.value.id}`
    if (q <= 0) cart.remove(key)
    else if (cart.qtyOfVariant(variant.value.id) > 0) cart.setQty(key, q)
    else cart.addProduct(props.product, variant.value.id, q)
  },
})

function add() {
  if (!variant.value || !props.product.is_available) return
  cart.addProduct(props.product, variant.value.id)
  toast.show('اتضاف للسلة')
}
</script>

<template>
  <article class="flex flex-col gap-2 rounded-card border border-border bg-surface p-2">
    <!-- Same destination as the name link below: hidden from assistive tech and the tab order so the
         card exposes one link whose accessible name is its visible text (WCAG 2.5.3, label in name). -->
    <RouterLink :to="`/products/${product.slug}`" class="block" tabindex="-1" aria-hidden="true">
      <div class="h-24">
        <ProductThumb
          :image="product.image"
          :alt="product.name"
          :tint="product.category.color"
          :icon="product.category.icon"
        >
          <DiscountBadge v-if="percent > 0" :percent="percent" />
          <span
            v-if="!product.is_available"
            class="absolute end-1.5 top-1.5 rounded-full bg-danger-soft px-2 py-0.5 text-[12px] font-bold text-danger"
          >
            خلصان
          </span>
        </ProductThumb>
      </div>
    </RouterLink>
    <div class="flex min-w-0 flex-col">
      <RouterLink
        :to="`/products/${product.slug}`"
        class="truncate text-[15px] font-bold text-ink"
        >{{ product.name }}</RouterLink
      >
      <span v-if="variant" class="text-[12px] font-semibold text-muted">{{ variant.label }}</span>
      <span v-if="offerOnly" class="text-[12px] font-bold text-success">خصم {{ offerOnly }}%</span>
    </div>
    <div v-if="variant" class="mt-auto flex items-center justify-between gap-2">
      <PriceTag :price="variant.price" :old-price="variant.old_price" />
      <button
        v-if="mode === 'round'"
        type="button"
        class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary text-ink disabled:bg-disabled disabled:text-disabled-text"
        :aria-label="`أضف ${product.name} للسلة`"
        :disabled="!product.is_available"
        @click="add"
      >
        <Plus class="h-6 w-6" :stroke-width="2.5" aria-hidden="true" />
      </button>
    </div>
    <template v-if="mode === 'stepper' && variant">
      <button
        v-if="qty === 0"
        type="button"
        class="inline-flex h-11 w-full items-center justify-center gap-1.5 rounded-full bg-primary text-[14px] font-bold text-ink disabled:bg-disabled disabled:text-disabled-text"
        :disabled="!product.is_available"
        @click="add"
      >
        <Plus class="h-5 w-5" :stroke-width="2.5" aria-hidden="true" />
        أضف للسلة
      </button>
      <QtyStepper v-else v-model="qty" :name="product.name" class="w-full justify-between" />
    </template>
  </article>
</template>

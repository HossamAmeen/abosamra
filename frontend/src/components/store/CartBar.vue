<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { ShoppingCart } from 'lucide-vue-next'
import { useCartStore } from '@/stores/cart'
import { formatMoney } from '@/utils/money'

const cart = useCartStore()
</script>

<template>
  <div
    v-if="!cart.isEmpty"
    class="pointer-events-none fixed inset-x-0 bottom-[calc(70px+env(safe-area-inset-bottom))] z-30 mx-auto max-w-app"
  >
    <RouterLink
      to="/cart"
      class="pointer-events-auto mx-4 mb-2.5 flex h-14 items-center justify-between rounded-card bg-ink px-4 text-on-dark"
    >
      <span class="flex items-center gap-2 text-[14px] font-bold">
        <ShoppingCart class="h-5 w-5" aria-hidden="true" />
        عرض السلة · {{ cart.count }} منتج
      </span>
      <span class="text-[17px] font-extrabold text-primary">{{
        formatMoney(cart.totals.total)
      }}</span>
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
import { formatMoney } from '@/utils/money'

defineProps<{ price: number; oldPrice?: number | null; size?: 'md' | 'lg' }>()
</script>

<template>
  <div class="flex flex-col leading-tight">
    <span :class="['font-extrabold text-ink', size === 'lg' ? 'text-[20px]' : 'text-[16px]']">
      {{ formatMoney(price) }}
    </span>
    <span
      v-if="oldPrice && oldPrice > price"
      class="text-[12px] font-semibold text-muted line-through"
    >
      {{ formatMoney(oldPrice) }}
    </span>
  </div>
</template>

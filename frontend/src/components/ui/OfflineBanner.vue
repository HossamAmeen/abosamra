<script setup lang="ts">
import { useOnline } from '@/composables/useOnline'

const { online } = useOnline()
</script>

<template>
  <div
    v-if="!online"
    role="status"
    class="bg-ink px-4 py-2 text-center text-[13px] font-bold text-on-dark"
  >
    انت أوفلاين دلوقتي — هتقدر تتفرج بس الطلب محتاج نت
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

defineProps<{ title: string; to?: string; linkLabel?: string }>()
</script>

<template>
  <div class="flex items-center justify-between">
    <h2 class="text-[18px] font-extrabold text-ink">{{ title }}</h2>
    <RouterLink
      v-if="to"
      :to="to"
      class="inline-flex min-h-[44px] items-center text-[14px] font-bold text-link hover:text-link-hover"
    >
      {{ linkLabel ?? 'عرض الكل' }}
    </RouterLink>
  </div>
</template>

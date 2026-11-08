<script setup lang="ts">
import { ChevronRight } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'

defineProps<{ title: string; backTo?: string }>()
const emit = defineEmits<{ back: [] }>()
</script>

<template>
  <header class="flex items-center gap-3 border-b border-border bg-surface px-4 py-2">
    <RouterLink
      v-if="backTo"
      :to="backTo"
      aria-label="رجوع"
      class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary-tint text-brand-deep"
    >
      <ChevronRight class="h-6 w-6" aria-hidden="true" />
    </RouterLink>
    <button
      v-else
      type="button"
      aria-label="رجوع"
      class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary-tint text-brand-deep"
      @click="emit('back')"
    >
      <ChevronRight class="h-6 w-6" aria-hidden="true" />
    </button>
    <h1 class="flex-1 truncate text-[20px] font-extrabold text-ink">{{ title }}</h1>
    <slot name="action" />
  </header>
</template>

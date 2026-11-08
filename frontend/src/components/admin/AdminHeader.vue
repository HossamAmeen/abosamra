<script setup lang="ts">
import { Eye } from 'lucide-vue-next'
import AppLogo from '@/components/ui/AppLogo.vue'

defineProps<{ title?: string; caption?: string }>()
</script>

<template>
  <div>
    <header
      class="flex items-center justify-between gap-3 border-b border-border bg-surface px-4 py-2"
    >
      <AppLogo variant="admin" :size="40" />
      <slot name="action">
        <a
          href="/"
          target="_blank"
          rel="noopener"
          class="inline-flex h-11 items-center gap-1.5 rounded-field bg-primary-tint px-3 text-[14px] font-bold text-brand-deep"
        >
          <Eye class="h-5 w-5" aria-hidden="true" />
          شوف المتجر
        </a>
      </slot>
    </header>
    <div v-if="title" class="px-4 pt-3">
      <h1 class="text-[22px] font-extrabold text-ink">{{ title }}</h1>
      <p v-if="caption" class="text-[13px] font-semibold text-muted">{{ caption }}</p>
    </div>
  </div>
</template>

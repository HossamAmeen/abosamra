<script setup lang="ts">
import { Eye, ShieldCheck } from 'lucide-vue-next'
import AppLogo from '@/components/ui/AppLogo.vue'

defineProps<{ title?: string; caption?: string }>()
</script>

<template>
  <div>
    <header
      class="flex items-center justify-between gap-3 border-b border-border bg-surface px-4 py-2"
    >
      <AppLogo variant="admin" :size="40" />
      <div class="flex items-center gap-2">
        <RouterLink
          to="/admin/staff"
          aria-label="الأدمنز"
          title="الأدمنز"
          class="flex h-11 w-11 items-center justify-center rounded-field bg-primary-tint text-brand-deep"
        >
          <ShieldCheck class="h-5 w-5" aria-hidden="true" />
        </RouterLink>
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
      </div>
    </header>
    <div v-if="title" class="px-4 pt-3">
      <h1 class="text-[22px] font-extrabold text-ink">{{ title }}</h1>
      <p v-if="caption" class="text-[13px] font-semibold text-muted">{{ caption }}</p>
    </div>
  </div>
</template>

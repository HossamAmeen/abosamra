<script setup lang="ts">
import { useToast } from '@/composables/useToast'

const { toasts, dismiss } = useToast()
</script>

<template>
  <div
    class="pointer-events-none fixed inset-x-0 bottom-24 z-50 mx-auto flex max-w-app flex-col items-center gap-2 px-4"
  >
    <div
      v-for="t in toasts"
      :key="t.id"
      role="status"
      class="pointer-events-auto flex w-full items-center justify-between gap-3 rounded-field bg-success px-4 py-3 text-[14px] font-bold text-white"
    >
      <span>{{ t.message }}</span>
      <button
        v-if="t.actionLabel"
        type="button"
        class="min-h-[44px] rounded-field px-3 font-extrabold underline"
        @click="(t.onAction?.(), dismiss(t.id))"
      >
        {{ t.actionLabel }}
      </button>
    </div>
  </div>
</template>

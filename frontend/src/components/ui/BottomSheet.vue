<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { X } from 'lucide-vue-next'

defineProps<{ title: string }>()
const emit = defineEmits<{ close: [] }>()
const panel = ref<HTMLElement | null>(null)

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}
onMounted(() => {
  document.addEventListener('keydown', onKey)
  panel.value?.querySelector<HTMLElement>('button')?.focus()
})
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-end justify-center bg-ink/50"
    @click.self="emit('close')"
  >
    <div
      ref="panel"
      role="dialog"
      aria-modal="true"
      :aria-label="title"
      class="max-h-[88vh] w-full max-w-admin overflow-y-auto rounded-t-band bg-surface p-4 pb-8"
    >
      <div class="mb-3 flex items-center justify-between gap-3">
        <h2 class="text-[18px] font-extrabold text-ink">{{ title }}</h2>
        <button
          type="button"
          aria-label="إغلاق"
          class="flex h-11 w-11 items-center justify-center rounded-full bg-primary-tint text-brand-deep"
          @click="emit('close')"
        >
          <X class="h-5 w-5" aria-hidden="true" />
        </button>
      </div>
      <slot />
    </div>
  </div>
</template>

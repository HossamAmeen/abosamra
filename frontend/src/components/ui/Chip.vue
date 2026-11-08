<script setup lang="ts">
withDefaults(defineProps<{ selected?: boolean; size?: 'store' | 'admin' }>(), { size: 'store' })
</script>

<template>
  <button
    type="button"
    :aria-pressed="selected"
    :class="[
      'shrink-0 rounded-full border px-4 text-[14px] font-bold whitespace-nowrap',
      size === 'admin' ? 'h-10 min-h-[40px]' : 'h-11 min-h-[44px]',
      selected ? 'border-ink bg-ink text-on-dark' : 'border-input-border bg-white text-ink',
    ]"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Loader2 } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'dark' | 'danger' | 'danger-text' | 'ghost'
    size?: 'lg' | 'md'
    block?: boolean
    loading?: boolean
    disabled?: boolean
    type?: 'button' | 'submit' | 'reset'
  }>(),
  { variant: 'primary', size: 'lg', block: false, type: 'button' },
)

const classes = computed(() => {
  const base =
    'inline-flex items-center justify-center gap-2 select-none transition-colors min-h-[44px]'
  const size =
    props.size === 'lg'
      ? 'h-[52px] rounded-btn px-5 text-[16px] font-extrabold'
      : 'h-11 rounded-field px-4 text-[14px] font-bold'
  const inactive = props.disabled || props.loading
  const look = inactive
    ? props.variant === 'danger-text' || props.variant === 'ghost'
      ? 'text-muted cursor-not-allowed'
      : 'bg-disabled text-disabled-text cursor-not-allowed'
    : {
        primary: 'bg-primary text-ink',
        secondary: 'bg-primary-tint text-brand-deep',
        dark: 'bg-ink text-on-dark',
        danger: 'bg-danger text-white',
        'danger-text': 'bg-transparent text-danger',
        ghost: 'bg-transparent text-link hover:text-link-hover',
      }[props.variant]
  return [base, size, look, props.block ? 'w-full' : '']
})
</script>

<template>
  <button
    :type="type"
    :class="classes"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
  >
    <Loader2 v-if="loading" class="h-5 w-5 animate-spin" aria-hidden="true" />
    <slot v-else name="icon" />
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = withDefaults(defineProps<{ variant?: 'dark' | 'soft' | 'success'; to?: string }>(), {
  variant: 'dark',
})
const tag = computed(() => (props.to ? RouterLink : 'div'))
const tone = computed(
  () =>
    ({
      dark: 'bg-ink text-on-dark',
      soft: 'bg-primary-soft text-ink',
      success: 'bg-success-soft text-success-strong',
    })[props.variant],
)
</script>

<template>
  <component
    :is="tag"
    :to="to"
    :class="['flex items-center justify-between gap-3 rounded-banner p-[18px]', tone]"
  >
    <div class="flex min-w-0 flex-1 flex-col items-start gap-2">
      <slot />
    </div>
    <slot name="end" />
  </component>
</template>

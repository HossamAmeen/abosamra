<script setup lang="ts">
import { computed } from 'vue'
import { Leaf } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    size?: number
    variant?: 'store' | 'admin'
    onOrange?: boolean
    iconOnly?: boolean
  }>(),
  { size: 44, variant: 'store' },
)
const iconPx = computed(() => Math.round(props.size * 0.55))
</script>

<template>
  <div class="flex items-center gap-2.5">
    <span
      class="flex shrink-0 items-center justify-center rounded-full"
      :class="onOrange ? 'bg-white' : 'bg-primary'"
      :style="{ width: size + 'px', height: size + 'px' }"
    >
      <Leaf
        class="text-ink"
        :style="{ width: iconPx + 'px', height: iconPx + 'px' }"
        aria-hidden="true"
      />
    </span>
    <span v-if="!iconOnly" class="flex flex-col leading-tight">
      <span class="text-[20px] font-extrabold text-ink">أبو سمرة</span>
      <span class="text-[12px] font-semibold text-ink-2">
        {{ variant === 'admin' ? 'لوحة التحكم' : 'عطارة وبهارات' }}
      </span>
    </span>
  </div>
</template>

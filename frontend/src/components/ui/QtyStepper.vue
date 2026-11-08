<script setup lang="ts">
import { Minus, Plus } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{ modelValue: number; min?: number; max?: number; name?: string }>(),
  { min: 0, max: 50 },
)
const emit = defineEmits<{ 'update:modelValue': [value: number] }>()

const inc = () => props.modelValue < props.max && emit('update:modelValue', props.modelValue + 1)
const dec = () => props.modelValue > props.min && emit('update:modelValue', props.modelValue - 1)
</script>

<template>
  <div class="inline-flex items-center rounded-full bg-primary-soft" role="group">
    <!-- DOM order: "+" first, so in RTL it sits on the right (start) -->
    <button
      type="button"
      class="flex h-11 w-11 items-center justify-center rounded-full bg-primary text-ink disabled:opacity-50"
      :aria-label="name ? `زوّد ${name}` : 'زيادة الكمية'"
      :disabled="modelValue >= max"
      data-test="inc"
      @click="inc"
    >
      <Plus class="h-5 w-5" :stroke-width="2.5" aria-hidden="true" />
    </button>
    <span class="min-w-[48px] text-center text-[17px] font-extrabold text-ink" aria-live="polite">
      {{ modelValue }}
    </span>
    <button
      type="button"
      class="flex h-11 w-11 items-center justify-center rounded-full bg-white text-ink"
      :aria-label="name ? `قلّل ${name}` : 'تقليل الكمية'"
      :disabled="modelValue <= min"
      data-test="dec"
      @click="dec"
    >
      <Minus class="h-5 w-5" :stroke-width="2.5" aria-hidden="true" />
    </button>
  </div>
</template>

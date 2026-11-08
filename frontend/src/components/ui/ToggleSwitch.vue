<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: boolean
    labelOn?: string
    labelOff?: string
    ariaLabel?: string
    disabled?: boolean
  }>(),
  { labelOn: 'متوفر', labelOff: 'خلصان' },
)
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

function toggle() {
  if (!props.disabled) emit('update:modelValue', !props.modelValue)
}
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :aria-label="ariaLabel"
    :disabled="disabled"
    class="inline-flex min-h-[44px] min-w-[44px] items-center gap-2"
    @click="toggle"
  >
    <span
      :class="[
        'flex h-7 w-12 shrink-0 items-center rounded-full px-[3px] transition-colors',
        modelValue ? 'justify-end bg-success' : 'justify-start bg-switch-off',
      ]"
    >
      <span class="h-[22px] w-[22px] rounded-full bg-white" />
    </span>
    <span :class="['text-[12px] font-bold', modelValue ? 'text-success' : 'text-muted']">
      {{ modelValue ? labelOn : labelOff }}
    </span>
  </button>
</template>

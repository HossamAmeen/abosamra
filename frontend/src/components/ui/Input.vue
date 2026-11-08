<script setup lang="ts">
import { computed, useId } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue?: string | number
    label?: string
    optional?: boolean
    error?: string
    type?: string
    placeholder?: string
    multiline?: boolean
    rows?: number
    ltr?: boolean
    inputmode?: 'text' | 'numeric' | 'tel' | 'email' | 'decimal' | 'search'
    autocomplete?: string
    ariaLabel?: string
    id?: string
  }>(),
  { type: 'text', rows: 2 },
)
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const autoId = useId()
const inputId = computed(() => props.id ?? `in-${autoId}`)
const errId = computed(() => `${inputId.value}-err`)

function onInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLInputElement | HTMLTextAreaElement).value)
}

const fieldClass = computed(() => [
  'w-full bg-white border rounded-field px-[14px] text-[15px] text-ink placeholder:text-muted/70',
  props.error ? 'border-danger' : 'border-input-border',
  props.multiline ? 'py-3 leading-[1.7] resize-none' : 'h-[50px]',
  props.ltr ? 'text-right' : '',
])
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="inputId" class="text-[14px] font-bold text-ink">
      {{ label }}
      <span v-if="optional" class="font-semibold text-muted">(اختياري)</span>
    </label>
    <textarea
      v-if="multiline"
      :id="inputId"
      :class="fieldClass"
      :value="modelValue"
      :rows="rows"
      :placeholder="placeholder"
      :aria-label="label ? undefined : ariaLabel"
      :aria-invalid="!!error || undefined"
      :aria-describedby="error ? errId : undefined"
      @input="onInput"
    />
    <input
      v-else
      :id="inputId"
      :class="fieldClass"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :inputmode="inputmode"
      :autocomplete="autocomplete"
      :dir="ltr ? 'ltr' : undefined"
      :aria-label="label ? undefined : ariaLabel"
      :aria-invalid="!!error || undefined"
      :aria-describedby="error ? errId : undefined"
      @input="onInput"
    />
    <p v-if="error" :id="errId" class="text-[13px] font-semibold text-danger" role="alert">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'

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

const isPassword = computed(() => props.type === 'password')
const revealed = ref(false)
const inputType = computed(() => (isPassword.value && revealed.value ? 'text' : props.type))

function onInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLInputElement | HTMLTextAreaElement).value)
}

const fieldClass = computed(() => [
  'w-full bg-white border rounded-field px-[14px] text-[15px] text-ink placeholder:text-muted/70',
  props.error ? 'border-danger' : 'border-input-border',
  props.multiline ? 'py-3 leading-[1.7] resize-none' : 'h-[50px]',
  props.ltr ? 'text-right' : '',
  isPassword.value ? 'pl-12' : '',
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
    <div v-else class="relative">
      <input
        :id="inputId"
        :class="fieldClass"
        :type="inputType"
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
      <button
        v-if="isPassword"
        type="button"
        class="absolute left-1 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-field text-ink-2"
        :aria-label="revealed ? 'اخفي كلمة السر' : 'اظهر كلمة السر'"
        :aria-pressed="revealed"
        :aria-controls="inputId"
        @click="revealed = !revealed"
      >
        <EyeOff v-if="revealed" class="h-5 w-5" aria-hidden="true" />
        <Eye v-else class="h-5 w-5" aria-hidden="true" />
      </button>
    </div>
    <p v-if="error" :id="errId" class="text-[13px] font-semibold text-danger" role="alert">
      {{ error }}
    </p>
  </div>
</template>

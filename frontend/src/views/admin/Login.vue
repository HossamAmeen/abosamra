<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiError } from '@/api/client'
import AppLogo from '@/components/ui/AppLogo.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { usePhone } from '@/composables/usePhone'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const phoneUtil = usePhone()

const phone = ref('')
const password = ref('')
const submitting = ref(false)
const touched = ref(false)
const formError = ref('')

const phoneError = computed(() =>
  touched.value && !phoneUtil.isValid(phone.value) ? 'اكتب رقم موبايل صحيح' : '',
)
const passwordError = computed(() => (touched.value && !password.value ? 'اكتب كلمة السر' : ''))

async function submit() {
  touched.value = true
  formError.value = ''
  if (!phoneUtil.isValid(phone.value) || !password.value || submitting.value) return
  submitting.value = true
  try {
    await auth.adminLogin(phone.value, password.value)
    if (!auth.isStaff) {
      auth.clear()
      formError.value = 'الحساب ده مش حساب إدارة'
      return
    }
    const next = typeof route.query.next === 'string' ? route.query.next : ''
    router.replace(next.startsWith('/admin') ? next : '/admin')
  } catch (e) {
    const { status, body } = apiError(e)
    formError.value =
      status === 429
        ? 'محاولات كتير، استنى شوية وجرّب تاني'
        : status === 0
          ? 'مفيش اتصال بالنت، جرّب تاني'
          : (body.detail ?? 'الرقم أو كلمة السر غلط')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="mx-auto flex min-h-screen max-w-app flex-col justify-center gap-6 bg-bg px-4 py-10">
    <div class="flex flex-col items-center gap-2">
      <AppLogo variant="admin" :size="84" icon-only />
      <h1 class="text-[22px] font-extrabold text-ink">دخول لوحة التحكم</h1>
      <p class="text-[14px] font-semibold text-ink-2">أبو سمرة - لوحة التحكم</p>
    </div>
    <form
      class="flex flex-col gap-4 rounded-card bg-surface p-4"
      novalidate
      @submit.prevent="submit"
    >
      <Input
        v-model="phone"
        label="رقم الموبايل"
        type="tel"
        inputmode="tel"
        autocomplete="username"
        placeholder="01012345678"
        ltr
        :error="phoneError"
      />
      <Input
        v-model="password"
        label="كلمة السر"
        type="password"
        autocomplete="current-password"
        ltr
        :error="passwordError"
      />
      <p v-if="formError" class="text-[14px] font-bold text-danger" role="alert">{{ formError }}</p>
      <Button type="submit" block :loading="submitting">دخول</Button>
    </form>
  </main>
</template>

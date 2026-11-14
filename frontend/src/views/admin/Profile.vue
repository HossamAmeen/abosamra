<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronLeft, LogOut, ShieldCheck } from 'lucide-vue-next'
import { changeAdminPassword } from '@/api/auth'
import { apiError } from '@/api/client'
import AdminHeader from '@/components/admin/AdminHeader.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import { APP_VERSION } from '@/composables/useAppUpdate'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { formatPhoneDisplay } from '@/utils/phone'

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

const networkError = (status: number) =>
  status === 0 ? 'مفيش اتصال بالنت، جرّب تاني' : 'حصلت مشكلة، جرّب تاني'
const firstError = (body: unknown, key: string) =>
  (body as Record<string, string[] | undefined>)[key]?.[0]

// ---- name ----
const name = ref(auth.user?.name ?? '')
const nameTouched = ref(false)
const savingName = ref(false)
const nameServerError = ref('')
const nameError = computed(() => {
  if (nameServerError.value) return nameServerError.value
  return nameTouched.value && name.value.trim().length < 2 ? 'الاسم لازم يكون حرفين على الأقل' : ''
})
const nameChanged = computed(() => name.value.trim() !== (auth.user?.name ?? ''))

async function saveName() {
  nameTouched.value = true
  nameServerError.value = ''
  if (nameError.value || !nameChanged.value || savingName.value) return
  savingName.value = true
  try {
    await auth.updateProfile({ name: name.value.trim() })
    name.value = auth.user?.name ?? name.value
    toast.show('الاسم اتحفظ')
  } catch (e) {
    const { status, body } = apiError(e)
    nameServerError.value = firstError(body, 'name') ?? networkError(status)
  } finally {
    savingName.value = false
  }
}

// ---- password ----
const pw = reactive({ current: '', next: '' })
const pwTouched = ref(false)
const changingPw = ref(false)
const pwServer = ref<{ current?: string; next?: string; form?: string }>({})
const pwErrors = computed(() => {
  const e = { ...pwServer.value }
  if (!pwTouched.value) return e
  if (!pw.current) e.current ??= 'اكتب كلمة السر الحالية'
  if (pw.next.length < 8) e.next ??= 'كلمة السر لازم تكون 8 حروف على الأقل'
  else if (/^\d+$/.test(pw.next)) e.next ??= 'كلمة السر مينفعش تكون أرقام بس'
  return e
})

async function changePassword() {
  pwTouched.value = true
  pwServer.value = {}
  const { current, next } = pwErrors.value
  if (current || next || changingPw.value) return
  changingPw.value = true
  try {
    await changeAdminPassword({ current_password: pw.current, new_password: pw.next })
    Object.assign(pw, { current: '', next: '' })
    pwTouched.value = false
    toast.show('كلمة السر اتغيرت')
  } catch (e) {
    const { status, body } = apiError(e)
    if (status === 400) {
      pwServer.value = {
        current: firstError(body, 'current_password'),
        next: firstError(body, 'new_password'),
      }
    } else {
      pwServer.value = {
        form: status === 429 ? 'محاولات كتير، استنى شوية وجرّب تاني' : networkError(status),
      }
    }
  } finally {
    changingPw.value = false
  }
}

// ---- logout ----
const loggingOut = ref(false)
async function logout() {
  loggingOut.value = true
  await auth.logout()
  await router.replace({ name: 'admin-login' })
}
</script>

<template>
  <div>
    <AdminHeader title="حسابي" />

    <div class="flex flex-col gap-4 p-4">
      <section class="flex items-center gap-3 rounded-card border border-border bg-surface p-3">
        <span
          class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-primary-soft text-[22px] font-extrabold text-brand-deep"
          aria-hidden="true"
        >
          {{ auth.user?.name.trim().charAt(0) }}
        </span>
        <span class="flex min-w-0 flex-col">
          <span class="text-[17px] font-extrabold text-ink">{{ auth.user?.name }}</span>
          <span dir="ltr" class="self-start text-[14px] text-ink-2">
            {{ formatPhoneDisplay(auth.user?.phone ?? '') }}
          </span>
        </span>
      </section>

      <form
        class="flex flex-col gap-3 rounded-card border border-border bg-surface p-4"
        aria-labelledby="profile-name-h"
        novalidate
        @submit.prevent="saveName"
      >
        <h2 id="profile-name-h" class="text-[17px] font-extrabold text-ink">الاسم</h2>
        <Input
          v-model="name"
          aria-label="الاسم"
          autocomplete="name"
          :error="nameError"
          @update:model-value="nameServerError = ''"
        />
        <Button type="submit" size="md" :disabled="!nameChanged" :loading="savingName">
          حفظ الاسم
        </Button>
      </form>

      <form
        class="flex flex-col gap-3 rounded-card border border-border bg-surface p-4"
        aria-labelledby="profile-pw-h"
        novalidate
        @submit.prevent="changePassword"
      >
        <h2 id="profile-pw-h" class="text-[17px] font-extrabold text-ink">تغيير كلمة السر</h2>
        <Input
          v-model="pw.current"
          label="كلمة السر الحالية"
          type="password"
          autocomplete="current-password"
          ltr
          :error="pwErrors.current"
        />
        <Input
          v-model="pw.next"
          label="كلمة السر الجديدة"
          type="password"
          autocomplete="new-password"
          ltr
          :error="pwErrors.next"
        />
        <p v-if="pwErrors.form" class="text-[14px] font-bold text-danger" role="alert">
          {{ pwErrors.form }}
        </p>
        <Button type="submit" size="md" :loading="changingPw">تغيير كلمة السر</Button>
      </form>

      <RouterLink
        to="/admin/staff"
        class="flex min-h-[56px] items-center gap-3 rounded-card border border-border bg-surface px-4 text-[15px] font-bold text-ink"
      >
        <ShieldCheck class="h-5 w-5 text-brand-deep" aria-hidden="true" />
        <span class="flex-1">الأدمنز</span>
        <ChevronLeft class="h-5 w-5 text-muted" aria-hidden="true" />
      </RouterLink>

      <Button variant="danger" block :loading="loggingOut" @click="logout">
        <LogOut class="h-5 w-5" aria-hidden="true" />
        تسجيل خروج
      </Button>

      <p class="text-center text-[12px] font-semibold text-muted">
        إصدار التطبيق {{ APP_VERSION }}
      </p>
    </div>
  </div>
</template>

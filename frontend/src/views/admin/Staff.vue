<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Plus, ShieldCheck } from 'lucide-vue-next'
import { apiError } from '@/api/client'
import { createAdminStaff, listAdminStaff } from '@/api/admin/staff'
import AdminHeader from '@/components/admin/AdminHeader.vue'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import Button from '@/components/ui/Button.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Input from '@/components/ui/Input.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import { usePhone } from '@/composables/usePhone'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import type { AdminStaff, AdminStaffInput } from '@/types/api'
import { formatDayMonth } from '@/utils/date'
import { formatPhoneDisplay } from '@/utils/phone'

const auth = useAuthStore()
const toast = useToast()
const phoneUtil = usePhone()

const staff = ref<AdminStaff[]>([])
const loading = ref(true)
const failed = ref(false)

async function load() {
  loading.value = true
  failed.value = false
  try {
    staff.value = (await listAdminStaff()).results
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}
load()

// ---- add form ----
const formOpen = ref(false)
const form = reactive<AdminStaffInput>({ name: '', phone: '', password: '' })
const touched = ref(false)
const submitting = ref(false)
const serverErrors = ref<Partial<Record<keyof AdminStaffInput, string>>>({})
const formError = ref('')

const errors = computed(() => {
  const e: Partial<Record<keyof AdminStaffInput, string>> = { ...serverErrors.value }
  if (!touched.value) return e
  if (form.name.trim().length < 2) e.name ??= 'الاسم لازم يكون حرفين على الأقل'
  if (!phoneUtil.isValid(form.phone)) e.phone ??= 'اكتب رقم موبايل صحيح'
  if (form.password.length < 8) e.password ??= 'كلمة السر لازم تكون 8 حروف على الأقل'
  else if (/^\d+$/.test(form.password)) e.password ??= 'كلمة السر مينفعش تكون أرقام بس'
  return e
})

function openForm() {
  Object.assign(form, { name: '', phone: '', password: '' })
  touched.value = false
  serverErrors.value = {}
  formError.value = ''
  formOpen.value = true
}

async function submit() {
  touched.value = true
  serverErrors.value = {}
  formError.value = ''
  if (Object.keys(errors.value).length || submitting.value) return
  submitting.value = true
  try {
    const created = await createAdminStaff({ ...form, name: form.name.trim() })
    staff.value = [...staff.value, created]
    formOpen.value = false
    toast.show(`تمت إضافة ${created.name} كأدمن`)
  } catch (e) {
    const { status, body } = apiError(e)
    if (status === 400) {
      const fields = body as Record<string, string[] | undefined>
      serverErrors.value = {
        name: fields.name?.[0],
        phone: fields.phone?.[0],
        password: fields.password?.[0],
      }
      for (const k of Object.keys(serverErrors.value) as (keyof AdminStaffInput)[]) {
        if (!serverErrors.value[k]) delete serverErrors.value[k]
      }
    } else if (status === 409) {
      serverErrors.value = { phone: body.detail ?? 'الرقم ده مسجل قبل كده' }
    } else {
      formError.value = status === 0 ? 'مفيش اتصال بالنت، جرّب تاني' : 'حصلت مشكلة، جرّب تاني'
    }
  } finally {
    submitting.value = false
  }
}

const initial = (name: string) => name.trim().charAt(0)
</script>

<template>
  <div>
    <AdminHeader title="الأدمنز" caption="الناس اللي تقدر تدخل لوحة التحكم" />

    <div class="flex flex-col gap-2 p-4">
      <Button block @click="openForm">
        <Plus class="h-5 w-5" aria-hidden="true" />
        إضافة أدمن
      </Button>

      <template v-if="loading">
        <Skeleton v-for="i in 2" :key="i" class="h-[72px]" />
      </template>
      <p v-else-if="failed" class="text-[14px] font-bold text-danger" role="alert">
        مقدرناش نحمّل الأدمنز
        <button type="button" class="min-h-[44px] ms-2 text-link underline" @click="load">
          حاول تاني
        </button>
      </p>
      <EmptyState v-else-if="!staff.length" :icon="ShieldCheck" text="مفيش أدمنز لسه" />
      <ul v-else class="flex flex-col gap-2">
        <li
          v-for="s in staff"
          :key="s.id"
          class="flex items-center gap-3 rounded-card border border-border bg-surface p-3"
        >
          <span
            class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary-soft text-[18px] font-extrabold text-brand-deep"
            aria-hidden="true"
          >
            {{ initial(s.name) }}
          </span>
          <span class="flex min-w-0 flex-1 flex-col">
            <span class="text-[15px] font-extrabold text-ink">
              {{ s.name }}
              <span v-if="s.id === auth.user?.id" class="text-[13px] font-semibold text-muted">
                (إنت)
              </span>
            </span>
            <span dir="ltr" class="self-start text-[14px] text-ink-2">
              {{ formatPhoneDisplay(s.phone) }}
            </span>
            <span class="text-[13px] text-muted">من {{ formatDayMonth(s.date_joined) }}</span>
          </span>
        </li>
      </ul>
    </div>

    <BottomSheet v-if="formOpen" title="إضافة أدمن" @close="formOpen = false">
      <form class="flex flex-col gap-4" novalidate @submit.prevent="submit">
        <Input v-model="form.name" label="الاسم" autocomplete="off" :error="errors.name" />
        <Input
          v-model="form.phone"
          label="رقم الموبايل"
          type="tel"
          inputmode="tel"
          autocomplete="off"
          placeholder="01012345678"
          ltr
          :error="errors.phone"
        />
        <Input
          v-model="form.password"
          label="كلمة السر"
          type="password"
          autocomplete="new-password"
          ltr
          :error="errors.password"
        />
        <p class="text-[13px] text-muted">
          الأدمن الجديد هيقدر يدخل لوحة التحكم بالرقم وكلمة السر دول، وليه نفس صلاحياتك.
        </p>
        <p v-if="formError" class="text-[14px] font-bold text-danger" role="alert">
          {{ formError }}
        </p>
        <Button type="submit" block :loading="submitting">إضافة</Button>
      </form>
    </BottomSheet>
  </div>
</template>

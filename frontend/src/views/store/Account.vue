<script setup lang="ts">
import { APP_VERSION } from '@/composables/useAppUpdate'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiError } from '@/api/client'
import { getMyOrders } from '@/api/orders'
import AppLogo from '@/components/ui/AppLogo.vue'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import TopBar from '@/components/ui/TopBar.vue'
import { usePhone } from '@/composables/usePhone'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'
import type { Order } from '@/types/api'
import { formatDayMonth } from '@/utils/date'
import { formatMoney } from '@/utils/money'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const cart = useCartStore()
const phoneUtil = usePhone()

const mode = ref<'register' | 'login'>('register')
const name = ref('')
const phone = ref('')
const email = ref('')
const submitting = ref(false)
const info = ref('')
const errors = ref<{ name?: string; phone?: string; email?: string; form?: string }>({})

const next = computed(() => (typeof route.query.next === 'string' ? route.query.next : ''))
const fromCheckout = computed(() => next.value === 'checkout')

const nameValid = computed(() => name.value.trim().length >= 2)
const phoneValid = computed(() => phoneUtil.isValid(phone.value))
const emailValid = computed(() => !email.value.trim() || /^\S+@\S+\.\S+$/.test(email.value.trim()))
const valid = computed(() =>
  mode.value === 'register'
    ? nameValid.value && phoneValid.value && emailValid.value
    : phoneValid.value,
)

function switchMode(m: 'register' | 'login') {
  mode.value = m
  errors.value = {}
  info.value = ''
}

function afterAuth() {
  if (fromCheckout.value) router.replace({ name: 'cart', query: { resume: '1' } })
  else if (next.value.startsWith('/')) router.replace(next.value)
}

async function submit() {
  if (!valid.value || submitting.value) return
  submitting.value = true
  errors.value = {}
  info.value = ''
  try {
    if (mode.value === 'register') {
      await auth.register({
        name: name.value.trim(),
        phone: phone.value,
        email: email.value.trim() || undefined,
      })
    } else {
      await auth.login(phone.value)
    }
    afterAuth()
  } catch (e) {
    const { status, body } = apiError(e)
    if (mode.value === 'register' && status === 409 && body.code === 'phone_exists') {
      phone.value = phoneUtil.normalize(phone.value)
      switchMode('login')
      info.value = 'الرقم ده عنده حساب، ادخل بيه'
    } else if (mode.value === 'login' && status === 404) {
      phone.value = phoneUtil.normalize(phone.value)
      switchMode('register')
      errors.value = { form: 'مفيش حساب بالرقم ده' }
    } else if (status === 400) {
      const first = (k: string) => (Array.isArray(body[k]) ? String(body[k][0]) : undefined)
      errors.value = { name: first('name'), phone: first('phone'), email: first('email') }
      if (!errors.value.name && !errors.value.phone && !errors.value.email) {
        errors.value.form = body.detail ?? 'حصلت مشكلة، حاول تاني'
      }
    } else {
      errors.value = { form: body.detail ?? 'حصلت مشكلة، حاول تاني' }
    }
  } finally {
    submitting.value = false
  }
}

// ---- logged-in view ----
const orders = ref<Order[]>([])
const ordersLoading = ref(false)
const ordersFailed = ref(false)
async function loadOrders() {
  if (!auth.isLoggedIn) return
  ordersLoading.value = true
  ordersFailed.value = false
  try {
    orders.value = (await getMyOrders()).results
  } catch {
    ordersFailed.value = true
  } finally {
    ordersLoading.value = false
  }
}
onMounted(loadOrders)
watch(() => auth.isLoggedIn, loadOrders)

async function logout() {
  await auth.logout()
  orders.value = []
  switchMode('register')
}
</script>

<template>
  <div>
    <TopBar title="حسابي" @back="router.back()" />

    <!-- logged in -->
    <div v-if="auth.isLoggedIn && auth.user" class="flex flex-col gap-4 px-4 py-5">
      <section class="flex flex-col gap-1 rounded-card border border-border bg-surface p-4">
        <h2 class="text-[18px] font-extrabold text-ink">{{ auth.user.name }}</h2>
        <p dir="ltr" class="text-end text-[15px] font-semibold text-ink-2">{{ auth.user.phone }}</p>
        <p v-if="auth.user.email" dir="ltr" class="text-end text-[14px] text-muted">
          {{ auth.user.email }}
        </p>
      </section>

      <section class="flex flex-col gap-2">
        <h2 class="text-[18px] font-extrabold text-ink">طلباتي</h2>
        <Skeleton v-if="ordersLoading" class="h-16 rounded-card" />
        <div v-else-if="ordersFailed" class="text-center">
          <p class="text-[14px] font-semibold text-danger">حصلت مشكلة في تحميل الطلبات</p>
          <button type="button" class="min-h-[44px] font-bold text-link" @click="loadOrders">
            حاول تاني
          </button>
        </div>
        <p v-else-if="!orders.length" class="py-4 text-center text-[14px] font-semibold text-muted">
          لسه معملتش أي طلب
        </p>
        <ul v-else class="flex flex-col gap-2.5">
          <li
            v-for="o in orders"
            :key="o.id"
            class="flex items-center justify-between gap-3 rounded-card border border-border bg-surface p-3.5"
          >
            <div class="flex flex-col">
              <span class="text-[15px] font-extrabold text-ink">طلب #{{ o.number }}</span>
              <span class="text-[12px] font-semibold text-muted">{{
                formatDayMonth(o.created_at)
              }}</span>
            </div>
            <div class="flex flex-col items-end gap-1">
              <span class="text-[15px] font-extrabold text-ink">{{ formatMoney(o.total) }}</span>
              <StatusPill :status="o.status" />
            </div>
          </li>
        </ul>
      </section>

      <button
        type="button"
        class="min-h-[44px] self-center px-4 text-[15px] font-bold text-danger"
        @click="logout"
      >
        تسجيل خروج
      </button>
      <p class="self-center text-[12px] font-semibold text-muted">
        إصدار التطبيق {{ APP_VERSION }}
      </p>
    </div>

    <!-- guest -->
    <form
      v-else
      class="flex flex-col items-center gap-[18px] px-5 py-6"
      novalidate
      @submit.prevent="submit"
    >
      <AppLogo :size="84" icon-only class="mt-3" />
      <div class="text-center">
        <h2 class="text-[22px] font-extrabold text-ink">اعمل حسابك في ثانية</h2>
        <p class="mt-3 text-[15px] leading-[1.7] text-ink-2">
          محتاجين اسمك ورقم موبايلك بس عشان نوصلّك طلبك
        </p>
      </div>

      <p
        v-if="info"
        role="status"
        class="w-full rounded-field bg-success-soft px-3 py-2 text-[14px] font-bold text-success-strong"
      >
        {{ info }}
      </p>
      <p
        v-if="errors.form"
        role="alert"
        class="w-full rounded-field bg-danger-soft px-3 py-2 text-[14px] font-bold text-danger"
      >
        {{ errors.form }}
      </p>

      <div class="flex w-full flex-col gap-[18px]">
        <Input
          v-if="mode === 'register'"
          v-model="name"
          label="الاسم"
          placeholder="مثلاً: محمد أحمد"
          autocomplete="name"
          :error="errors.name"
        />
        <Input
          v-model="phone"
          label="رقم الموبايل"
          type="tel"
          inputmode="numeric"
          ltr
          placeholder="01xxxxxxxxx"
          autocomplete="tel"
          :error="errors.phone"
        />
        <Input
          v-if="mode === 'register'"
          v-model="email"
          label="الإيميل"
          optional
          type="email"
          ltr
          placeholder="name@example.com"
          autocomplete="email"
          :error="errors.email"
        />
      </div>

      <div class="flex w-full flex-col gap-2">
        <Button type="submit" block :loading="submitting" :disabled="!valid">
          <template v-if="mode === 'login'">دخول</template>
          <template v-else>{{
            fromCheckout || !cart.isEmpty ? 'إنشاء الحساب وتأكيد الطلب' : 'إنشاء الحساب'
          }}</template>
        </Button>
        <p v-if="!valid" class="text-center text-[13px] font-semibold text-muted">
          {{ mode === 'register' ? phoneUtil.hint : phoneUtil.error }}
        </p>
      </div>

      <button
        v-if="mode === 'register'"
        type="button"
        class="mt-2 min-h-[44px] text-[14px] text-ink-2"
        @click="switchMode('login')"
      >
        عندك حساب؟ <span class="font-bold text-link">ادخل برقم موبايلك</span>
      </button>
      <button
        v-else
        type="button"
        class="min-h-[44px] text-[14px] font-bold text-link"
        @click="switchMode('register')"
      >
        مش عندك حساب؟ اعمل حساب جديد
      </button>
    </form>
  </div>
</template>

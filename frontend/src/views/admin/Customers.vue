<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { Phone, Search, UserX } from 'lucide-vue-next'
import { getCustomerOrders, listAdminCustomers } from '@/api/admin/customers'
import AdminHeader from '@/components/admin/AdminHeader.vue'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import type { AdminCustomer, AdminOrder } from '@/types/api'
import { dayLabel, formatDayMonth } from '@/utils/date'
import { formatPhoneDisplay } from '@/utils/phone'
import { formatMoney } from '@/utils/money'

const q = ref('')
const customers = ref<AdminCustomer[]>([])
const page = ref(1)
const hasMore = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const failed = ref(false)
const selected = ref<AdminCustomer | null>(null)
const customerOrders = ref<AdminOrder[]>([])
const ordersLoading = ref(false)
let seq = 0
let timer: ReturnType<typeof setTimeout> | undefined

async function load(reset = true) {
  const mine = ++seq
  if (reset) {
    page.value = 1
    loading.value = true
  } else {
    page.value += 1
    loadingMore.value = true
  }
  failed.value = false
  try {
    const res = await listAdminCustomers(q.value.trim() || undefined, page.value)
    if (mine !== seq) return
    customers.value = reset ? res.results : [...customers.value, ...res.results]
    hasMore.value = !!res.next
  } catch {
    if (mine !== seq) return
    failed.value = true
    if (!reset) page.value -= 1
  } finally {
    if (mine === seq) {
      loading.value = false
      loadingMore.value = false
    }
  }
}

load()
watch(q, () => {
  clearTimeout(timer)
  timer = setTimeout(() => load(), 300)
})
onBeforeUnmount(() => clearTimeout(timer))

async function open(c: AdminCustomer) {
  selected.value = c
  customerOrders.value = []
  ordersLoading.value = true
  try {
    customerOrders.value = (await getCustomerOrders(c.id)).results
  } catch {
    customerOrders.value = []
  } finally {
    ordersLoading.value = false
  }
}

const initial = (name: string) => name.trim().charAt(0)
</script>

<template>
  <div>
    <AdminHeader title="الزبائن" />
    <div class="flex flex-col gap-2 px-4 pt-3">
      <div class="relative">
        <input
          v-model="q"
          type="search"
          aria-label="ابحث بالاسم أو رقم الموبايل"
          placeholder="ابحث بالاسم أو رقم الموبايل"
          class="h-[50px] w-full rounded-field border border-input-border bg-white ps-11 pe-[14px] text-[15px] text-ink"
        />
        <Search
          class="pointer-events-none absolute start-3 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-2"
          aria-hidden="true"
        />
      </div>
      <p class="text-[13px] font-semibold text-muted">مرتبين حسب آخر طلب</p>
    </div>

    <div class="flex flex-col gap-2 p-4">
      <template v-if="loading">
        <Skeleton v-for="i in 4" :key="i" class="h-[96px]" />
      </template>
      <p v-else-if="failed" class="text-[14px] font-bold text-danger" role="alert">
        مقدرناش نحمّل الزبائن
        <button type="button" class="min-h-[44px] ms-2 text-link underline" @click="load()">
          حاول تاني
        </button>
      </p>
      <EmptyState v-else-if="!customers.length" :icon="UserX" text="مفيش زبائن بالاسم ده" />
      <template v-else>
        <article
          v-for="c in customers"
          :key="c.id"
          class="flex items-center gap-3 rounded-card border border-border bg-surface p-3"
        >
          <button
            type="button"
            class="flex min-w-0 flex-1 items-center gap-3 text-start"
            @click="open(c)"
          >
            <span
              class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary-soft text-[18px] font-extrabold text-brand-deep"
              aria-hidden="true"
            >
              {{ initial(c.name) }}
            </span>
            <span class="flex min-w-0 flex-col">
              <span class="text-[15px] font-extrabold text-ink">{{ c.name }}</span>
              <span dir="ltr" class="self-start text-[14px] text-ink-2">{{
                formatPhoneDisplay(c.phone)
              }}</span>
              <span class="truncate text-[13px] text-muted">{{ c.email || 'بدون إيميل' }}</span>
              <span class="text-[13px] font-bold text-ink">
                {{ c.orders_count }} طلب · {{ formatMoney(c.total_spent) }}
                <template v-if="c.last_order_at">
                  · آخر طلب {{ dayLabel(c.last_order_at) }}</template
                >
              </span>
            </span>
          </button>
          <a
            :href="`tel:${c.phone}`"
            :aria-label="`اتصال بـ ${c.name}`"
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-field bg-primary-tint text-brand-deep"
          >
            <Phone class="h-5 w-5" aria-hidden="true" />
          </a>
        </article>
        <button
          v-if="hasMore"
          type="button"
          class="min-h-[44px] rounded-btn border border-input-border bg-white font-bold text-ink"
          :disabled="loadingMore"
          @click="load(false)"
        >
          عرض المزيد
        </button>
      </template>
    </div>

    <BottomSheet v-if="selected" :title="`طلبات ${selected.name}`" @close="selected = null">
      <Skeleton v-if="ordersLoading" class="h-[80px]" />
      <p v-else-if="!customerOrders.length" class="text-[14px] text-muted">مفيش طلبات لسه</p>
      <ul v-else class="flex flex-col gap-2">
        <li
          v-for="o in customerOrders"
          :key="o.id"
          class="flex flex-col gap-1 rounded-card border border-border p-3"
        >
          <span class="flex items-center justify-between">
            <span class="font-extrabold text-ink">طلب #{{ o.number }}</span>
            <StatusPill :status="o.status" />
          </span>
          <span class="text-[14px] text-ink-2">{{ o.items_summary }}</span>
          <span class="text-[13px] text-muted">
            {{ formatDayMonth(o.created_at) }} · {{ formatMoney(o.total) }}
          </span>
        </li>
      </ul>
    </BottomSheet>
  </div>
</template>

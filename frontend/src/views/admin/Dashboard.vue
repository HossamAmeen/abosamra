<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { BarChart3, Check, Package, Phone, Plus, Tag, Users } from 'lucide-vue-next'
import { getDashboard } from '@/api/admin/dashboard'
import { listAdminOrders, setOrderStatus } from '@/api/admin/orders'
import AdminHeader from '@/components/admin/AdminHeader.vue'
import Button from '@/components/ui/Button.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import { usePolling } from '@/composables/usePolling'
import { useToast } from '@/composables/useToast'
import { useAdminStore } from '@/stores/admin'
import type { AdminOrder, Dashboard } from '@/types/api'
import { formatWeekdayDate, timeAgo } from '@/utils/date'
import { formatMoney } from '@/utils/money'

const admin = useAdminStore()
const toast = useToast()
const data = ref<Dashboard | null>(null)
const pendingOrders = ref<AdminOrder[]>([])
const confirmed = ref<AdminOrder[]>([])
// Confirmed orders stay visible (green label) until the page is left.
const shown = computed(() => [...confirmed.value, ...pendingOrders.value])
const isConfirmed = (id: number) => confirmed.value.some((c) => c.id === id)
const busy = ref<number | null>(null)
const failed = ref(false)
const today = formatWeekdayDate(new Date())

async function load() {
  try {
    const [d, o] = await Promise.all([getDashboard(), listAdminOrders({ status: 'new' })])
    data.value = d
    pendingOrders.value = o.results.slice(0, 3)
    admin.pending = d.pending_count
    failed.value = false
  } catch {
    failed.value = true
  }
}

usePolling(load, 30000)

async function confirmOrder(o: AdminOrder) {
  if (busy.value) return
  busy.value = o.id
  try {
    await setOrderStatus(o.id, 'preparing')
    confirmed.value = [...confirmed.value, o]
    toast.show('تم تأكيد الطلب')
    await load()
  } catch {
    toast.show('معرفناش نأكد الطلب، جرّب تاني', { duration: 4000 })
  } finally {
    busy.value = null
  }
}

const stats = () =>
  data.value
    ? [
        { label: 'طلبات النهاردة', value: String(data.value.orders_today), icon: Package },
        { label: 'مبيعات النهاردة', value: formatMoney(data.value.sales_today), icon: BarChart3 },
        {
          label: 'مستنية تأكيد',
          value: String(data.value.pending_count),
          icon: Phone,
          highlight: true,
        },
        {
          label: 'زبائن جدد الأسبوع ده',
          value: String(data.value.new_customers_week),
          icon: Users,
        },
      ]
    : []
</script>

<template>
  <div>
    <AdminHeader title="أهلاً يا أبو سمرة" :caption="`${today} · ملخص النهاردة`" />

    <div class="flex flex-col gap-5 p-4">
      <p v-if="failed && !data" class="text-[14px] font-bold text-danger" role="alert">
        مقدرناش نحمّل البيانات
        <button type="button" class="min-h-[44px] ms-2 text-link underline" @click="load">
          حاول تاني
        </button>
      </p>

      <section class="grid grid-cols-2 gap-3" aria-label="ملخص النهاردة">
        <template v-if="data">
          <div
            v-for="s in stats()"
            :key="s.label"
            :class="[
              'flex flex-col gap-2 rounded-card border p-3',
              s.highlight ? 'border-primary bg-primary-soft' : 'border-border bg-surface',
            ]"
          >
            <span class="flex h-9 w-9 items-center justify-center rounded-field bg-primary-tint">
              <component :is="s.icon" class="h-5 w-5 text-brand-deep" aria-hidden="true" />
            </span>
            <span class="text-[13px] font-semibold text-ink-2">{{ s.label }}</span>
            <span class="text-[24px] font-extrabold text-ink">{{ s.value }}</span>
          </div>
        </template>
        <template v-else>
          <Skeleton v-for="i in 4" :key="i" class="h-[120px]" />
        </template>
      </section>

      <section class="grid grid-cols-2 gap-3">
        <RouterLink
          to="/admin/products/new"
          class="flex h-[52px] items-center justify-center gap-2 rounded-btn bg-primary text-[16px] font-extrabold text-ink"
        >
          <Plus class="h-5 w-5" aria-hidden="true" />
          إضافة منتج
        </RouterLink>
        <RouterLink
          to="/admin/offers"
          class="flex h-[52px] items-center justify-center gap-2 rounded-btn bg-ink text-[16px] font-extrabold text-on-dark"
        >
          <Tag class="h-5 w-5" aria-hidden="true" />
          عرض جديد
        </RouterLink>
      </section>

      <section class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <h2 class="text-[17px] font-extrabold text-ink">طلبات جديدة محتاجة تأكيد</h2>
          <RouterLink to="/admin/orders" class="min-h-[44px] py-3 text-[14px] font-bold text-link">
            كل الطلبات
          </RouterLink>
        </div>
        <p v-if="data && !shown.length" class="text-[14px] text-muted">مفيش طلبات جديدة دلوقتي</p>
        <article
          v-for="o in shown"
          :key="o.id"
          class="flex flex-col gap-2 rounded-card border border-border bg-surface p-3.5"
        >
          <div class="flex items-start justify-between gap-2">
            <h3 class="text-[15px] font-extrabold text-ink">
              #{{ o.number }} · {{ o.customer.name }}
            </h3>
            <span class="shrink-0 text-[12px] text-muted">{{ timeAgo(o.created_at) }}</span>
          </div>
          <p class="text-[14px] text-ink-2">{{ o.items_summary }}</p>
          <div class="flex items-center justify-between gap-2">
            <span class="text-[17px] font-extrabold text-ink">{{ formatMoney(o.total) }}</span>
            <div class="flex items-center gap-2">
              <a
                :href="`tel:${o.customer.phone}`"
                :aria-label="`اتصل بـ ${o.customer.name}`"
                class="flex h-11 w-11 items-center justify-center rounded-field bg-primary-tint text-brand-deep"
              >
                <Phone class="h-5 w-5" aria-hidden="true" />
              </a>
              <span
                v-if="isConfirmed(o.id)"
                class="inline-flex h-11 items-center gap-1 px-3 text-[14px] font-extrabold text-success"
              >
                <Check class="h-5 w-5" aria-hidden="true" /> اتأكد
              </span>
              <Button v-else size="md" :loading="busy === o.id" @click="confirmOrder(o)">
                تأكيد الطلب
              </Button>
            </div>
          </div>
        </article>
      </section>

      <section class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <h2 class="text-[17px] font-extrabold text-ink">قرب يخلص من المخزن</h2>
          <RouterLink
            to="/admin/products"
            class="min-h-[44px] py-3 text-[14px] font-bold text-link"
          >
            المنتجات
          </RouterLink>
        </div>
        <p v-if="data && !data.low_stock.length" class="text-[14px] text-muted">
          المخزن تمام، مفيش حاجة قربت تخلص
        </p>
        <ul v-else class="flex flex-col gap-2">
          <li
            v-for="p in data?.low_stock ?? []"
            :key="p.id"
            class="flex min-h-[52px] items-center justify-between rounded-card border border-border bg-surface px-3.5"
          >
            <span class="text-[15px] font-bold text-ink">{{ p.name }}</span>
            <span class="text-[14px] font-extrabold text-danger">
              باقي <span dir="ltr">{{ Number(p.stock_qty) }}</span> {{ p.stock_unit }}
            </span>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

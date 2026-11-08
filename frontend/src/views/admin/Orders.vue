<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MoreHorizontal, PackageOpen } from 'lucide-vue-next'
import { apiError } from '@/api/client'
import { getOrderCounts, listAdminOrders, setOrderStatus } from '@/api/admin/orders'
import AdminHeader from '@/components/admin/AdminHeader.vue'
import OrderCard from '@/components/admin/OrderCard.vue'
import OrderSheet from '@/components/admin/OrderSheet.vue'
import Chip from '@/components/ui/Chip.vue'
import ChipRow from '@/components/ui/ChipRow.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import { useToast } from '@/composables/useToast'
import { useAdminStore } from '@/stores/admin'
import type { AdminOrder, OrderCounts, OrderStatus } from '@/types/api'
import { NEXT_ACTION, STATUS_LABELS } from '@/utils/status'

const MAIN: OrderStatus[] = ['new', 'preparing', 'out_for_delivery', 'delivered']
const route = useRoute()
const router = useRouter()
const toast = useToast()
const admin = useAdminStore()

const status = computed<OrderStatus>(() => {
  const s = route.query.status
  return typeof s === 'string' && s in STATUS_LABELS ? (s as OrderStatus) : 'new'
})
const counts = ref<OrderCounts | null>(null)
const orders = ref<AdminOrder[]>([])
const page = ref(1)
const hasMore = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const failed = ref(false)
const busyId = ref<number | null>(null)
const selected = ref<AdminOrder | null>(null)
const showMenu = ref(false)
let seq = 0

async function loadCounts() {
  try {
    counts.value = await getOrderCounts()
    admin.pending = counts.value.new
  } catch {
    /* chips render without counts */
  }
}

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
    const res = await listAdminOrders({ status: status.value, page: page.value })
    if (mine !== seq) return
    orders.value = reset ? res.results : [...orders.value, ...res.results]
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

watch(status, () => load(), { immediate: true })
loadCounts()

function pick(s: OrderStatus) {
  showMenu.value = false
  router.replace({ query: { status: s } })
}

function reason(e: unknown) {
  const { body } = apiError(e)
  return body.detail ?? 'حصلت مشكلة، جرّب تاني'
}

async function changeStatus(o: AdminOrder, next: OrderStatus) {
  busyId.value = o.id
  try {
    await setOrderStatus(o.id, next)
    orders.value = orders.value.filter((x) => x.id !== o.id)
    selected.value = null
    toast.show(`طلب #${o.number}: ${STATUS_LABELS[next]}`)
    loadCounts()
  } catch (e) {
    toast.show(reason(e), { duration: 4000 })
  } finally {
    busyId.value = null
  }
}

const advance = (o: AdminOrder) => {
  const next = NEXT_ACTION[o.status]
  if (next) void changeStatus(o, next.status)
}
</script>

<template>
  <div>
    <AdminHeader title="الطلبات" />
    <div class="relative">
      <ChipRow aria-label="حالة الطلب">
        <Chip v-for="s in MAIN" :key="s" size="admin" :selected="status === s" @click="pick(s)">
          {{ STATUS_LABELS[s] }}<template v-if="counts"> ({{ counts[s] }})</template>
        </Chip>
        <Chip v-if="status === 'cancelled'" size="admin" selected @click="pick('cancelled')">
          {{ STATUS_LABELS.cancelled }}<template v-if="counts"> ({{ counts.cancelled }})</template>
        </Chip>
        <button
          type="button"
          aria-label="حالات تانية"
          :aria-expanded="showMenu"
          class="flex h-10 min-h-[44px] w-11 shrink-0 items-center justify-center rounded-full border border-input-border bg-white text-ink"
          @click="showMenu = !showMenu"
        >
          <MoreHorizontal class="h-5 w-5" aria-hidden="true" />
        </button>
      </ChipRow>
      <div
        v-if="showMenu"
        class="absolute start-4 top-14 z-10 rounded-card border border-border bg-surface p-1 shadow"
      >
        <button
          type="button"
          class="min-h-[44px] w-full rounded-field px-4 text-start text-[14px] font-bold text-ink"
          @click="pick('cancelled')"
        >
          {{ STATUS_LABELS.cancelled }}<template v-if="counts"> ({{ counts.cancelled }})</template>
        </button>
      </div>
    </div>

    <div class="flex flex-col gap-3 px-4 pb-4">
      <template v-if="loading">
        <Skeleton v-for="i in 3" :key="i" class="h-[150px]" />
      </template>
      <p v-else-if="failed" class="text-[14px] font-bold text-danger" role="alert">
        مقدرناش نحمّل الطلبات
        <button type="button" class="min-h-[44px] ms-2 text-link underline" @click="load()">
          حاول تاني
        </button>
      </p>
      <EmptyState v-else-if="!orders.length" :icon="PackageOpen" text="مفيش طلبات هنا" />
      <template v-else>
        <OrderCard
          v-for="o in orders"
          :key="o.id"
          :order="o"
          :busy="busyId === o.id"
          @open="selected = o"
          @advance="advance(o)"
        />
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

    <OrderSheet
      v-if="selected"
      :order="selected"
      :cancelling="busyId === selected.id"
      @close="selected = null"
      @cancel="changeStatus(selected, 'cancelled')"
    />
  </div>
</template>

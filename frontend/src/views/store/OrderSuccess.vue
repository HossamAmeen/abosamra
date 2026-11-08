<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { Check, Phone } from 'lucide-vue-next'
import { getOrder } from '@/api/orders'
import EmptyState from '@/components/ui/EmptyState.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import { useSettingsStore } from '@/stores/settings'
import type { Order } from '@/types/api'
import { formatMoney } from '@/utils/money'

const route = useRoute()
const settings = useSettingsStore()
const order = ref<Order | null>(null)
const loading = ref(true)
const failed = ref(false)

async function load() {
  loading.value = true
  failed.value = false
  try {
    order.value = await getOrder(String(route.params.id))
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}
onMounted(() => {
  settings.load()
  load()
})
const itemsCount = computed(() => order.value?.lines.reduce((s, l) => s + l.qty, 0) ?? 0)
</script>

<template>
  <div class="flex flex-col items-center gap-4 px-5 pb-5 pt-10 text-center">
    <div v-if="loading" class="flex w-full flex-col items-center gap-4">
      <Skeleton class="h-[104px] w-[104px] rounded-full" />
      <Skeleton class="h-8 w-2/3" />
    </div>
    <EmptyState
      v-else-if="failed || !order"
      text="مقدرناش نجيب الطلب ده"
      action-label="حاول تاني"
      @action="load"
    />
    <template v-else>
      <div
        class="flex h-[104px] w-[104px] items-center justify-center rounded-full bg-success-soft"
      >
        <Check class="h-14 w-14 text-success" :stroke-width="2.5" aria-hidden="true" />
      </div>
      <h1 class="mt-3 text-[26px] font-extrabold text-ink">طلبك وصل لأبو سمرة!</h1>
      <span class="rounded-full bg-primary-soft px-4 py-1.5 text-[15px] font-bold text-brand-deep">
        رقم الطلب #{{ order.number }}
      </span>
      <p class="px-5 text-[15px] leading-[1.7] text-ink-2">
        هنكلمك على رقمك خلال دقايق نأكد الطلب ونقولك ميعاد التوصيل.
      </p>
      <section
        class="flex w-full flex-col gap-2.5 rounded-card border border-border bg-surface p-4 text-[15px]"
      >
        <div class="flex justify-between">
          <span class="text-ink-2">عدد المنتجات</span
          ><span class="font-bold">{{ itemsCount }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-ink-2">الإجمالي</span>
          <span class="font-extrabold">{{ formatMoney(order.total) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-ink-2">طريقة الدفع</span><span class="font-bold">كاش عند الاستلام</span>
        </div>
      </section>
      <RouterLink
        to="/"
        class="inline-flex h-[52px] w-full items-center justify-center rounded-btn bg-primary text-[16px] font-extrabold text-ink"
      >
        كمّل تسوق
      </RouterLink>
      <a
        v-if="settings.shopPhone"
        :href="`tel:${settings.shopPhone}`"
        class="mt-2 inline-flex min-h-[44px] items-center gap-2 font-bold text-link"
      >
        <Phone class="h-5 w-5" aria-hidden="true" />
        اتصل بالمحل
      </a>
    </template>
  </div>
</template>

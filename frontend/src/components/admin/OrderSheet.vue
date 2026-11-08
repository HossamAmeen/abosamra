<script setup lang="ts">
import { ref } from 'vue'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import Button from '@/components/ui/Button.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import type { AdminOrder } from '@/types/api'
import { formatDiscount, formatMoney } from '@/utils/money'

const props = defineProps<{ order: AdminOrder; cancelling?: boolean }>()
const emit = defineEmits<{ close: []; cancel: [] }>()
const confirming = ref(false)
const canCancel = !['delivered', 'cancelled'].includes(props.order.status)
</script>

<template>
  <BottomSheet :title="`طلب #${order.number}`" @close="emit('close')">
    <div class="flex flex-col gap-3 text-[14px] text-ink">
      <div class="flex items-center justify-between">
        <span class="font-bold">{{ order.customer.name }}</span>
        <StatusPill :status="order.status" />
      </div>
      <a :href="`tel:${order.customer.phone}`" dir="ltr" class="self-start text-link underline">
        {{ order.customer.phone }}
      </a>
      <p>
        <span class="font-bold">العنوان: </span
        >{{ [order.address, order.area].filter(Boolean).join('، ') }}
      </p>
      <p v-if="order.notes"><span class="font-bold">ملاحظات: </span>{{ order.notes }}</p>

      <ul class="flex flex-col divide-y divide-border rounded-card border border-border">
        <li v-for="(l, i) in order.lines" :key="i" class="flex flex-col gap-0.5 p-3">
          <span class="flex justify-between gap-2">
            <span class="font-bold">{{ l.name }} {{ l.unit_label }} × {{ l.qty }}</span>
            <span class="font-bold">{{ formatMoney(l.line_total) }}</span>
          </span>
          <span v-if="l.note" class="text-[13px] text-muted">{{ l.note }}</span>
        </li>
      </ul>

      <dl class="flex flex-col gap-1">
        <div class="flex justify-between">
          <dt>المجموع</dt>
          <dd>{{ formatMoney(order.subtotal) }}</dd>
        </div>
        <div v-for="d in order.discounts" :key="d.label" class="flex justify-between text-success">
          <dt>{{ d.label }}</dt>
          <dd>{{ formatDiscount(d.amount) }}</dd>
        </div>
        <div class="flex justify-between">
          <dt>التوصيل</dt>
          <dd>{{ order.delivery_fee ? formatMoney(order.delivery_fee) : 'مجاني' }}</dd>
        </div>
        <div class="flex justify-between text-[18px] font-extrabold">
          <dt>الإجمالي</dt>
          <dd>{{ formatMoney(order.total) }}</dd>
        </div>
      </dl>

      <template v-if="canCancel">
        <Button v-if="!confirming" variant="danger-text" block @click="confirming = true">
          إلغاء الطلب
        </Button>
        <div v-else class="flex flex-col gap-2 rounded-card bg-danger-soft p-3" role="alert">
          <p class="font-bold text-danger">متأكد إنك عايز تلغي الطلب ده؟ المخزون هيرجع.</p>
          <div class="grid grid-cols-2 gap-2">
            <Button variant="danger" size="md" :loading="cancelling" @click="emit('cancel')">
              أيوه، إلغي
            </Button>
            <Button variant="secondary" size="md" @click="confirming = false">لأ</Button>
          </div>
        </div>
      </template>
    </div>
  </BottomSheet>
</template>

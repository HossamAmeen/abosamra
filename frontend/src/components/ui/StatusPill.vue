<script setup lang="ts">
import { computed } from 'vue'
import type { OrderStatus } from '@/types/api'
import { STATUS_LABELS } from '@/utils/status'

const props = defineProps<{ status: OrderStatus }>()

const STYLE: Record<OrderStatus, string> = {
  new: 'bg-status-new-bg text-status-new-text',
  preparing: 'bg-status-preparing-bg text-status-preparing-text',
  out_for_delivery: 'bg-status-out-bg text-status-out-text',
  delivered: 'bg-status-delivered-bg text-status-delivered-text',
  cancelled: 'bg-status-cancelled-bg text-status-cancelled-text',
}
const label = computed(() => STATUS_LABELS[props.status])
</script>

<template>
  <span :class="['inline-block rounded-full px-3 py-1 text-[12px] font-bold', STYLE[status]]">
    {{ label }}
  </span>
</template>

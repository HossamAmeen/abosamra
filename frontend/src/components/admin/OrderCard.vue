<script setup lang="ts">
import { computed } from 'vue'
import { Phone } from 'lucide-vue-next'
import Button from '@/components/ui/Button.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import type { AdminOrder } from '@/types/api'
import { timeAgo } from '@/utils/date'
import { formatMoney } from '@/utils/money'
import { formatPhoneDisplay } from '@/utils/phone'
import { NEXT_ACTION } from '@/utils/status'

const props = defineProps<{ order: AdminOrder; busy?: boolean }>()
const emit = defineEmits<{ open: []; advance: [] }>()
const next = computed(() => NEXT_ACTION[props.order.status])
</script>

<template>
  <article
    class="flex flex-col gap-2 rounded-card border border-border bg-surface p-3.5"
    :data-testid="`order-${order.number}`"
  >
    <button type="button" class="flex flex-col gap-2 text-start" @click="emit('open')">
      <span class="flex items-center justify-between gap-2">
        <span class="text-[16px] font-extrabold text-ink">طلب #{{ order.number }}</span>
        <StatusPill :status="order.status" />
      </span>
      <span class="flex items-center justify-between gap-2">
        <span class="text-[15px] font-bold text-ink">{{ order.customer.name }}</span>
        <span dir="ltr" class="text-[14px] text-ink-2">{{
          formatPhoneDisplay(order.customer.phone)
        }}</span>
      </span>
      <span class="text-[14px] text-ink-2">{{ order.items_summary }}</span>
      <span class="text-[13px] text-muted">
        {{ [order.area, timeAgo(order.created_at)].filter(Boolean).join(' · ') }}
      </span>
    </button>
    <hr class="border-border" />
    <div class="flex items-center justify-between gap-2">
      <span class="text-[18px] font-extrabold text-ink">{{ formatMoney(order.total) }}</span>
      <div class="flex items-center gap-2">
        <a
          :href="`tel:${order.customer.phone}`"
          :aria-label="`اتصال بـ ${order.customer.name}`"
          class="inline-flex h-11 items-center gap-1.5 rounded-field bg-primary-tint px-3 text-[14px] font-bold text-brand-deep"
        >
          <Phone class="h-5 w-5" aria-hidden="true" />
          اتصال
        </a>
        <Button v-if="next" size="md" :loading="busy" @click="emit('advance')">
          {{ next.label }}
        </Button>
      </div>
    </div>
  </article>
</template>

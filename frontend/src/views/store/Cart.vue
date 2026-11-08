<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ShoppingCart, Trash2 } from 'lucide-vue-next'
import { apiError } from '@/api/client'
import { createOrder } from '@/api/orders'
import Button from '@/components/ui/Button.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Input from '@/components/ui/Input.vue'
import ProductThumb from '@/components/ui/ProductThumb.vue'
import QtyStepper from '@/components/ui/QtyStepper.vue'
import { useCheckoutDraft } from '@/composables/useCheckoutDraft'
import { useOnline } from '@/composables/useOnline'
import { lineKey, useCartStore } from '@/stores/cart'
import { useAuthStore } from '@/stores/auth'
import { useCatalogStore } from '@/stores/catalog'
import { useSettingsStore } from '@/stores/settings'
import { formatDiscount, formatMoney } from '@/utils/money'

const route = useRoute()
const router = useRouter()
const cart = useCartStore()
const auth = useAuthStore()
const catalog = useCatalogStore()
const settings = useSettingsStore()
const { address } = useCheckoutDraft()
const { online } = useOnline()

const addressError = ref('')
const submitError = ref('')
const submitting = ref(false)

onMounted(async () => {
  settings.load()
  catalog.loadOffers()
  catalog.loadCategories()
  if (!address.value && auth.user?.default_address) address.value = auth.user.default_address
  await cart.revalidate()
  if (route.query.resume === '1') {
    router.replace({ name: 'cart' })
    if (auth.isLoggedIn) await checkout()
  }
})

// Re-quote (debounced) after any quantity/line change; the server stays the source of truth.
let timer: ReturnType<typeof setTimeout> | undefined
watch(
  () => cart.lines.map((l) => `${lineKey(l)}:${l.qty}`).join(','),
  () => {
    clearTimeout(timer)
    timer = setTimeout(() => cart.revalidate(), 300)
  },
)
onBeforeUnmount(() => clearTimeout(timer))

const totals = computed(() => cart.totals)
const threshold = computed(() => totals.value.free_delivery_threshold || 1)
const remaining = computed(() => totals.value.free_delivery_remaining)
const progress = computed(() =>
  Math.max(
    0,
    Math.min(100, Math.round(((threshold.value - remaining.value) / threshold.value) * 100)),
  ),
)
const unitPart = (l: { unitLabel: string; unitPrice: number }) =>
  `${l.unitLabel} · ${formatMoney(l.unitPrice)}`

const lineTotal = (l: { unitPrice: number; qty: number }) => l.unitPrice * l.qty

const ADDRESS_MIN = 10
async function checkout() {
  submitError.value = ''
  addressError.value = ''
  if (cart.isEmpty) return
  if (!auth.isLoggedIn) {
    router.push({ name: 'account', query: { next: 'checkout' } })
    return
  }
  if (address.value.trim().length < ADDRESS_MIN) {
    addressError.value = 'اكتب العنوان بالتفصيل (10 حروف على الأقل)'
    return
  }
  submitting.value = true
  try {
    const q = await cart.revalidate()
    if (!q || cart.hasBlockingWarnings) {
      submitError.value = q ? 'راجع السلة وبعدين كمّل الطلب' : 'مقدرناش نراجع السلة، حاول تاني'
      return
    }
    const order = await createOrder({
      ...cart.orderBody(),
      address: address.value.trim(),
      area: auth.user?.area || undefined,
    })
    cart.clear()
    address.value = ''
    router.push({ name: 'order-success', params: { id: order.id } })
  } catch (e) {
    const { status, body } = apiError(e)
    if (status === 409 && body.code === 'cart_changed' && body.quote) {
      cart.applyQuote(body.quote)
      submitError.value = 'فيه حاجات في السلة اتغيرت، راجع السلة وكمّل الطلب'
    } else if (status === 400 && Array.isArray(body.address)) {
      addressError.value = String(body.address[0])
    } else {
      submitError.value = body.detail ?? 'حصلت مشكلة، حاول تاني'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <header class="flex items-center justify-between bg-surface px-4 py-3">
      <h1 class="text-[22px] font-extrabold text-ink">السلة</h1>
      <span v-if="!cart.isEmpty" class="text-[14px] font-bold text-muted"
        >{{ cart.count }} منتج</span
      >
    </header>

    <EmptyState
      v-if="cart.isEmpty"
      :icon="ShoppingCart"
      text="السلة فاضية"
      action-label="ابدأ التسوق"
      to="/"
    />

    <div v-else class="flex flex-col gap-3 px-4 pt-4">
      <div
        v-if="cart.notices.length"
        role="alert"
        class="flex flex-col gap-1 rounded-card bg-danger-soft px-4 py-3 text-[14px] font-bold text-danger"
      >
        <p v-for="n in cart.notices" :key="n">{{ n }}</p>
      </div>

      <ul class="flex flex-col gap-3">
        <li
          v-for="l in cart.lines"
          :key="lineKey(l)"
          class="flex gap-3 rounded-card border border-border bg-surface p-2.5"
        >
          <div class="h-[72px] w-[72px] shrink-0">
            <ProductThumb
              :tint="catalog.categoryBySlug(l.categorySlug ?? '')?.color"
              :icon="catalog.categoryBySlug(l.categorySlug ?? '')?.icon ?? 'soup'"
              :icon-size="32"
            />
          </div>
          <div class="flex min-w-0 flex-1 flex-col justify-between">
            <span class="text-[15px] font-bold text-ink">{{ l.name }}</span>
            <span class="text-[12px] font-semibold text-muted">{{ unitPart(l) }}</span>
            <span class="text-[15px] font-extrabold text-ink">{{ formatMoney(lineTotal(l)) }}</span>
          </div>
          <div class="flex shrink-0 flex-col items-center justify-between gap-1">
            <QtyStepper
              :model-value="l.qty"
              :min="0"
              :name="l.name"
              @update:model-value="cart.setQty(lineKey(l), $event)"
            />
            <button
              type="button"
              class="inline-flex min-h-[44px] items-center gap-1 px-2 text-[13px] font-bold text-danger"
              :aria-label="`شيل ${l.name} من السلة`"
              @click="cart.remove(lineKey(l))"
            >
              <Trash2 class="h-4 w-4" aria-hidden="true" />
              شيل
            </button>
          </div>
        </li>
      </ul>

      <section class="flex flex-col gap-2 rounded-card bg-success-soft p-3.5 text-success-strong">
        <p class="text-[14px] font-bold">
          <template v-if="remaining > 0"
            >فاضلك {{ formatMoney(remaining) }} وتاخد توصيل مجاني</template
          >
          <template v-else>مبروك! طلبك عليه توصيل مجاني</template>
        </p>
        <div
          class="h-2 overflow-hidden rounded-full bg-white"
          role="progressbar"
          :aria-valuenow="progress"
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label="التقدم نحو التوصيل المجاني"
        >
          <div
            class="h-full rounded-full bg-success transition-all"
            :style="{ width: progress + '%' }"
          />
        </div>
      </section>

      <Input
        v-model="address"
        label="عنوان التوصيل"
        multiline
        :rows="2"
        placeholder="المنطقة، الشارع، رقم العمارة والدور"
        autocomplete="street-address"
        :error="addressError"
      />

      <section class="flex flex-col gap-2.5 rounded-card border border-border bg-surface p-4">
        <div class="flex justify-between text-[15px] text-ink-2">
          <span>المجموع</span><span class="font-bold">{{ formatMoney(totals.subtotal) }}</span>
        </div>
        <div
          v-for="d in totals.discounts"
          :key="d.offer_id"
          class="flex justify-between text-[15px] font-bold text-danger"
        >
          <span>{{ d.label }}</span
          ><span>{{ formatDiscount(d.amount) }}</span>
        </div>
        <div class="flex justify-between text-[15px] text-ink-2">
          <span>التوصيل</span>
          <span class="font-bold" :class="totals.delivery_fee === 0 ? 'text-success' : ''">{{
            totals.delivery_fee === 0 ? 'مجاني' : formatMoney(totals.delivery_fee)
          }}</span>
        </div>
        <hr class="border-border" />
        <div class="flex justify-between text-[18px] font-extrabold text-ink">
          <span>الإجمالي</span><span>{{ formatMoney(totals.total) }}</span>
        </div>
        <p class="text-[13px] text-muted">الدفع كاش عند الاستلام</p>
      </section>

      <p v-if="submitError" role="alert" class="text-[14px] font-bold text-danger">
        {{ submitError }}
      </p>
      <p v-if="cart.quoteError" role="alert" class="text-[13px] font-semibold text-danger">
        مقدرناش نحدّث الأسعار.
        <button type="button" class="min-h-[44px] font-bold text-link" @click="cart.revalidate()">
          حاول تاني
        </button>
      </p>
      <p v-if="!online" role="alert" class="text-[13px] font-semibold text-danger">
        الطلب محتاج نت، ارجع اتصل وكمّل
      </p>
      <Button
        block
        :loading="submitting"
        :disabled="cart.quoting || cart.hasBlockingWarnings || !online"
        @click="checkout"
      >
        كمّل الطلب
      </Button>
    </div>
  </div>
</template>

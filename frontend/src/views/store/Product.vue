<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ChevronRight, PackageX, ShoppingCart } from 'lucide-vue-next'
import CategoryIcon from '@/components/ui/CategoryIcon.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Input from '@/components/ui/Input.vue'
import QtyStepper from '@/components/ui/QtyStepper.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import { useCartStore } from '@/stores/cart'
import { useCatalogStore } from '@/stores/catalog'
import type { Product } from '@/types/api'
import { apiError } from '@/api/client'
import { formatMoney } from '@/utils/money'
import { defaultVariant } from '@/utils/product'

const route = useRoute()
const router = useRouter()
const cart = useCartStore()
const catalog = useCatalogStore()

const product = ref<Product | null>(null)
const loading = ref(true)
const error = ref<'notfound' | 'failed' | null>(null)
const variantId = ref<number | null>(null)
const qty = ref(1)
const note = ref('')
const added = ref(false)

async function load() {
  loading.value = true
  error.value = null
  added.value = false
  try {
    const p = await catalog.fetchProduct(String(route.params.slug))
    product.value = p
    variantId.value = defaultVariant(p)?.id ?? null
    qty.value = 1
    note.value = ''
  } catch (e) {
    error.value = apiError(e).status === 404 ? 'notfound' : 'failed'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => route.params.slug, load)

const variant = computed(() => product.value?.variants.find((v) => v.id === variantId.value))
const total = computed(() => (variant.value?.price ?? 0) * qty.value)
const offer = computed(() =>
  product.value?.active_offer?.type === 'percentage' ? product.value.active_offer : null,
)

function back() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}
function add() {
  if (!product.value || !variant.value) return
  cart.addProduct(product.value, variant.value.id, qty.value, note.value.trim())
  added.value = true
}
</script>

<template>
  <div class="pb-32">
    <div v-if="loading" class="flex flex-col gap-4">
      <Skeleton class="h-[280px] rounded-none" />
      <div class="flex flex-col gap-3 px-4">
        <Skeleton class="h-8 w-2/3" />
        <Skeleton class="h-20" />
        <Skeleton class="h-16" />
      </div>
    </div>

    <template v-else-if="error">
      <button
        type="button"
        aria-label="رجوع"
        class="m-3.5 flex h-11 w-11 items-center justify-center rounded-full bg-white text-ink"
        @click="back"
      >
        <ChevronRight class="h-6 w-6" aria-hidden="true" />
      </button>
      <EmptyState
        :icon="PackageX"
        :text="error === 'notfound' ? 'المنتج ده مش موجود' : 'حصلت مشكلة في تحميل المنتج'"
        :action-label="error === 'notfound' ? 'ارجع للرئيسية' : 'حاول تاني'"
        :to="error === 'notfound' ? '/' : undefined"
        @action="load"
      />
    </template>

    <template v-else-if="product">
      <div
        class="relative flex h-[280px] items-center justify-center"
        :style="{ backgroundColor: product.category.color }"
      >
        <img
          v-if="product.image"
          :src="product.image"
          :alt="product.name"
          fetchpriority="high"
          decoding="async"
          class="h-full w-full object-cover"
        />
        <CategoryIcon v-else :name="product.category.icon" class="h-[120px] w-[120px]" />
        <button
          type="button"
          aria-label="رجوع"
          class="absolute start-3.5 top-3.5 flex h-11 w-11 items-center justify-center rounded-full bg-white text-ink"
          @click="back"
        >
          <ChevronRight class="h-6 w-6" aria-hidden="true" />
        </button>
        <span
          v-if="offer"
          class="absolute bottom-3.5 start-3.5 rounded-full bg-danger px-3 py-1 text-[13px] font-bold text-white"
        >
          عليه خصم {{ offer.value }}%
        </span>
      </div>

      <div class="flex flex-col gap-[18px] px-4 py-[18px]">
        <div class="flex flex-wrap items-center gap-2">
          <span
            class="rounded-full bg-primary-soft px-3 py-1 text-[12px] font-bold text-brand-deep"
            >{{ product.category.name }}</span
          >
          <span
            v-if="product.is_available"
            class="rounded-full bg-success-soft px-3 py-1 text-[12px] font-bold text-success"
            >متوفر</span
          >
          <span
            v-else
            class="rounded-full bg-danger-soft px-3 py-1 text-[12px] font-bold text-danger"
            >خلصان</span
          >
        </div>
        <div class="flex flex-col gap-2">
          <h1 class="text-[26px] font-extrabold leading-tight text-ink">{{ product.name }}</h1>
          <p v-if="product.description" class="text-[15px] leading-[1.7] text-ink-2">
            {{ product.description }}
          </p>
        </div>

        <section class="flex flex-col gap-2.5">
          <h2 class="text-[16px] font-extrabold text-ink">اختار الوزن</h2>
          <div class="grid grid-cols-3 gap-2.5">
            <button
              v-for="v in product.variants"
              :key="v.id"
              type="button"
              :aria-pressed="v.id === variantId"
              :class="[
                'flex min-h-16 flex-col items-center justify-center rounded-btn border-2 px-1 py-2',
                v.id === variantId ? 'border-primary bg-primary-tint' : 'border-border bg-white',
              ]"
              @click="variantId = v.id"
            >
              <span class="text-[14px] font-bold text-ink">{{ v.label }}</span>
              <span class="text-[13px] text-muted">{{ formatMoney(v.price) }}</span>
            </button>
          </div>
        </section>

        <div class="flex items-center justify-between">
          <span class="text-[16px] font-extrabold text-ink">الكمية</span>
          <QtyStepper v-model="qty" :min="1" :name="product.name" />
        </div>

        <Input
          v-model="note"
          label="ملاحظة للمحل (اختياري)"
          multiline
          :rows="2"
          placeholder="مثلاً: عايزه مطحون ناعم"
        />

        <div
          v-if="added"
          role="status"
          class="flex items-center justify-between rounded-card bg-success-soft px-4 py-3 text-success-strong"
        >
          <span class="text-[15px] font-extrabold">اتضاف للسلة</span>
          <RouterLink
            to="/cart"
            class="inline-flex min-h-[44px] items-center font-bold text-success"
          >
            روح للسلة
          </RouterLink>
        </div>
      </div>

      <div
        class="pb-safe fixed inset-x-0 bottom-0 z-40 mx-auto flex max-w-app items-center gap-4 border-t border-border bg-surface px-4 pb-[18px] pt-3"
      >
        <div class="flex flex-col leading-tight">
          <span class="text-[12px] font-semibold text-muted">الإجمالي</span>
          <span class="text-[20px] font-extrabold text-ink">{{ formatMoney(total) }}</span>
        </div>
        <button
          type="button"
          :disabled="!product.is_available || !variant"
          class="inline-flex h-[52px] flex-1 items-center justify-center gap-2 rounded-btn bg-primary text-[16px] font-extrabold text-ink disabled:bg-disabled disabled:text-disabled-text"
          @click="add"
        >
          <template v-if="product.is_available">
            <ShoppingCart class="h-5 w-5" aria-hidden="true" />
            أضف للسلة
          </template>
          <template v-else>المنتج خلصان حالياً</template>
        </button>
      </div>
    </template>
  </div>
</template>

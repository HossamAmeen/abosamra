<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Tag, Truck } from 'lucide-vue-next'
import AppLogo from '@/components/ui/AppLogo.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import OfferBanner from '@/components/ui/OfferBanner.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import ProductCard from '@/components/store/ProductCard.vue'
import { useProgressive } from '@/composables/useProgressive'
import { useToast } from '@/composables/useToast'
import { useCartStore } from '@/stores/cart'
import { useCatalogStore } from '@/stores/catalog'
import type { Offer, Product } from '@/types/api'
import { formatWeekdayDate } from '@/utils/date'
import { isDiscounted } from '@/utils/product'
import { formatMoney } from '@/utils/money'

const catalog = useCatalogStore()
const cart = useCartStore()
const toast = useToast()

const products = ref<Product[]>([])
const loadingProducts = ref(true)
const shownProducts = useProgressive(products, 2, 2)

onMounted(async () => {
  catalog.loadOffers(true)
  catalog.loadCategories()
  try {
    products.value = (await catalog.fetchProducts({ discounted: true })).results.filter(
      isDiscounted,
    )
  } catch {
    products.value = []
  } finally {
    loadingProducts.value = false
  }
})

const percentTitle = (o: Offer) => o.name.replace(/^خصم\s+/, '')

function shopLabel(o: Offer): string {
  if (o.target?.kind === 'category') {
    const name = catalog.categoryBySlug(o.target.slug ?? '')?.name
    if (name) return name.includes(' ') ? `تسوّق ${name}` : `تسوّق ال${name}`
  }
  return 'تسوّق كل المنتجات'
}
const shopTo = (o: Offer) =>
  o.target?.kind === 'category' && o.target.slug
    ? `/categories/${o.target.slug}`
    : '/categories/all'

const percentSub = (o: Offer) =>
  (o.ends_at ? `ساري لحد ${formatWeekdayDate(o.ends_at)} · ` : '') + 'الخصم بيتحسب لوحده في السلة'

const bundleItems = (o: Offer) =>
  o.bundle_items.map((i) => (i.qty > 1 ? `${i.name} ×${i.qty}` : i.name)).join(' + ')

function addBundle(o: Offer) {
  cart.addBundle(o)
  toast.show('اتضاف للسلة')
}
const none = computed(
  () => catalog.offersLoaded && !catalog.loadingOffers && catalog.offers.length === 0,
)
</script>

<template>
  <div>
    <header class="flex items-center justify-between border-b border-border bg-surface px-4 py-3">
      <h1 class="text-[22px] font-extrabold text-ink">العروض</h1>
      <AppLogo :size="36" />
    </header>

    <div class="flex flex-col gap-5 px-4 pt-4">
      <div class="flex flex-col gap-3.5">
        <Skeleton
          v-if="!catalog.offersLoaded && !catalog.offers.length"
          class="h-36 rounded-banner"
        />
        <EmptyState
          v-if="none"
          :icon="Tag"
          text="مفيش عروض دلوقتي"
          action-label="ابدأ التسوق"
          to="/"
        />
        <template v-for="o in catalog.offers" :key="o.id">
          <OfferBanner v-if="o.type === 'percentage'" variant="dark">
            <span class="rounded-full bg-primary px-3 py-1 text-[12px] font-bold text-ink"
              >خصم</span
            >
            <span class="text-[22px] font-extrabold leading-snug text-on-dark">{{
              percentTitle(o)
            }}</span>
            <span class="text-[13px] text-on-dark-sub">{{ percentSub(o) }}</span>
            <RouterLink
              :to="shopTo(o)"
              class="inline-flex h-11 items-center rounded-field bg-primary px-4 text-[14px] font-bold text-ink"
            >
              {{ shopLabel(o) }}
            </RouterLink>
          </OfferBanner>

          <OfferBanner v-else-if="o.type === 'bundle'" variant="soft">
            <span class="rounded-full bg-white px-3 py-1 text-[12px] font-bold text-brand-deep"
              >باكدج</span
            >
            <span class="text-[20px] font-extrabold text-ink">{{ o.name }}</span>
            <span class="text-[14px] text-ink-2">{{ bundleItems(o) }}</span>
            <div class="flex items-baseline gap-2">
              <span class="text-[20px] font-extrabold text-ink">{{
                formatMoney(o.bundle_price ?? 0)
              }}</span>
              <span
                v-if="o.old_price && o.old_price > (o.bundle_price ?? 0)"
                class="text-[13px] font-semibold text-muted line-through"
                >{{ formatMoney(o.old_price) }}</span
              >
            </div>
            <template #end>
              <button
                type="button"
                class="h-12 shrink-0 rounded-btn bg-primary px-4 text-[15px] font-extrabold text-ink"
                @click="addBundle(o)"
              >
                أضف الباكدج
              </button>
            </template>
          </OfferBanner>

          <OfferBanner v-else variant="success">
            <div class="flex items-center gap-3">
              <span
                class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white"
              >
                <Truck class="h-6 w-6 text-success" aria-hidden="true" />
              </span>
              <div class="flex flex-col">
                <span class="text-[18px] font-extrabold">توصيل مجاني</span>
                <span class="text-[14px] font-semibold"
                  >على أي طلب فوق {{ formatMoney(o.min_order ?? 0) }}</span
                >
              </div>
            </div>
          </OfferBanner>
        </template>
      </div>

      <section
        v-if="catalog.offersLoaded && (loadingProducts || products.length)"
        class="flex flex-col gap-2"
      >
        <SectionHeader title="منتجات عليها خصم" />
        <div class="grid grid-cols-2 gap-3">
          <template v-if="loadingProducts">
            <Skeleton v-for="i in 4" :key="i" class="h-[210px] rounded-card" />
          </template>
          <ProductCard v-for="p in shownProducts" v-else :key="p.id" :product="p" />
        </div>
      </section>
    </div>
  </div>
</template>

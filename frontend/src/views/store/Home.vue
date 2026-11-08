<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Search, ShoppingCart } from 'lucide-vue-next'
import SpiceIcon from '@/components/ui/SpiceIcon.vue'
import AppLogo from '@/components/ui/AppLogo.vue'
import CategoryIcon from '@/components/ui/CategoryIcon.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import OfferBanner from '@/components/ui/OfferBanner.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import InstallPrompt from '@/components/store/InstallPrompt.vue'
import ProductCard from '@/components/store/ProductCard.vue'
import { useProgressive } from '@/composables/useProgressive'
import { useCartStore } from '@/stores/cart'
import { useCatalogStore } from '@/stores/catalog'
import type { Product } from '@/types/api'
import { weekdayName } from '@/utils/date'
import { formatMoney } from '@/utils/money'
import { defaultVariant, isDiscounted } from '@/utils/product'

const router = useRouter()
const route = useRoute()
const cart = useCartStore()
const catalog = useCatalogStore()

const discounted = ref<Product[]>([])
const featured = ref<Product[]>([])
const loading = ref(true)
const shownDiscounted = useProgressive(discounted, 2, 2)
const shownFeatured = useProgressive(featured, 2, 2)
const failed = ref(false)

async function loadProducts() {
  loading.value = true
  failed.value = false
  try {
    const [d, f] = await Promise.all([
      catalog.fetchProducts({ discounted: true }),
      catalog.fetchProducts({ featured: true }),
    ])
    discounted.value = d.results.filter(isDiscounted)
    featured.value = f.results
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}
onMounted(() => {
  catalog.loadCategories()
  catalog.loadOffers()
  loadProducts()
})

// ---- search (debounced 300 ms) ----
const query = ref('')
const results = ref<Product[]>([])
const searching = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined
let seq = 0

watch(query, (q) => {
  clearTimeout(timer)
  const term = q.trim()
  if (!term) {
    results.value = []
    searching.value = false
    seq++
    return
  }
  searching.value = true
  timer = setTimeout(async () => {
    const mine = ++seq
    try {
      const res = await catalog.fetchProducts({ q: term })
      if (mine === seq) results.value = res.results.slice(0, 6)
    } catch {
      if (mine === seq) results.value = []
    } finally {
      if (mine === seq) searching.value = false
    }
  }, 300)
})
watch(
  () => route.fullPath,
  () => (query.value = ''),
)
onBeforeUnmount(() => clearTimeout(timer))

function submitSearch() {
  const term = query.value.trim()
  if (term) router.push({ path: '/categories/all', query: { q: term } })
}

const offer = computed(() => catalog.featuredOffer)
const offerSub = computed(() =>
  offer.value?.ends_at
    ? `لحد يوم ${weekdayName(offer.value.ends_at)} · اطلب دلوقتي`
    : 'اطلب دلوقتي',
)
</script>

<template>
  <div>
    <header class="relative z-20 rounded-b-band bg-primary px-4 pb-5 pt-4">
      <div class="flex flex-col gap-3.5">
        <div class="flex items-center justify-between">
          <AppLogo :size="48" on-orange />
          <RouterLink
            to="/cart"
            :aria-label="`السلة، ${cart.count} منتج`"
            class="relative flex h-12 w-12 items-center justify-center rounded-full bg-white text-ink"
          >
            <ShoppingCart class="h-6 w-6" aria-hidden="true" />
            <span
              v-if="cart.count > 0"
              class="absolute -end-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-danger px-1 text-[11px] font-bold text-white"
              >{{ cart.count }}</span
            >
          </RouterLink>
        </div>
        <p class="text-[16px] font-bold text-ink">أهلاً بيك.. عايز تطلب إيه النهاردة؟</p>
        <form class="relative" role="search" @submit.prevent="submitSearch">
          <Search
            class="pointer-events-none absolute start-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-muted"
            aria-hidden="true"
          />
          <input
            v-model="query"
            type="search"
            enterkeyhint="search"
            aria-label="بحث عن منتج"
            placeholder="دوّر على كمون، عسل، ينسون..."
            class="h-[50px] w-full rounded-btn border-0 bg-white ps-11 pe-3 text-[15px] text-ink placeholder:text-muted/70"
          />
          <ul
            v-if="query.trim()"
            class="absolute inset-x-0 top-[56px] z-30 max-h-72 overflow-y-auto rounded-card border border-border bg-white shadow-sm"
            aria-label="نتائج البحث"
          >
            <li v-if="searching" class="px-4 py-3 text-[14px] font-semibold text-muted">
              بندوّر...
            </li>
            <li
              v-else-if="results.length === 0"
              class="px-4 py-3 text-[14px] font-semibold text-muted"
            >
              مفيش نتايج
            </li>
            <li v-for="p in results" v-else :key="p.id">
              <RouterLink
                :to="`/products/${p.slug}`"
                class="flex min-h-[48px] items-center justify-between gap-3 border-b border-border px-4 py-2 last:border-b-0"
              >
                <span class="text-[15px] font-bold text-ink">{{ p.name }}</span>
                <span class="text-[13px] font-semibold text-muted">
                  {{ defaultVariant(p) ? formatMoney(defaultVariant(p)!.price) : '' }}
                </span>
              </RouterLink>
            </li>
          </ul>
        </form>
      </div>
    </header>
    <InstallPrompt />

    <div class="flex flex-col gap-5 px-4 pt-5">
      <OfferBanner v-if="offer" to="/offers" variant="dark">
        <span class="rounded-full bg-primary px-3 py-1 text-[12px] font-bold text-ink"
          >عرض الأسبوع</span
        >
        <span class="text-[21px] font-extrabold leading-snug text-on-dark">{{ offer.name }}</span>
        <span class="text-[13px] text-on-dark-sub">{{ offerSub }}</span>
        <template #end>
          <span
            class="flex h-[76px] w-[76px] shrink-0 items-center justify-center rounded-full bg-primary"
          >
            <SpiceIcon class="h-9 w-9 text-ink" aria-hidden="true" />
          </span>
        </template>
      </OfferBanner>
      <Skeleton v-else-if="!catalog.offersLoaded" class="h-[120px] rounded-banner" />

      <section class="flex flex-col gap-2">
        <SectionHeader title="الأقسام" to="/categories/all" />
        <div v-if="catalog.loadingCategories" class="grid grid-cols-3 gap-2.5">
          <Skeleton v-for="i in 6" :key="i" class="h-[104px] rounded-card" />
        </div>
        <div v-else-if="catalog.error && !catalog.categories.length" class="text-center">
          <p class="text-[14px] font-semibold text-danger">حصلت مشكلة في تحميل الأقسام</p>
          <button
            type="button"
            class="min-h-[44px] font-bold text-link"
            @click="catalog.loadCategories(true)"
          >
            حاول تاني
          </button>
        </div>
        <ul v-else class="grid grid-cols-3 gap-2.5">
          <li v-for="c in catalog.categories" :key="c.id">
            <RouterLink
              :to="`/categories/${c.slug}`"
              class="flex flex-col items-center gap-2 rounded-card border border-border bg-surface px-1 py-3"
            >
              <span
                class="flex h-[54px] w-[54px] items-center justify-center rounded-full"
                :style="{ backgroundColor: c.color }"
              >
                <CategoryIcon :name="c.icon" class="h-7 w-7" />
              </span>
              <span class="text-center text-[13px] font-bold text-ink">{{ c.name }}</span>
            </RouterLink>
          </li>
        </ul>
      </section>

      <div v-if="failed" class="text-center">
        <p class="text-[14px] font-semibold text-danger">حصلت مشكلة في تحميل المنتجات</p>
        <button type="button" class="min-h-[44px] font-bold text-link" @click="loadProducts">
          حاول تاني
        </button>
      </div>

      <section v-if="loading || discounted.length" class="flex flex-col gap-2">
        <SectionHeader title="عروض النهاردة" to="/offers" />
        <div class="no-scrollbar -mx-4 flex gap-3 overflow-x-auto px-4">
          <template v-if="loading">
            <Skeleton v-for="i in 3" :key="i" class="h-[210px] w-[156px] shrink-0 rounded-card" />
          </template>
          <ProductCard
            v-for="p in shownDiscounted"
            v-else
            :key="p.id"
            :product="p"
            class="w-[156px] shrink-0"
          />
        </div>
      </section>

      <section class="flex flex-col gap-2">
        <SectionHeader title="الأكثر طلباً" />
        <div v-if="loading" class="grid grid-cols-2 gap-3">
          <Skeleton v-for="i in 4" :key="i" class="h-[210px] rounded-card" />
        </div>
        <EmptyState
          v-else-if="!failed && !featured.length"
          :icon="SpiceIcon"
          text="مفيش منتجات دلوقتي"
        />
        <div v-else class="grid grid-cols-2 gap-3">
          <ProductCard v-for="p in shownFeatured" :key="p.id" :product="p" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, SearchX } from 'lucide-vue-next'
import Chip from '@/components/ui/Chip.vue'
import ChipRow from '@/components/ui/ChipRow.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import TopBar from '@/components/ui/TopBar.vue'
import CartBar from '@/components/store/CartBar.vue'
import ProductCard from '@/components/store/ProductCard.vue'
import { useProgressive } from '@/composables/useProgressive'
import { useCartStore } from '@/stores/cart'
import { useCatalogStore } from '@/stores/catalog'
import type { Product } from '@/types/api'

const route = useRoute()
const router = useRouter()
const catalog = useCatalogStore()
const cart = useCartStore()

const slug = computed(() => (route.params.slug as string | undefined) || 'all')
const q = computed(() => (typeof route.query.q === 'string' ? route.query.q : ''))
const title = computed(() =>
  slug.value === 'all' ? 'كل المنتجات' : (catalog.categoryBySlug(slug.value)?.name ?? ''),
)

const products = ref<Product[]>([])
const shownProducts = useProgressive(products, 6)
const count = ref(0)
const page = ref(1)
const hasMore = ref(false)
const loading = ref(true)
const loadingMore = ref(false)
const failed = ref(false)
let seq = 0

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
    const res = await catalog.fetchProducts({
      category: slug.value === 'all' ? undefined : slug.value,
      q: q.value || undefined,
      page: page.value,
    })
    if (mine !== seq) return
    products.value = reset ? res.results : [...products.value, ...res.results]
    count.value = res.count
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

onMounted(() => {
  catalog.loadCategories()
  load()
})
watch([slug, q], () => load())

function select(target: string) {
  router.push({ path: `/categories/${target}`, query: q.value ? { q: q.value } : {} })
}

// search toggle (end action of the TopBar)
const searchOpen = ref(!!q.value)
const term = ref(q.value)
watch(q, (v) => (term.value = v))
function submitSearch() {
  const t = term.value.trim()
  router.push({ path: route.path, query: t ? { q: t } : {} })
}
</script>

<template>
  <div :class="cart.isEmpty ? '' : 'pb-20'">
    <TopBar :title="title" back-to="/">
      <template #action>
        <button
          type="button"
          aria-label="بحث"
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary-tint text-brand-deep"
          @click="searchOpen = !searchOpen"
        >
          <Search class="h-5 w-5" aria-hidden="true" />
        </button>
      </template>
    </TopBar>

    <form
      v-if="searchOpen"
      class="bg-surface px-4 pb-3"
      role="search"
      @submit.prevent="submitSearch"
    >
      <input
        v-model="term"
        type="search"
        aria-label="بحث عن منتج"
        placeholder="دوّر على كمون، عسل، ينسون..."
        class="h-[50px] w-full rounded-field border border-input-border bg-white px-3.5 text-[15px] text-ink"
      />
    </form>

    <ChipRow>
      <Chip :selected="slug === 'all'" @click="select('all')">الكل</Chip>
      <Chip
        v-for="c in catalog.categories"
        :key="c.id"
        :selected="slug === c.slug"
        @click="select(c.slug)"
      >
        {{ c.name }}
      </Chip>
    </ChipRow>

    <div class="px-4">
      <p v-if="!loading && !failed" class="mb-3 text-[13px] font-semibold text-muted">
        {{ count }} منتج
      </p>

      <div v-if="loading" class="grid grid-cols-2 gap-3">
        <Skeleton v-for="i in 6" :key="i" class="h-[250px] rounded-card" />
      </div>
      <div v-else-if="failed && !products.length" class="py-8 text-center">
        <p class="text-[14px] font-semibold text-danger">حصلت مشكلة في تحميل المنتجات</p>
        <button type="button" class="min-h-[44px] font-bold text-link" @click="load()">
          حاول تاني
        </button>
      </div>
      <EmptyState
        v-else-if="!products.length"
        :icon="SearchX"
        text="مفيش منتجات هنا"
        action-label="شوف كل المنتجات"
        to="/categories/all"
      />
      <template v-else>
        <div class="grid grid-cols-2 gap-3">
          <ProductCard v-for="p in shownProducts" :key="p.id" :product="p" mode="stepper" />
        </div>
        <div class="flex justify-center py-4">
          <button
            v-if="hasMore"
            type="button"
            class="h-11 rounded-field bg-primary-tint px-6 text-[14px] font-bold text-brand-deep"
            :disabled="loadingMore"
            @click="load(false)"
          >
            {{ loadingMore ? 'بنحمّل...' : 'عرض المزيد' }}
          </button>
          <p v-if="failed" class="text-[13px] font-semibold text-danger">حصلت مشكلة، حاول تاني</p>
        </div>
      </template>
    </div>
    <CartBar />
  </div>
</template>

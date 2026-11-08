<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Pencil, Plus, Search, SearchX } from 'lucide-vue-next'
import { listAdminProducts, setProductAvailability } from '@/api/admin/products'
import AdminHeader from '@/components/admin/AdminHeader.vue'
import Chip from '@/components/ui/Chip.vue'
import ChipRow from '@/components/ui/ChipRow.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ProductThumb from '@/components/ui/ProductThumb.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue'
import { useToast } from '@/composables/useToast'
import { useCatalogStore } from '@/stores/catalog'
import type { AdminProduct } from '@/types/api'
import { formatMoney } from '@/utils/money'

const catalog = useCatalogStore()
const toast = useToast()
catalog.loadCategories()

const q = ref('')
const category = ref('all')
const products = ref<AdminProduct[]>([])
const page = ref(1)
const hasMore = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const failed = ref(false)
let seq = 0
let timer: ReturnType<typeof setTimeout> | undefined

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
    const res = await listAdminProducts({
      category: category.value === 'all' ? undefined : category.value,
      q: q.value.trim() || undefined,
      page: page.value,
    })
    if (mine !== seq) return
    products.value = reset ? res.results : [...products.value, ...res.results]
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

watch(category, () => load(), { immediate: true })
watch(q, () => {
  clearTimeout(timer)
  timer = setTimeout(() => load(), 300)
})
onBeforeUnmount(() => clearTimeout(timer))

async function toggle(p: AdminProduct, value: boolean) {
  const previous = p.is_available
  p.is_available = value // optimistic
  try {
    await setProductAvailability(p.id, value)
  } catch {
    p.is_available = previous
    toast.show('معرفناش نغيّر حالة المنتج، جرّب تاني', { duration: 4000 })
  }
}

function summary(p: AdminProduct) {
  const v = p.variants.find((x) => x.is_default) ?? p.variants[0]
  return v ? `${v.label} · ${formatMoney(v.price)}` : ''
}
</script>

<template>
  <div>
    <AdminHeader title="المنتجات">
      <template #action>
        <RouterLink
          to="/admin/products/new"
          class="inline-flex h-11 items-center gap-1.5 rounded-field bg-primary px-3 text-[14px] font-extrabold text-ink"
        >
          <Plus class="h-5 w-5" aria-hidden="true" />
          منتج جديد
        </RouterLink>
      </template>
    </AdminHeader>

    <div class="px-4 pt-3">
      <div class="relative">
        <input
          v-model="q"
          type="search"
          aria-label="ابحث باسم المنتج"
          placeholder="ابحث باسم المنتج"
          class="h-[50px] w-full rounded-field border border-input-border bg-white ps-11 pe-[14px] text-[15px] text-ink"
        />
        <Search
          class="pointer-events-none absolute start-3 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-2"
          aria-hidden="true"
        />
      </div>
    </div>
    <ChipRow aria-label="الأقسام">
      <Chip size="admin" :selected="category === 'all'" @click="category = 'all'">الكل</Chip>
      <Chip
        v-for="c in catalog.categories"
        :key="c.slug"
        size="admin"
        :selected="category === c.slug"
        @click="category = c.slug"
      >
        {{ c.name }}
      </Chip>
    </ChipRow>

    <div class="flex flex-col gap-2 px-4 pb-4">
      <template v-if="loading">
        <Skeleton v-for="i in 5" :key="i" class="h-[80px]" />
      </template>
      <p v-else-if="failed" class="text-[14px] font-bold text-danger" role="alert">
        مقدرناش نحمّل المنتجات
        <button type="button" class="min-h-[44px] ms-2 text-link underline" @click="load()">
          حاول تاني
        </button>
      </p>
      <EmptyState v-else-if="!products.length" :icon="SearchX" text="مفيش منتجات هنا" />
      <template v-else>
        <article
          v-for="p in products"
          :key="p.id"
          class="flex items-center gap-3 rounded-card border border-border bg-surface p-3"
        >
          <div class="h-14 w-14 shrink-0">
            <ProductThumb
              :image="p.image"
              :alt="p.name"
              :tint="p.category.color"
              :icon="p.category.icon"
              :icon-size="28"
            />
          </div>
          <div class="min-w-0 flex-1">
            <h3 class="truncate text-[15px] font-bold text-ink">{{ p.name }}</h3>
            <p class="truncate text-[13px] text-ink-2">{{ summary(p) }}</p>
          </div>
          <ToggleSwitch
            :model-value="p.is_available"
            :aria-label="`${p.name}: متوفر`"
            @update:model-value="toggle(p, $event)"
          />
          <RouterLink
            :to="`/admin/products/${p.id}`"
            :aria-label="`تعديل ${p.name}`"
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-field bg-primary-tint text-brand-deep"
          >
            <Pencil class="h-5 w-5" aria-hidden="true" />
          </RouterLink>
        </article>
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
  </div>
</template>

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as catalogApi from '@/api/catalog'
import type { Category, Offer, Paginated, Product, ProductsQuery } from '@/types/api'

export const useCatalogStore = defineStore('catalog', () => {
  const categories = ref<Category[]>([])
  const offers = ref<Offer[]>([])
  const loadingCategories = ref(false)
  const loadingOffers = ref(false)
  /** True once the first offers request has settled (so the empty state never flashes before it). */
  const offersLoaded = ref(false)
  const error = ref(false)

  const featuredOffer = computed(
    () => offers.value.find((o) => o.is_featured) ?? offers.value[0] ?? null,
  )
  const percentageOffers = computed(() => offers.value.filter((o) => o.type === 'percentage'))
  const bundleOffers = computed(() => offers.value.filter((o) => o.type === 'bundle'))
  const freeDeliveryOffer = computed(
    () => offers.value.find((o) => o.type === 'free_delivery') ?? null,
  )

  function categoryBySlug(slug: string) {
    return categories.value.find((c) => c.slug === slug)
  }

  async function loadCategories(force = false) {
    if ((categories.value.length && !force) || loadingCategories.value) return
    loadingCategories.value = true
    error.value = false
    try {
      categories.value = await catalogApi.getCategories()
    } catch {
      error.value = true
    } finally {
      loadingCategories.value = false
    }
  }

  async function loadOffers(force = false) {
    if ((offers.value.length && !force) || loadingOffers.value) return
    loadingOffers.value = true
    try {
      offers.value = await catalogApi.getOffers()
    } catch {
      error.value = true
    } finally {
      loadingOffers.value = false
      offersLoaded.value = true
    }
  }

  const fetchProducts = (query: ProductsQuery = {}): Promise<Paginated<Product>> =>
    catalogApi.getProducts(query)
  const fetchProduct = (slug: string) => catalogApi.getProduct(slug)

  return {
    categories,
    offers,
    error,
    loadingCategories,
    loadingOffers,
    offersLoaded,
    featuredOffer,
    percentageOffers,
    bundleOffers,
    freeDeliveryOffer,
    categoryBySlug,
    loadCategories,
    loadOffers,
    fetchProducts,
    fetchProduct,
  }
})

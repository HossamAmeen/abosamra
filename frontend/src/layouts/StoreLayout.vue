<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import OfflineBanner from '@/components/ui/OfflineBanner.vue'
import BottomNav from '@/components/ui/BottomNav.vue'
import { useCartStore } from '@/stores/cart'
import { useCatalogStore } from '@/stores/catalog'
import { useSettingsStore } from '@/stores/settings'

const route = useRoute()
const cart = useCartStore()
const catalog = useCatalogStore()
const settings = useSettingsStore()

onMounted(() => {
  settings.load()
  catalog.loadCategories()
  catalog.loadOffers()
})
</script>

<template>
  <div class="mx-auto min-h-screen max-w-app bg-bg pb-24">
    <OfflineBanner />
    <main>
      <RouterView />
    </main>
    <BottomNav v-if="!route.meta.hideNav" variant="store" :cart-count="cart.count" />
  </div>
</template>

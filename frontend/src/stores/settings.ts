import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getSettings } from '@/api/catalog'
import type { ShopSettings } from '@/types/api'

const DEFAULTS: ShopSettings = {
  shop_name: 'أبو سمرة',
  phone: '',
  whatsapp: '',
  delivery_fee: 30,
  free_delivery_threshold: 500,
  currency: 'EGP',
  is_accepting_orders: true,
}

export const useSettingsStore = defineStore(
  'settings',
  () => {
    const settings = ref<ShopSettings>({ ...DEFAULTS })
    const loaded = ref(false)
    const loading = ref(false)
    const error = ref(false)

    const deliveryFee = computed(() => settings.value.delivery_fee)
    const freeDeliveryThreshold = computed(() => settings.value.free_delivery_threshold)
    const shopPhone = computed(() => settings.value.phone)
    const isAcceptingOrders = computed(() => settings.value.is_accepting_orders)

    async function load(force = false) {
      if ((loaded.value && !force) || loading.value) return
      loading.value = true
      error.value = false
      try {
        settings.value = await getSettings()
        loaded.value = true
      } catch {
        error.value = true // keep cached/default values (works offline)
      } finally {
        loading.value = false
      }
    }

    return {
      settings,
      loaded,
      loading,
      error,
      deliveryFee,
      freeDeliveryThreshold,
      shopPhone,
      isAcceptingOrders,
      load,
    }
  },
  { persist: { pick: ['settings'] } },
)

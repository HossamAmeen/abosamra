import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getOrderCounts } from '@/api/admin/orders'

/** Shared admin state: the count of new orders shown on the nav badge. */
export const useAdminStore = defineStore('admin', () => {
  const pending = ref(0)

  async function refreshPending() {
    try {
      pending.value = (await getOrderCounts()).new
    } catch {
      /* keep the last known value */
    }
  }

  return { pending, refreshPending }
})

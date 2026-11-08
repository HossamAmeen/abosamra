<script setup lang="ts">
import { watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import OfflineBanner from '@/components/ui/OfflineBanner.vue'
import BottomNav from '@/components/ui/BottomNav.vue'
import { usePolling } from '@/composables/usePolling'
import { useAdminStore } from '@/stores/admin'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const admin = useAdminStore()

usePolling(() => admin.refreshPending(), 30000)

// A failed token refresh clears the session: send the owner back to the login screen.
watch(
  () => auth.isStaff,
  (staff) => {
    if (!staff) router.replace({ name: 'admin-login', query: { next: route.fullPath } })
  },
)
</script>

<template>
  <div class="mx-auto min-h-screen max-w-admin bg-bg pb-24">
    <OfflineBanner />
    <main>
      <RouterView />
    </main>
    <BottomNav v-if="!route.meta.hideNav" variant="admin" :orders-badge="admin.pending" />
  </div>
</template>

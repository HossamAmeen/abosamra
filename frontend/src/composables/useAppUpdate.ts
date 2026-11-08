import { useToast } from '@/composables/useToast'

/**
 * Registers the Workbox service worker (production, real API only: MSW owns the
 * root scope while VITE_USE_MOCKS=true) and shows the update toast when a new
 * version is waiting.
 */
export async function registerServiceWorker() {
  if (!import.meta.env.PROD || import.meta.env.VITE_USE_MOCKS === 'true') return
  if (!('serviceWorker' in navigator)) return
  const { registerSW } = await import('virtual:pwa-register')
  const toast = useToast()
  const update = registerSW({
    onNeedRefresh() {
      toast.show('فيه نسخة جديدة', {
        duration: 0,
        actionLabel: 'تحديث',
        onAction: () => void update(true),
      })
    },
  })
}

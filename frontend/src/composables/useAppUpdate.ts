import { useToast } from '@/composables/useToast'

/** Version of the running bundle: VITE_APP_VERSION from frontend/.env.production. */
export const APP_VERSION: string = import.meta.env.VITE_APP_VERSION || 'dev'

/** How often an open app checks the server for a new deploy. */
export const UPDATE_CHECK_INTERVAL = 5 * 60 * 1000

/** The version currently deployed on the server (dist/version.json), or null if unknown. */
export async function fetchServerVersion(): Promise<string | null> {
  try {
    const res = await fetch(`/version.json?t=${Date.now()}`, { cache: 'no-store' })
    if (!res.ok) return null
    const body = (await res.json()) as { version?: unknown }
    return typeof body.version === 'string' ? body.version : null
  } catch {
    return null
  }
}

export function updateMessage(serverVersion: string | null): string {
  return serverVersion && serverVersion !== APP_VERSION
    ? `فيه نسخة جديدة (${serverVersion})`
    : 'فيه نسخة جديدة'
}

/**
 * Registers the Workbox service worker (production, real API only: MSW owns the
 * root scope while VITE_USE_MOCKS=true). An open app re-checks for a new deploy
 * every few minutes and whenever it comes back to the foreground; when a new
 * version is waiting it shows a toast with the new version number.
 */
export async function registerServiceWorker() {
  if (!import.meta.env.PROD || import.meta.env.VITE_USE_MOCKS === 'true') return
  if (!('serviceWorker' in navigator)) return
  const { registerSW } = await import('virtual:pwa-register')
  const toast = useToast()
  let notified = false
  const update = registerSW({
    async onNeedRefresh() {
      if (notified) return
      notified = true
      toast.show(updateMessage(await fetchServerVersion()), {
        duration: 0,
        actionLabel: 'تحديث',
        onAction: () => void update(true),
      })
    },
    onRegisteredSW(_url, registration) {
      if (!registration) return
      const check = () => {
        if (notified || document.visibilityState !== 'visible' || !navigator.onLine) return
        registration.update().catch(() => {
          /* offline or server down: try again next time */
        })
      }
      setInterval(check, UPDATE_CHECK_INTERVAL)
      document.addEventListener('visibilitychange', check)
    },
  })
}

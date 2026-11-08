import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import { router } from './router'
import { prefetchLanding } from './api/catalog'
import { registerServiceWorker } from './composables/useAppUpdate'
import { useCatalogStore } from './stores/catalog'
import { useSettingsStore } from './stores/settings'
import { initInstallPrompt } from './composables/useInstallPrompt'
import './styles/main.css'

function whenIdle(fn: () => void) {
  const run = () =>
    'requestIdleCallback' in window ? requestIdleCallback(fn) : setTimeout(fn, 200)
  if (document.readyState === 'complete') run()
  else window.addEventListener('load', run, { once: true })
}

async function enableMocks() {
  if (import.meta.env.VITE_USE_MOCKS === 'true') {
    const { worker } = await import('./mocks/browser')
    await worker.start({ onUnhandledFrame: 'bypass', quiet: true })
  }
}

enableMocks().then(() => {
  const pinia = createPinia()
  pinia.use(piniaPluginPersistedstate)
  createApp(App).use(pinia).use(router).mount('#app')
  // Storefront data does not depend on the route chunk: start the requests now instead of after it loads.
  if (!location.pathname.startsWith('/admin')) {
    useSettingsStore(pinia).load()
    void useCatalogStore(pinia).loadCategories()
    void useCatalogStore(pinia).loadOffers()
    prefetchLanding(location.pathname, location.search)
  }
  initInstallPrompt() // must listen early: `beforeinstallprompt` can fire before load
  // The service worker is not needed for first paint: register it once the page has settled.
  whenIdle(() => void registerServiceWorker())
})

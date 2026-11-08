import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import type { Plugin } from 'vite'

// Preload only the Cairo subsets/weights the storefront paints with first (Arabic text + Latin digits),
// so the font requests start with the HTML instead of after the first render.
function preloadCriticalFonts(): Plugin {
  const critical = [/cairo-arabic-700-normal-.*\.woff2$/, /cairo-arabic-400-normal-.*\.woff2$/]
  return {
    name: 'abosamra-preload-fonts',
    apply: 'build',
    transformIndexHtml: {
      order: 'post',
      handler(_html, ctx) {
        const files = Object.keys(ctx.bundle ?? {}).filter((f) => critical.some((re) => re.test(f)))
        return files.map((f) => ({
          tag: 'link',
          attrs: { rel: 'preload', as: 'font', type: 'font/woff2', href: `/${f}`, crossorigin: '' },
          injectTo: 'head-prepend' as const,
        }))
      },
    },
  }
}

export default defineConfig({
  plugins: [
    vue(),
    preloadCriticalFonts(),
    VitePWA({
      registerType: 'prompt', // the app shows the "فيه نسخة جديدة" toast, then calls update
      injectRegister: false,
      manifest: {
        name: 'أبو سمرة – عطارة وبهارات',
        short_name: 'أبو سمرة',
        lang: 'ar',
        dir: 'rtl',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        orientation: 'portrait',
        theme_color: '#F7A04B',
        background_color: '#FFF8F1',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          {
            src: '/icons/maskable-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
        shortcuts: [
          {
            name: 'العروض',
            url: '/offers',
            icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }],
          },
          {
            name: 'السلة',
            url: '/cart',
            icons: [{ src: '/icons/icon-192.png', sizes: '192x192' }],
          },
        ],
      },
      workbox: {
        // App shell, fonts and icons are precached; the MSW worker never is.
        globPatterns: ['**/*.{js,css,html,woff,woff2,png,svg,ico,webmanifest}'],
        globIgnores: ['**/mockServiceWorker.js'],
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//],
        cleanupOutdatedCaches: true,
        runtimeCaching: [
          {
            // Auth, quote, orders and every admin call: never cached.
            urlPattern: ({ url }) =>
              /\/api\/v1\/(auth|cart|orders|admin|me)(\/|$)/.test(url.pathname),
            handler: 'NetworkOnly',
          },
          {
            urlPattern: ({ url }) =>
              /\/api\/v1\/(categories|products|offers\/active|settings)(\/|$)/.test(url.pathname),
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'catalog-api',
              expiration: { maxAgeSeconds: 24 * 60 * 60, maxEntries: 200 },
              cacheableResponse: { statuses: [200] },
            },
          },
          {
            urlPattern: ({ request }) => request.destination === 'image',
            handler: 'CacheFirst',
            options: {
              cacheName: 'product-images',
              expiration: { maxEntries: 200, maxAgeSeconds: 30 * 24 * 60 * 60 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
    }),
  ],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  test: {
    environment: 'jsdom',
    environmentOptions: { jsdom: { url: 'http://localhost:8000/' } },
    globals: true,
    include: ['src/**/*.spec.ts'],
    setupFiles: ['src/test/setup.ts'],
    env: { VITE_API_BASE_URL: 'http://localhost:8000/api/v1', VITE_USE_MOCKS: 'false' },
  },
})

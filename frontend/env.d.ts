/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_USE_MOCKS: string
  /** Version shown to users and in the update toast (frontend/.env.production). */
  readonly VITE_APP_VERSION?: string
}
interface ImportMeta {
  readonly env: ImportMetaEnv
}

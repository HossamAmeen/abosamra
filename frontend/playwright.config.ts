import { existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig, devices } from '@playwright/test'

// Mock mode (default): vite dev server with MSW. Set E2E_USE_MOCKS=false and
// E2E_BASE_URL to run against a real stack instead.
const useMocks = process.env.E2E_USE_MOCKS !== 'false'
const port = Number(process.env.E2E_PORT ?? 5174)
const pwaPort = Number(process.env.E2E_PWA_PORT ?? 4174)
const baseURL = process.env.E2E_BASE_URL ?? `http://localhost:${port}`

// QA-06 "real-api": `npm run e2e:real` (E2E_REAL=1) runs ONLY the real-api project against a real Django
// backend (fresh sqlite in the tmp dir, migrate + seed_abo_samra) and a vite dev server with
// VITE_USE_MOCKS=false. The default `npm run e2e` never starts the backend.
const realMode = process.env.E2E_REAL === '1'
const realFrontPort = Number(process.env.E2E_REAL_FRONT_PORT ?? 5175)
const realApiPort = Number(process.env.E2E_REAL_API_PORT ?? 8100)
const realDir = join(tmpdir(), 'abosamra-e2e-real')
const backendDir = resolve(dirname(fileURLToPath(import.meta.url)), '../backend')
const backendPython =
  process.env.E2E_BACKEND_PYTHON ??
  (existsSync(join(backendDir, '.venv/bin/python'))
    ? join(backendDir, '.venv/bin/python')
    : 'python')
export const REAL = {
  front: `http://localhost:${realFrontPort}`,
  api: `http://localhost:${realApiPort}/api/v1`,
  admin: { phone: '01000000000', password: 'e2e-admin-pass' },
}

const realWebServers = [
  {
    command: `rm -rf "${realDir}" && mkdir -p "${realDir}/media" && "${backendPython}" manage.py migrate --noinput && "${backendPython}" manage.py seed_abo_samra && "${backendPython}" manage.py runserver 127.0.0.1:${realApiPort} --noreload`,
    cwd: backendDir,
    url: `http://localhost:${realApiPort}/api/v1/settings/`,
    reuseExistingServer: false,
    timeout: 180_000,
    env: {
      DJANGO_SETTINGS_MODULE: 'config.settings.development',
      SECRET_KEY: 'e2e-real-secret-key-0123456789-abcdefghijklmnop',
      DEBUG: 'True',
      ALLOWED_HOSTS: 'localhost,127.0.0.1',
      DATABASE_URL: `sqlite:///${join(realDir, 'db.sqlite3')}`,
      MEDIA_PATH: join(realDir, 'media'),
      CORS_ALLOWED_ORIGINS: `http://localhost:${realFrontPort},http://127.0.0.1:${realFrontPort}`,
      ADMIN_PHONE: REAL.admin.phone,
      ADMIN_PASSWORD: REAL.admin.password,
      RATELIMIT_ANON: '100000/minute',
      RATELIMIT_USER: '100000/minute',
      RATELIMIT_AUTH: '100000/minute',
      RATELIMIT_QUOTE: '100000/minute',
      RATELIMIT_ORDERS: '100000/minute',
      RATELIMIT_SENSITIVE: '100000/minute',
    },
  },
  {
    command: `npx vite --port ${realFrontPort} --strictPort`,
    url: `http://localhost:${realFrontPort}`,
    reuseExistingServer: false,
    timeout: 120_000,
    env: { VITE_USE_MOCKS: 'false', VITE_API_BASE_URL: `http://localhost:${realApiPort}/api/v1` },
  },
]
export default defineConfig({
  testDir: './e2e',
  outputDir: './test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: { baseURL, locale: 'ar-EG', trace: 'on-first-retry' },
  projects: realMode
    ? [
        {
          name: 'real-api',
          testDir: './e2e/real',
          fullyParallel: false,
          workers: 1,
          timeout: 90_000,
          use: {
            ...devices['Pixel 7'],
            viewport: { width: 390, height: 844 },
            locale: 'ar-EG',
            baseURL: REAL.front,
          },
        },
      ]
    : [
        {
          name: 'mobile-390-rtl',
          testIgnore: [/pwa\.spec\.ts/, /e2e\/real\//],
          use: { ...devices['Pixel 7'], viewport: { width: 390, height: 844 }, locale: 'ar-EG' },
        },
        {
          // Production build served by `vite preview` (real service worker, no MSW);
          // /api routes are mocked inside the tests with Playwright routes.
          name: 'pwa-prod-build',
          testMatch: /pwa\.spec\.ts/,
          use: {
            ...devices['Pixel 7'],
            viewport: { width: 390, height: 844 },
            locale: 'ar-EG',
            baseURL: `http://localhost:${pwaPort}`,
            serviceWorkers: 'allow',
          },
        },
      ],
  webServer: realMode
    ? realWebServers
    : process.env.E2E_BASE_URL
      ? undefined
      : [
          {
            command: `npx vite --port ${port} --strictPort`,
            url: baseURL,
            reuseExistingServer: !process.env.CI,
            env: {
              VITE_USE_MOCKS: String(useMocks),
              VITE_API_BASE_URL: 'http://localhost:8000/api/v1',
            },
            timeout: 120_000,
          },
          {
            command: `npx vite build --outDir dist/e2e-pwa && npx vite preview --outDir dist/e2e-pwa --port ${pwaPort} --strictPort`,
            url: `http://localhost:${pwaPort}`,
            reuseExistingServer: !process.env.CI,
            env: { VITE_USE_MOCKS: 'false', VITE_API_BASE_URL: 'http://localhost:8000/api/v1' },
            timeout: 180_000,
          },
        ],
})

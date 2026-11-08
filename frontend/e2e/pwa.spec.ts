import AxeBuilder from '@axe-core/playwright'
import { test, expect } from '@playwright/test'
import type { BrowserContext, Page } from '@playwright/test'
import { mockApi } from './fixtures/pwa-api'

// QA-04. Runs against the PRODUCTION build served by `vite preview` (real Workbox service worker).
// The API is mocked with Playwright routes (MSW is not part of the production build).

async function swReady(page: Page) {
  await page.evaluate(async () => {
    const reg = await navigator.serviceWorker.ready
    if (!reg.active) throw new Error('no active service worker')
  })
}

/** Load once so the SW installs, reload so it controls the page and caches the catalog. */
async function warmUp(page: Page, context: BrowserContext, path: string) {
  await mockApi(context)
  await page.goto(path)
  await swReady(page)
  await page.reload()
  await page.waitForLoadState('networkidle')
  await expect
    .poll(() => page.evaluate(() => !!navigator.serviceWorker.controller), { timeout: 10_000 })
    .toBe(true)
}

test.describe('QA-04 PWA', () => {
  test('manifest is valid and linked (CP-P1)', async ({ page, request }) => {
    await page.goto('/')
    const href = await page.locator('link[rel="manifest"]').getAttribute('href')
    expect(href).toBeTruthy()
    const res = await request.get(new URL(href!, page.url()).toString())
    expect(res.ok()).toBe(true)
    const m = await res.json()
    expect(m).toMatchObject({
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
    })
    const sizes = m.icons.map(
      (i: { sizes: string; purpose?: string }) => `${i.sizes}${i.purpose ? ':' + i.purpose : ''}`,
    )
    expect(sizes).toEqual(expect.arrayContaining(['192x192', '512x512', '512x512:maskable']))
    for (const icon of m.icons) {
      const r = await request.get(new URL(icon.src, page.url()).toString())
      expect(r.ok(), icon.src).toBe(true)
      expect(r.headers()['content-type']).toContain('image/png')
    }
    expect(m.shortcuts.map((s: { name: string; url: string }) => [s.name, s.url])).toEqual([
      ['العروض', '/offers'],
      ['السلة', '/cart'],
    ])
    await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('content', '#F7A04B')
    await expect(page.locator('link[rel="apple-touch-icon"]')).toHaveCount(1)
    await expect(page.locator('meta[name="apple-mobile-web-app-status-bar-style"]')).toHaveCount(1)
  })

  test('service worker registers and controls the page', async ({ page, context }) => {
    await warmUp(page, context, '/')
    const scope = await page.evaluate(async () => (await navigator.serviceWorker.ready).scope)
    expect(scope).toMatch(/\/$/)
  })

  test('offline: cached catalog browsing works and the banner shows (CP-P2)', async ({
    page,
    context,
  }) => {
    await warmUp(page, context, '/categories/spices')
    await expect(page.getByText('كمون مطحون').first()).toBeVisible()
    await expect(page.getByText('انت أوفلاين دلوقتي — هتقدر تتفرج بس الطلب محتاج نت')).toHaveCount(
      0,
    )

    const cacheNames = await page.evaluate(() => caches.keys())
    expect(cacheNames.some((n) => n.includes('catalog-api'))).toBe(true)

    await context.setOffline(true)
    await page.reload()
    await expect(page.getByText('انت أوفلاين دلوقتي — هتقدر تتفرج بس الطلب محتاج نت')).toBeVisible()
    await expect(page.getByText('كمون مطحون').first()).toBeVisible()
    await expect(page.getByText('كركم').first()).toBeVisible()

    await context.setOffline(false)
    await expect(page.getByText('انت أوفلاين دلوقتي — هتقدر تتفرج بس الطلب محتاج نت')).toHaveCount(
      0,
    )
  })

  test('offline: banner appears live and checkout is disabled (CP-P2)', async ({
    page,
    context,
  }) => {
    await warmUp(page, context, '/categories/spices')
    await page
      .locator('article', { hasText: 'كمون مطحون' })
      .getByRole('button', { name: 'أضف للسلة' })
      .click()
    await page.getByRole('link', { name: /عرض السلة/ }).click()
    const checkout = page.getByRole('button', { name: 'كمّل الطلب' })
    await expect(checkout).toBeEnabled()

    await context.setOffline(true)
    await expect(page.getByText('انت أوفلاين دلوقتي — هتقدر تتفرج بس الطلب محتاج نت')).toBeVisible()
    await expect(checkout).toBeDisabled()
    await expect(page.getByText('الطلب محتاج نت، ارجع اتصل وكمّل')).toBeVisible()

    await context.setOffline(false)
    await expect(checkout).toBeEnabled()
  })

  test('offline: cart survives a reload (CP-F7)', async ({ page, context }) => {
    await warmUp(page, context, '/categories/spices')
    await page
      .locator('article', { hasText: 'كركم' })
      .getByRole('button', { name: 'أضف للسلة' })
      .click()
    await context.setOffline(true)
    await page.goto('/cart')
    await expect(page.getByText('كركم').first()).toBeVisible()
    await expect(page.getByText('1 منتج')).toBeVisible()
  })

  test('keyboard focus ring is visible on interactive elements', async ({ page, context }) => {
    await mockApi(context)
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    const seen: { tag: string; ring: boolean }[] = []
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press('Tab')
      const info = await page.evaluate(() => {
        const el = document.activeElement as HTMLElement
        if (!el || el === document.body) return null
        const s = getComputedStyle(el)
        const outline = s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0
        const shadow = s.boxShadow !== 'none' && s.boxShadow !== ''
        return {
          tag: `${el.tagName}:${el.getAttribute('aria-label') ?? el.textContent?.trim().slice(0, 20)}`,
          ring: outline || shadow,
        }
      })
      if (info) seen.push(info)
    }
    expect(seen.length).toBeGreaterThan(3)
    const missing = seen.filter((s) => !s.ring)
    expect(missing, `focused elements without a visible ring: ${JSON.stringify(missing)}`).toEqual(
      [],
    )
  })

  const SCREENS = ['/', '/categories/spices', '/products/cumin', '/offers', '/cart', '/account']
  for (const path of SCREENS) {
    test(`a11y: icon buttons/links/inputs have accessible names - ${path}`, async ({
      page,
      context,
    }) => {
      await mockApi(context)
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      const results = await new AxeBuilder({ page })
        .withRules([
          'button-name',
          'link-name',
          'label',
          'input-button-name',
          'aria-valid-attr',
          'aria-allowed-attr',
          'aria-required-attr',
          'aria-roles',
          'image-alt',
          'select-name',
          'html-has-lang',
          'document-title',
        ])
        .analyze()
      expect(
        results.violations.map(
          (v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(' | ')}`,
        ),
      ).toEqual([])
    })

    test(`a11y: WCAG A/AA scan - ${path}`, async ({ page, context }) => {
      await mockApi(context)
      await page.goto(path)
      await page.waitForLoadState('networkidle')
      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze()
      expect(
        results.violations.map(
          (v) => `${v.id} (${v.impact}): ${v.nodes.map((n) => n.target.join(' ')).join(' | ')}`,
        ),
      ).toEqual([])
    })
  }
})

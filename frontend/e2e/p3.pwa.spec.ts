import { readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { test, expect } from '@playwright/test'
import type { BrowserContext, Page } from '@playwright/test'
import { mockApi } from './fixtures/pwa-api'

// FIX-08 / CP-P3: install prompt, iOS sheet, update toast. Production build (project pwa-prod-build).

const IOS_UA =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'
const CARD_TEXT = 'نزّل تطبيق أبو سمرة على موبايلك'

async function fireInstallEvent(page: Page) {
  await page.evaluate(() => {
    const e = new Event('beforeinstallprompt', { cancelable: true }) as Event & {
      prompt: () => Promise<void>
      userChoice: Promise<{ outcome: string }>
    }
    ;(window as unknown as { __prompted: number }).__prompted = 0
    e.prompt = async () => {
      ;(window as unknown as { __prompted: number }).__prompted++
    }
    e.userChoice = Promise.resolve({ outcome: 'accepted' })
    window.dispatchEvent(e)
  })
}

test.describe('FIX-08 CP-P3 install prompt', () => {
  test('first visit shows no prompt, second visit shows it; تثبيت triggers the browser prompt', async ({
    page,
    context,
  }) => {
    await mockApi(context)
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await fireInstallEvent(page)
    await expect(page.getByText(CARD_TEXT)).toHaveCount(0)
    expect(await page.evaluate(() => localStorage.getItem('abosamra.visits'))).toBe('1')

    // New browser session = second visit.
    await page.evaluate(() => sessionStorage.removeItem('abosamra.visit-counted'))
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    expect(await page.evaluate(() => localStorage.getItem('abosamra.visits'))).toBe('2')
    await fireInstallEvent(page)
    await expect(page.getByText(CARD_TEXT)).toBeVisible()
    await expect(page.getByRole('button', { name: 'تثبيت', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'مش دلوقتي' })).toBeVisible()

    await page.getByRole('button', { name: 'تثبيت', exact: true }).click()
    await expect
      .poll(() => page.evaluate(() => (window as never as { __prompted: number }).__prompted))
      .toBe(1)
    await expect(page.getByText(CARD_TEXT)).toHaveCount(0)
  })

  test('مش دلوقتي hides the card and it stays hidden after reload', async ({ page, context }) => {
    await mockApi(context)
    await page.addInitScript(() => {
      if (!localStorage.getItem('abosamra.visits')) localStorage.setItem('abosamra.visits', '1')
    })
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await fireInstallEvent(page)
    await expect(page.getByText(CARD_TEXT)).toBeVisible()
    await page.getByRole('button', { name: 'مش دلوقتي' }).click()
    await expect(page.getByText(CARD_TEXT)).toHaveCount(0)
    await page.evaluate(() => sessionStorage.removeItem('abosamra.visit-counted'))
    await page.reload()
    await page.waitForLoadState('networkidle')
    await fireInstallEvent(page)
    await expect(page.getByText(CARD_TEXT)).toHaveCount(0)
  })
})

test.describe('FIX-08 CP-P3 iOS instructions', () => {
  test.use({ userAgent: IOS_UA })
  test('Safari iPhone: card on 2nd visit without beforeinstallprompt, تثبيت opens the instructions sheet', async ({
    page,
    context,
  }) => {
    await mockApi(context)
    await page.addInitScript(() => {
      if (!localStorage.getItem('abosamra.visits')) localStorage.setItem('abosamra.visits', '1')
    })
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText(CARD_TEXT)).toBeVisible()
    await page.getByRole('button', { name: 'تثبيت', exact: true }).click()
    await expect(page.getByText('تثبيت على الآيفون')).toBeVisible()
    await expect(page.getByText('اختار "إضافة إلى الشاشة الرئيسية"')).toBeVisible()
    await expect(page.getByText('اضغط "إضافة"')).toBeVisible()
    await page.getByRole('button', { name: 'تمام' }).click()
    await expect(page.getByText('تثبيت على الآيفون')).toHaveCount(0)
    await expect(page.getByText(CARD_TEXT)).toHaveCount(0)
  })
})

async function swControlled(page: Page, context: BrowserContext) {
  await mockApi(context)
  await page.goto('/')
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready
  })
  await page.reload()
  await page.waitForLoadState('networkidle')
  await expect
    .poll(() => page.evaluate(() => !!navigator.serviceWorker.controller), { timeout: 10_000 })
    .toBe(true)
}

test.describe('FIX-08 CP-P3 update toast', () => {
  test('a changed service worker script shows "فيه نسخة جديدة" with تحديث (real SW update path)', async ({
    page,
    context,
  }) => {
    await swControlled(page, context)
    await expect(page.getByText('فيه نسخة جديدة')).toHaveCount(0)

    // Make the served sw.js byte-different (Playwright cannot intercept the SW script fetch):
    // the browser installs it and, with registerType "prompt", leaves it waiting ->
    // workbox-window "waiting" -> onNeedRefresh -> toast. The file is restored afterwards.
    const swPath = resolve(process.cwd(), 'dist/e2e-pwa/sw.js')
    const original = readFileSync(swPath, 'utf8')
    try {
      writeFileSync(swPath, `${original}\n// update-${Date.now()}`)
      await runUpdate(page)
    } finally {
      writeFileSync(swPath, original)
    }
  })
})

async function runUpdate(page: Page) {
  await page.evaluate(async () => {
    const reg = await navigator.serviceWorker.getRegistration()
    await reg?.update()
  })
  await expect(page.getByText('فيه نسخة جديدة')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByRole('button', { name: 'تحديث' })).toBeVisible()
}

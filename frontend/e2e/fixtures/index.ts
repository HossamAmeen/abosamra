import { test as base, expect, type Page } from '@playwright/test'

export const ADMIN = { phone: '01099999999', password: 'admin123' }
export const CUSTOMER = { phone: '01012345678', name: 'محمد أحمد' }

/** Client-side navigation keeps the in-memory MSW db and the Pinia state alive. */
export async function spaGo(page: Page, path: string) {
  await page.evaluate((p) => {
    window.history.pushState({}, '', p)
    window.dispatchEvent(new PopStateEvent('popstate'))
  }, path)
}

export async function adminLogin(page: Page) {
  await page.goto('/admin/login')
  await page.getByLabel('رقم الموبايل').fill(ADMIN.phone)
  await page.getByLabel('كلمة السر').fill(ADMIN.password)
  await page.getByRole('button', { name: 'دخول' }).click()
  await expect(page).toHaveURL(/\/admin\/?$/)
}

export const test = base.extend<{ gotoHome: () => Promise<void> }>({
  gotoHome: async ({ page }, use) => {
    await use(async () => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
    })
  },
})

export { expect }

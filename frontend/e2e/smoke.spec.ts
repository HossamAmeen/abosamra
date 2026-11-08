import { test, expect } from './fixtures'

test('home loads in RTL', async ({ page, gotoHome }) => {
  await gotoHome()
  await expect(page.locator('html')).toHaveAttribute('dir', 'rtl')
  await expect(page.locator('#app')).not.toBeEmpty()
})

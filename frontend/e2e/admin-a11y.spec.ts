import AxeBuilder from '@axe-core/playwright'
import { test, expect, adminLogin, spaGo } from './fixtures'

// FIX-08: axe WCAG 2 A/AA on every /admin/* screen (MSW mocks, logged in as staff).
const SCREENS: [string, string][] = [
  ['dashboard', '/admin'],
  ['orders', '/admin/orders'],
  ['products', '/admin/products'],
  ['product form (new)', '/admin/products/new'],
  ['product form (edit)', '/admin/products/1'],
  ['offers', '/admin/offers'],
  ['customers', '/admin/customers'],
]

test.describe('FIX-08 admin a11y', () => {
  test('a11y: admin login', async ({ page }) => {
    await page.goto('/admin/login')
    await page.waitForLoadState('networkidle')
    const r = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()
    expect(
      r.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(' | ')}`),
    ).toEqual([])
  })

  for (const [name, path] of SCREENS) {
    test(`a11y: admin ${name}`, async ({ page }) => {
      await adminLogin(page)
      if (path !== '/admin') await spaGo(page, path)
      await expect(page).toHaveURL(new RegExp(`${path}$`))
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      const r = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze()
      expect(
        r.violations.map(
          (v) => `${v.id} (${v.impact}): ${v.nodes.map((n) => n.target.join(' ')).join(' | ')}`,
        ),
      ).toEqual([])
    })
  }
})

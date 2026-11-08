import fs from 'node:fs'
import path from 'node:path'
import sharp from 'sharp'
import { test, expect, adminLogin, spaGo, type Page } from '../fixtures'

// QA-07: 390x844 (DPR 2, full page => 780px wide like the design PNGs) screenshot of each of the
// 13 screens, plus a side-by-side image (app | design) in visual/compare/.
const root = path.resolve(import.meta.dirname)
const DESIGN_DIR = path.resolve(root, '../../../desin')
const SCREENS_DIR = path.join(root, 'screens')
const COMPARE_DIR = path.join(root, 'compare')

test.use({ deviceScaleFactor: 2 })
test.describe.configure({ mode: 'parallel' })

async function settle(page: Page) {
  await page.evaluate(() => document.fonts.ready)
  await page.waitForLoadState('networkidle')
  await page.addStyleTag({
    content:
      '*{animation:none!important;transition:none!important;caret-color:transparent!important}',
  })
  await page.waitForTimeout(400)
}

async function capture(page: Page, id: string, design: string) {
  await settle(page)
  // 1) the official 390x844 viewport screenshot
  await page.screenshot({ path: path.join(SCREENS_DIR, `${id}.png`) })
  // 2) the app lays out inside a viewport-height shell with fixed bars, so for the side-by-side
  //    the viewport is stretched to the design's height (the PNGs are full-length mockups).
  const dsg = sharp(path.join(DESIGN_DIR, `${design}.png`))
  const dm = await dsg.metadata()
  await page.setViewportSize({ width: 390, height: Math.round(dm.height! / 2) })
  await page.waitForTimeout(500)
  const tall = path.join(SCREENS_DIR, `${id}-tall.png`)
  await page.screenshot({ path: tall })
  const am = await sharp(tall).metadata()
  const h = Math.max(am.height!, dm.height!)
  const gap = 40
  await sharp({
    create: { width: am.width! + dm.width! + gap, height: h, channels: 3, background: '#888888' },
  })
    .composite([
      { input: tall, left: 0, top: 0 },
      { input: await dsg.toBuffer(), left: am.width! + gap, top: 0 },
    ])
    .png()
    .toFile(path.join(COMPARE_DIR, `${id}.png`))
  expect(fs.existsSync(tall)).toBe(true)
}

async function fillCart(page: Page) {
  await page.goto('/')
  await page.waitForLoadState('networkidle')
  await page.getByRole('button', { name: 'أضف فلفل أسود حب للسلة' }).first().click()
  await spaGo(page, '/categories/spices')
  const cumin = page.locator('article', { hasText: 'كمون مطحون' })
  await cumin.getByRole('button', { name: 'أضف للسلة' }).click()
  await cumin.getByRole('button', { name: 'زوّد كمون مطحون' }).click()
  await spaGo(page, '/categories/honey')
  await page
    .locator('article', { hasText: 'عسل نحل طبيعي' })
    .getByRole('button', { name: 'أضف للسلة' })
    .click()
  await page.waitForTimeout(3000) // let the add-to-cart toasts expire
}

test('01 home', async ({ page }) => {
  await page.goto('/')
  await capture(page, '01-home', 'الرئيسية')
})

test('02 category', async ({ page }) => {
  await fillCart(page)
  await spaGo(page, '/categories/spices')
  await capture(page, '02-category', 'الأقسام والمنتجات')
})

test('03 product', async ({ page }) => {
  await page.goto('/products/' + encodeURIComponent('كمون-مطحون'))
  await capture(page, '03-product', 'تفاصيل المنتج')
})

test('04 offers', async ({ page }) => {
  await page.goto('/offers')
  await capture(page, '04-offers', 'العروض')
})

test('05 cart', async ({ page }) => {
  await fillCart(page)
  await spaGo(page, '/cart')
  await page.getByText('الدفع كاش عند الاستلام').waitFor()
  await capture(page, '05-cart', 'السلة')
})

test('06 account (sign-up)', async ({ page }) => {
  await page.goto('/account')
  await capture(page, '06-account', 'إنشاء حساب')
})

test('07 order success', async ({ page }) => {
  await fillCart(page)
  await spaGo(page, '/cart')
  await page.getByLabel('عنوان التوصيل').fill('المعادي، شارع 9، عمارة 12 الدور 3')
  await page.getByRole('button', { name: 'كمّل الطلب' }).click()
  await page.getByLabel('الاسم').fill('محمد أحمد')
  await page.getByLabel('رقم الموبايل').fill('01098765432')
  await page.getByRole('button', { name: /إنشاء الحساب/ }).click()
  await page.getByText(/رقم الطلب #/).waitFor()
  await capture(page, '07-order-success', 'تم الطلب')
})

test('08 admin dashboard', async ({ page }) => {
  await adminLogin(page)
  await capture(page, '08-admin-dashboard', 'لوحة التحكم – الرئيسية')
})

test('09 admin orders', async ({ page }) => {
  await adminLogin(page)
  await spaGo(page, '/admin/orders')
  await page.getByTestId('order-1001').waitFor()
  await capture(page, '09-admin-orders', 'الطلبات')
})

test('10 admin products', async ({ page }) => {
  await adminLogin(page)
  await spaGo(page, '/admin/products')
  await page.getByRole('heading', { name: 'كمون مطحون' }).waitFor()
  await capture(page, '10-admin-products', 'المنتجات')
})

test('11 admin product form', async ({ page }) => {
  await adminLogin(page)
  await spaGo(page, '/admin/products/new')
  await page.getByLabel('اسم المنتج').waitFor()
  await capture(page, '11-admin-product-new', 'إضافة منتج')
})

test('12 admin offers', async ({ page }) => {
  await adminLogin(page)
  await spaGo(page, '/admin/offers')
  await page.getByText('العروض الحالية').waitFor()
  await capture(page, '12-admin-offers', 'إدارة العروض')
})

test('13 admin customers', async ({ page }) => {
  await adminLogin(page)
  await spaGo(page, '/admin/customers')
  await page.getByText('محمد أحمد').waitFor()
  await capture(page, '13-admin-customers', 'الزبائن')
})

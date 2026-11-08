import { test, expect, type APIRequestContext, type Page } from '@playwright/test'
import { REAL } from '../../playwright.config'

// QA-06: core journeys against the REAL Django backend (fresh sqlite + seed_abo_samra).
// Serial: later tests build on the data created by earlier ones (order 1001, stock levels).

test.describe.configure({ mode: 'serial' })

const CUSTOMER_PHONE = '01055512345'
const ADDRESS = 'المعادي، شارع 9، عمارة 12 الدور 3'

async function adminToken(request: APIRequestContext) {
  const r = await request.post(`${REAL.api}/auth/admin/login/`, { data: REAL.admin })
  expect(r.status()).toBe(200)
  return (await r.json()).access as string
}

async function adminGet(request: APIRequestContext, path: string) {
  const token = await adminToken(request)
  const r = await request.get(`${REAL.api}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  expect(r.status(), path).toBe(200)
  return r.json()
}

async function stockOf(request: APIRequestContext, name: string) {
  const list = await adminGet(request, `/admin/products/?q=${encodeURIComponent(name)}`)
  const product = list.results.find((p: { name: string }) => p.name === name)
  return Number(product.stock_qty)
}

async function setStock(request: APIRequestContext, name: string, qty: number) {
  const token = await adminToken(request)
  const list = await adminGet(request, `/admin/products/?q=${encodeURIComponent(name)}`)
  const product = list.results.find((p: { name: string }) => p.name === name)
  const r = await request.patch(`${REAL.api}/admin/products/${product.id}/`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { stock_qty: qty, stock_unit: 'كيلو' },
  })
  expect(r.status()).toBe(200)
}

async function adminLogin(page: Page) {
  await page.goto('/admin/login')
  await page.getByLabel('رقم الموبايل').fill(REAL.admin.phone)
  await page.getByLabel('كلمة السر').fill(REAL.admin.password)
  await page.getByRole('button', { name: 'دخول' }).click()
  await expect(page).toHaveURL(/\/admin\/?$/)
}

test.describe('QA-06 real API', () => {
  test('storefront: reference cart (435/32/30/433/97), sign up, COD order #1001, stock decremented', async ({
    page,
    request,
  }) => {
    await setStock(request, 'كمون مطحون', 10)
    expect(await stockOf(request, 'كمون مطحون')).toBe(10)

    await page.goto('/')
    await page.getByRole('button', { name: 'أضف فلفل أسود حب للسلة' }).first().click()
    await expect(page.getByText('اتضاف للسلة').first()).toBeVisible()
    await page.getByRole('link', { name: 'عرض الكل' }).first().click()
    await page.getByRole('button', { name: 'بهارات', exact: true }).click()
    const cumin = page.locator('article', { hasText: 'كمون مطحون' })
    await cumin.getByRole('button', { name: 'أضف للسلة' }).click()
    await cumin.getByRole('button', { name: 'زوّد كمون مطحون' }).click()
    await expect(cumin.locator('[aria-live="polite"]')).toHaveText('2')
    await page.getByRole('button', { name: 'عسل وزيوت' }).click()
    await page.getByRole('link', { name: 'عسل نحل طبيعي' }).first().click()
    await expect(page.getByRole('heading', { name: 'عسل نحل طبيعي' })).toBeVisible()
    await page.getByRole('button', { name: 'أضف للسلة' }).first().click()
    await page.getByRole('link', { name: 'روح للسلة' }).click()

    const summary = page.locator('section', { hasText: 'الدفع كاش عند الاستلام' })
    await expect(summary.locator('div', { hasText: /^الإجمالي/ })).toContainText('433')
    for (const n of ['435', '32', '30']) await expect(summary).toContainText(n)
    await expect(page.getByText(/فاضلك .*97.* وتاخد توصيل مجاني/)).toBeVisible()

    await page.getByLabel('عنوان التوصيل').fill(ADDRESS)
    await page.getByRole('button', { name: 'كمّل الطلب' }).click()
    await expect(page).toHaveURL(/\/account\?next=checkout/)
    await page.getByLabel('الاسم').fill('عميل حقيقي')
    await page.getByLabel('رقم الموبايل').fill(CUSTOMER_PHONE)
    await page.getByRole('button', { name: 'إنشاء الحساب وتأكيد الطلب' }).click()

    await expect(page).toHaveURL(/\/orders\/\d+\/success/, { timeout: 20_000 })
    await expect(page.getByText('رقم الطلب #1001')).toBeVisible()
    await expect(page.getByText('كاش عند الاستلام')).toBeVisible()

    // API: stock 10 - 2 x 0.25 = 9.5, order totals match the quote.
    expect(await stockOf(request, 'كمون مطحون')).toBe(9.5)
    const orders = await adminGet(request, '/admin/orders/')
    expect(orders.results[0]).toMatchObject({ number: 1001, status: 'new', total: 433 })
  })

  test('customer sees the order under "طلباتي" after reload', async ({ page }) => {
    await page.goto('/account')
    await page.getByRole('button', { name: /عندك حساب؟/ }).click()
    await page.getByLabel('رقم الموبايل').fill(CUSTOMER_PHONE)
    await page.getByRole('button', { name: 'دخول', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'عميل حقيقي' })).toBeVisible()
    await expect(page.getByText('#1001').first()).toBeVisible()
  })

  test('admin: advance 1001 through the chain, cancel a second order and see stock restored', async ({
    page,
    request,
  }) => {
    // Second order created through the API so the UI test can cancel it.
    const login = await request.post(`${REAL.api}/auth/login/`, { data: { phone: CUSTOMER_PHONE } })
    const { access } = await login.json()
    const products = await (
      await request.get(`${REAL.api}/products/?q=${encodeURIComponent('كمون')}`)
    ).json()
    const variantId = products.results[0].variants[0].id
    const created = await request.post(`${REAL.api}/orders/`, {
      headers: { Authorization: `Bearer ${access}` },
      data: { items: [{ variant_id: variantId, qty: 4 }], address: ADDRESS },
    })
    expect(created.status()).toBe(201)
    expect((await created.json()).number).toBe(1002)
    expect(await stockOf(request, 'كمون مطحون')).toBe(8.5)

    await adminLogin(page)
    await page.goto('/admin/orders')
    const card = page.getByTestId('order-1001')
    await expect(card).toBeVisible()
    await card.getByRole('button', { name: 'ابدأ التجهيز' }).click()
    await page.getByRole('button', { name: /^بيتجهز \(/ }).click()
    await page.getByTestId('order-1001').getByRole('button', { name: 'خرج للتوصيل' }).click()
    await page.getByRole('button', { name: /^في الطريق \(/ }).click()
    await page.getByTestId('order-1001').getByRole('button', { name: 'اتسلم' }).click()
    await page.getByRole('button', { name: /^اتسلم \(/ }).click()
    await expect(page.getByTestId('order-1001')).toBeVisible()
    expect((await adminGet(request, '/admin/orders/?status=delivered')).count).toBe(1)

    // Cancel 1002 from the sheet.
    await page.getByRole('button', { name: /^جديد \(/ }).click()
    await page.getByTestId('order-1002').getByRole('button').first().click()
    await page.getByRole('button', { name: 'إلغاء الطلب' }).click()
    await page.getByRole('button', { name: 'أيوه، إلغي' }).click()
    await expect(page.getByTestId('order-1002')).toHaveCount(0)
    expect((await adminGet(request, '/admin/orders/?status=cancelled')).count).toBe(1)
    expect(await stockOf(request, 'كمون مطحون')).toBe(9.5)
  })

  test('admin: create a product with 3 weights and see it on the storefront', async ({
    page,
    request,
  }) => {
    await adminLogin(page)
    await page.goto('/admin/products/new')
    await page.getByLabel('اسم المنتج').fill('شطة حارة')
    await page.getByLabel('القسم').selectOption({ label: 'بهارات' })
    const labels = page.getByLabel('الوزن', { exact: true })
    const prices = page.getByLabel('السعر', { exact: true })
    const data = [
      ['ربع كيلو', '40'],
      ['نص كيلو', '75'],
      ['كيلو', '140'],
    ]
    for (let i = 0; i < 3; i++) {
      await labels.nth(i).fill(data[i][0])
      await prices.nth(i).fill(data[i][1])
    }
    await page.getByLabel('وصف قصير').fill('شطة حارة مطحونة')
    await page.getByRole('button', { name: 'حفظ المنتج' }).click()
    await expect(page).toHaveURL(/\/admin\/products\/?$/)

    const list = await adminGet(request, '/admin/products/?q=%D8%B4%D8%B7%D8%A9')
    const created = list.results.find((p: { name: string }) => p.name === 'شطة حارة')
    expect(
      created.variants.map((v: { label: string; price: number }) => [v.label, v.price]),
    ).toEqual([
      ['ربع كيلو', 40],
      ['نص كيلو', 75],
      ['كيلو', 140],
    ])
    expect(typeof created.category).toBe('object')

    await page.goto(`/products/${created.slug}`)
    await expect(page.getByRole('button', { name: /ربع كيلو/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /نص كيلو/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /^كيلو/ })).toBeVisible()
  })
})

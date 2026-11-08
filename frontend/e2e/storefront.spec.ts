/* eslint-disable @typescript-eslint/no-explicit-any -- XHR monkey-patch used to simulate a server-side race */
import { test, expect } from './fixtures'

const ARABIC_PHONE = '٠١٠٩٨٧٦٥٤٣٢' // 01098765432

test.describe('QA-02 storefront', () => {
  test('browse a category and filter via chips', async ({ page, gotoHome }) => {
    await gotoHome()
    await page.getByRole('link', { name: 'بهارات', exact: true }).first().click()
    await expect(page).toHaveURL(/\/categories\/spices/)
    await expect(page.getByText('5 منتج')).toBeVisible()
    await page.getByRole('button', { name: 'عسل وزيوت' }).click()
    await expect(page).toHaveURL(/\/categories\/honey/)
    await expect(page.getByText('2 منتج')).toBeVisible()
    await expect(page.getByRole('link', { name: 'زيت زيتون' }).first()).toBeVisible()
  })

  test('add via card, stepper and product weight -> cart totals match reference quote -> sign up -> order', async ({
    page,
    gotoHome,
  }) => {
    await gotoHome()

    // 1) round "+" on a home card (pepper 95)
    await page.getByRole('button', { name: 'أضف فلفل أسود حب للسلة' }).first().click()
    await expect(page.getByText('اتضاف للسلة').first()).toBeVisible()

    // 2) stepper on the category page (cumin x2 = 120)
    await page.getByRole('link', { name: 'عرض الكل' }).first().click()
    await page.getByRole('button', { name: 'بهارات', exact: true }).click()
    const cumin = page.locator('article', { hasText: 'كمون مطحون' })
    await cumin.getByRole('button', { name: 'أضف للسلة' }).click()
    await cumin.getByRole('button', { name: 'زوّد كمون مطحون' }).click()
    await expect(cumin.locator('[aria-live="polite"]')).toHaveText('2')
    await expect(page.getByText('عرض السلة · 3 منتج')).toBeVisible()

    // 3) product page with weight selection (honey 220)
    await page.getByRole('button', { name: 'عسل وزيوت' }).click()
    await page.getByRole('link', { name: 'عسل نحل طبيعي' }).first().click()
    await expect(page.getByRole('heading', { name: 'عسل نحل طبيعي' })).toBeVisible()
    await page.getByRole('button', { name: 'أضف للسلة' }).click()
    await expect(page.getByText('اتضاف للسلة').first()).toBeVisible()
    await page.getByRole('link', { name: 'روح للسلة' }).click()

    // cart totals == reference quote 435 / 32 / 30 / 433 / 97
    await expect(page.getByRole('heading', { name: 'السلة' })).toBeVisible()
    const summary = page.locator('section', { hasText: 'الدفع كاش عند الاستلام' })
    await expect(summary).toContainText('435')
    await expect(summary).toContainText('32')
    await expect(summary).toContainText('30')
    await expect(summary).toContainText('433')
    await expect(page.getByText(/فاضلك .*97.* وتاخد توصيل مجاني/)).toBeVisible()
    await expect(summary.locator('span', { hasText: /^المجموع$/ }).locator('..')).toContainText(
      '435',
    )
    await expect(summary.locator('div', { hasText: /^خصم/ })).toContainText('32')
    await expect(summary.locator('div', { hasText: /^الإجمالي/ })).toContainText('433')

    // guest checkout -> account
    await page.getByLabel('عنوان التوصيل').fill('المعادي، شارع 9، عمارة 12 الدور 3')
    await page.getByRole('button', { name: 'كمّل الطلب' }).click()
    await expect(page).toHaveURL(/\/account\?next=checkout/)

    // sign-up with Arabic-Indic digits; button disabled until valid
    const submit = page.getByRole('button', { name: 'إنشاء الحساب وتأكيد الطلب' })
    await expect(submit).toBeDisabled()
    await page.getByLabel('الاسم').fill('عميل اختبار')
    await page.getByLabel('رقم الموبايل').fill(ARABIC_PHONE)
    await expect(submit).toBeEnabled()
    await submit.click()

    // resumes checkout and lands on the success screen with #number
    await expect(page).toHaveURL(/\/orders\/\d+\/success/, { timeout: 15_000 })
    await expect(page.getByText(/رقم الطلب #\d+/)).toBeVisible()
    await expect(page.getByText('رقم الطلب #1004')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'طلبك وصل لأبو سمرة!' })).toBeVisible()
    await expect(page.getByText('كاش عند الاستلام')).toBeVisible()
    await expect(page.getByText('433')).toBeVisible()
  })

  test('product page: choose weight changes total and quantity', async ({ page }) => {
    await page.goto('/products/' + encodeURIComponent('كمون-مطحون'))
    await expect(page.getByRole('heading', { name: 'كمون مطحون' })).toBeVisible()
    const half = page.getByRole('button', { name: /نص كيلو/ })
    await half.click()
    await expect(half).toHaveAttribute('aria-pressed', 'true')
    await page.getByRole('button', { name: 'زوّد كمون مطحون' }).click()
    await expect(page.getByText('الإجمالي').locator('..')).toContainText('230')
    await page.getByLabel('ملاحظة للمحل (اختياري)').fill('مطحون ناعم')
    await page.getByRole('button', { name: 'أضف للسلة' }).click()
    await page.getByRole('link', { name: 'روح للسلة' }).click()
    await expect(page.getByText('نص كيلو · ')).toBeVisible()
  })

  test('phone validation cases', async ({ page }) => {
    await page.goto('/account')
    const submit = page.getByRole('button', { name: /إنشاء الحساب/ })
    await page.getByLabel('الاسم').fill('محمد')
    const phone = page.getByLabel('رقم الموبايل')
    for (const bad of ['0101234567', '02012345678', '01312345678', 'abc']) {
      await phone.fill(bad)
      await expect(submit, `rejects ${bad}`).toBeDisabled()
    }
    await expect(page.getByText('اكتب اسمك ورقم موبايل صحيح (11 رقم يبدأ بـ 01)')).toBeVisible()
    for (const good of ['01012345678', '٠١٠١٢٣٤٥٦٧٨', '01512345678'.replace('015', '011')]) {
      await phone.fill(good)
      await expect(submit, `accepts ${good}`).toBeEnabled()
    }
  })

  test('register with existing phone switches to login mode (phone_exists)', async ({ page }) => {
    await page.goto('/account')
    await page.getByLabel('الاسم').fill('محمد تاني')
    await page.getByLabel('رقم الموبايل').fill('01012345678')
    await page.getByRole('button', { name: /إنشاء الحساب/ }).click()
    await expect(page.getByText('الرقم ده عنده حساب، ادخل بيه')).toBeVisible()
    await expect(page.getByLabel('رقم الموبايل')).toHaveValue('01012345678')
    await expect(page.getByLabel('الاسم')).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'دخول', exact: true })).toBeEnabled()
    await expect(page.getByRole('button', { name: 'مش عندك حساب؟ اعمل حساب جديد' })).toBeVisible()
  })

  test('login unknown phone -> not_found switches to register; existing phone logs in', async ({
    page,
  }) => {
    await page.goto('/account')
    await page.getByRole('button', { name: /عندك حساب؟/ }).click()
    await page.getByLabel('رقم الموبايل').fill('01155555555')
    await page.getByRole('button', { name: 'دخول', exact: true }).click()
    await expect(page.getByText('مفيش حساب بالرقم ده')).toBeVisible()
    await expect(page.getByLabel('الاسم')).toBeVisible()
    await expect(page.getByLabel('رقم الموبايل')).toHaveValue('01155555555')

    await page.getByRole('button', { name: /عندك حساب؟/ }).click()
    await page.getByLabel('رقم الموبايل').fill('٠١٠١٢٣٤٥٦٧٨')
    await page.getByRole('button', { name: 'دخول', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'محمد أحمد' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'طلباتي' })).toBeVisible()
    await expect(page.getByText(/طلب #\d+/).first()).toBeVisible()
    await page.getByRole('button', { name: 'تسجيل خروج' }).click()
    await expect(page.getByRole('heading', { name: 'اعمل حسابك في ثانية' })).toBeVisible()
  })

  test('409 cart_changed refreshes the cart and shows the notice', async ({ page, gotoHome }) => {
    await gotoHome()
    // log in first (client-side state), then break the cart server-side via the MSW db
    await page.getByRole('link', { name: 'حسابي' }).click()
    await page.getByRole('button', { name: /عندك حساب؟/ }).click()
    await page.getByLabel('رقم الموبايل').fill('01012345678')
    await page.getByRole('button', { name: 'دخول', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'محمد أحمد' })).toBeVisible()

    await page.getByRole('link', { name: 'الرئيسية' }).click()
    await page.getByRole('link', { name: 'عرض الكل' }).first().click()
    const turmeric = page.locator('article', { hasText: 'كركم' }).first()
    await turmeric.getByRole('button', { name: 'أضف للسلة' }).click()
    await page.getByRole('link', { name: /عرض السلة/ }).click()
    await page.getByLabel('عنوان التوصيل').fill('المعادي، شارع 9، عمارة 12 الدور 3')

    // Make the next order POST fail with 409 at the SW level by closing the product in the mock db.
    // The mock exposes no db handle, so we mark the product unavailable through the admin API
    // using the in-page axios-less fetch with an admin token obtained via the mock login.
    const ok = await page.evaluate(async () => {
      const base = 'http://localhost:8000/api/v1'
      const login = await fetch(`${base}/auth/admin/login/`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ phone: '01099999999', password: 'admin123' }),
      }).then((r) => r.json())
      const h = { 'content-type': 'application/json', authorization: `Bearer ${login.access}` }
      const list = await fetch(`${base}/admin/products/?q=كركم`, { headers: h }).then((r) =>
        r.json(),
      )
      const p = list.results.find((x: { name: string }) => x.name === 'كركم')
      const r = await fetch(`${base}/admin/products/${p.id}/`, {
        method: 'PATCH',
        headers: h,
        body: JSON.stringify({ is_available: false }),
      })
      return r.ok
    })
    expect(ok).toBe(true)

    await page.getByRole('button', { name: 'كمّل الطلب' }).click()
    await expect(page.getByText(/فيه حاجات في السلة اتغيرت|خلصان حالياً/).first()).toBeVisible()
    await expect(page).toHaveURL(/\/cart/)
    await expect(page.getByRole('button', { name: 'كمّل الطلب' })).toBeDisabled()
  })

  test('POST /orders/ answering 409 cart_changed applies the returned quote', async ({
    page,
    gotoHome,
  }) => {
    // Race simulation: the product is closed in the mock db after the pre-submit re-quote but
    // before the order POST, so the server (not the client pre-check) answers 409.
    await page.addInitScript(() => {
      const open = XMLHttpRequest.prototype.open
      const send = XMLHttpRequest.prototype.send
      XMLHttpRequest.prototype.open = function (m: string, u: string | URL, ...r: unknown[]) {
        ;(this as any).__m = m
        ;(this as any).__u = String(u)
        return (open as any).call(this, m, u, ...r)
      }
      XMLHttpRequest.prototype.send = function (body?: Document | XMLHttpRequestBodyInit | null) {
        const self = this as any
        if (self.__m === 'POST' && /\/orders\/$/.test(self.__u) && !(window as any).__raced) {
          ;(window as any).__raced = true
          const base = 'http://localhost:8000/api/v1'
          const run = async () => {
            const login = await fetch(`${base}/auth/admin/login/`, {
              method: 'POST',
              headers: { 'content-type': 'application/json' },
              body: JSON.stringify({ phone: '01099999999', password: 'admin123' }),
            }).then((r) => r.json())
            const h = {
              'content-type': 'application/json',
              authorization: `Bearer ${login.access}`,
            }
            const list = await fetch(`${base}/admin/products/?q=كركم`, { headers: h }).then((r) =>
              r.json(),
            )
            const p = list.results.find((x: { name: string }) => x.name === 'كركم')
            await fetch(`${base}/admin/products/${p.id}/`, {
              method: 'PATCH',
              headers: h,
              body: JSON.stringify({ is_available: false }),
            })
          }
          run().finally(() => (send as any).call(this, body))
          return
        }
        return (send as any).call(this, body)
      }
    })
    await gotoHome()
    await page.getByRole('link', { name: 'حسابي' }).click()
    await page.getByRole('button', { name: /عندك حساب؟/ }).click()
    await page.getByLabel('رقم الموبايل').fill('01012345678')
    await page.getByRole('button', { name: 'دخول', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'محمد أحمد' })).toBeVisible()
    await page.getByRole('link', { name: 'الرئيسية' }).click()
    await page.getByRole('link', { name: 'عرض الكل' }).first().click()
    await page
      .locator('article', { hasText: 'كركم' })
      .first()
      .getByRole('button', { name: 'أضف للسلة' })
      .click()
    await page.getByRole('link', { name: /عرض السلة/ }).click()
    await page.getByLabel('عنوان التوصيل').fill('المعادي، شارع 9، عمارة 12 الدور 3')
    await page.getByRole('button', { name: 'كمّل الطلب' }).click()
    await expect(page.getByText('فيه حاجات في السلة اتغيرت، راجع السلة وكمّل الطلب')).toBeVisible()
    await expect(page).toHaveURL(/\/cart/)
    await expect(page.getByRole('button', { name: 'كمّل الطلب' })).toBeDisabled()
  })
})

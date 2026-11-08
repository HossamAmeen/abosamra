import { test, expect, adminLogin, spaGo, ADMIN } from './fixtures'

test.describe('QA-03 admin', () => {
  test('guard: anonymous /admin redirects to login', async ({ page }) => {
    await page.goto('/admin/orders')
    await expect(page).toHaveURL(/\/admin\/login/)
    await expect(page.getByRole('button', { name: 'دخول' })).toBeVisible()
  })

  test('guard: logged-in customer cannot reach admin', async ({ page, gotoHome }) => {
    await gotoHome()
    await page.getByRole('link', { name: 'حسابي' }).click()
    await page.getByRole('button', { name: /عندك حساب؟/ }).click()
    await page.getByLabel('رقم الموبايل').fill('01012345678')
    await page.getByRole('button', { name: 'دخول', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'محمد أحمد' })).toBeVisible()
    await spaGo(page, '/admin')
    await expect(page).toHaveURL(/\/admin\/login/)
  })

  test('admin login: wrong password shows error, right password opens dashboard', async ({
    page,
  }) => {
    await page.goto('/admin/login')
    await page.getByLabel('رقم الموبايل').fill(ADMIN.phone)
    await page.getByLabel('كلمة السر').fill('غلط-غلط')
    await page.getByRole('button', { name: 'دخول' }).click()
    await expect(page.getByText('الرقم أو الباسورد غلط')).toBeVisible()
    await page.getByLabel('كلمة السر').fill(ADMIN.password)
    await page.getByRole('button', { name: 'دخول' }).click()
    await expect(page).toHaveURL(/\/admin\/?$/)
    await expect(page.getByRole('heading', { name: 'أهلاً يا أبو سمرة' })).toBeVisible()
    for (const l of ['طلبات النهاردة', 'مبيعات النهاردة', 'مستنية تأكيد'])
      await expect(page.getByText(l).first()).toBeVisible()
  })

  test('advance an order through the full chain and cancel another', async ({ page }) => {
    await adminLogin(page)
    await spaGo(page, '/admin/orders')
    const card = page.getByTestId('order-1001')
    await expect(card).toBeVisible()
    await expect(card).toContainText('جديد')
    await card.getByRole('button', { name: 'ابدأ التجهيز' }).click()
    await expect(page.getByTestId('order-1001')).toHaveCount(0)
    // chips: switch to preparing
    await page.getByRole('button', { name: /^بيتجهز \(/ }).click()
    const prep = page.getByTestId('order-1001')
    await expect(prep).toBeVisible()
    await prep.getByRole('button', { name: 'خرج للتوصيل' }).click()
    await page.getByRole('button', { name: /^في الطريق \(/ }).click()
    const out = page.getByTestId('order-1001')
    await expect(out).toBeVisible()
    await out.getByRole('button', { name: 'اتسلم' }).click()
    await page.getByRole('button', { name: /^اتسلم \(/ }).click()
    const done = page.getByTestId('order-1001')
    await expect(done).toBeVisible()
    await expect(done.getByRole('button', { name: 'اتسلم', exact: true })).toHaveCount(0)
    await expect(done.getByRole('button', { name: 'خرج للتوصيل', exact: true })).toHaveCount(0)

    // cancel order 1002 (preparing) from its detail sheet
    await page.getByRole('button', { name: /^بيتجهز \(/ }).click()
    await page.getByTestId('order-1002').getByRole('button').first().click()
    await page.getByRole('button', { name: 'إلغاء الطلب' }).click()
    await expect(page.getByText('متأكد إنك عايز تلغي الطلب ده؟ المخزون هيرجع.')).toBeVisible()
    await page.getByRole('button', { name: 'أيوه، إلغي' }).click()
    await expect(page.getByTestId('order-1002')).toHaveCount(0)
    await page.getByRole('button', { name: 'حالات تانية' }).click()
    await page.getByRole('button', { name: /^اتلغى \(/ }).click()
    await expect(page.getByTestId('order-1002')).toBeVisible()
  })

  test('dashboard: confirm a new order', async ({ page }) => {
    await adminLogin(page)
    await expect(page.getByText('طلبات جديدة محتاجة تأكيد')).toBeVisible()
    await page.getByRole('button', { name: 'تأكيد الطلب' }).first().click()
    await expect(page.getByText('اتأكد').first()).toBeVisible()
  })

  test('toggle product availability is reflected in the storefront', async ({ page }) => {
    await adminLogin(page)
    await spaGo(page, '/admin/products')
    const sw = page.getByRole('switch', { name: 'كركم: متوفر' })
    await expect(sw).toHaveAttribute('aria-checked', 'true')
    await sw.click()
    await expect(sw).toHaveAttribute('aria-checked', 'false')
    await spaGo(page, '/categories/spices')
    const card = page.locator('article', { hasText: 'كركم' }).first()
    await expect(card.getByText('خلصان')).toBeVisible()
    await expect(card.getByRole('button', { name: 'أضف للسلة' })).toBeDisabled()
  })

  test('create a product with 3 weights and see it in the list', async ({ page }) => {
    await adminLogin(page)
    await spaGo(page, '/admin/products/new')
    await expect(page.getByRole('heading', { name: 'إضافة منتج' })).toBeVisible()
    await page.getByLabel('اسم المنتج').fill('شطة حارة')
    await page.getByLabel('القسم').selectOption({ label: 'بهارات' })
    const labels = page.getByLabel('الوزن', { exact: true })
    const prices = page.getByLabel('السعر', { exact: true })
    await expect(labels).toHaveCount(3)
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
    await page.getByLabel('ابحث باسم المنتج').fill('شطة')
    await expect(page.getByRole('heading', { name: 'شطة حارة' })).toBeVisible()
    // storefront shows all 3 weights
    await spaGo(page, '/products/' + encodeURIComponent('شطة-حارة'))
    await expect(page.getByRole('button', { name: /ربع كيلو/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /نص كيلو/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /^كيلو/ })).toBeVisible()
  })

  test('product form validation: missing name and category', async ({ page }) => {
    await adminLogin(page)
    await spaGo(page, '/admin/products/new')
    await page.getByRole('button', { name: 'حفظ المنتج' }).click()
    await expect(page.getByText('اكتب اسم المنتج')).toBeVisible()
    await expect(page).toHaveURL(/products\/new/)
  })

  test('create a percentage offer, then pause it', async ({ page }) => {
    await adminLogin(page)
    await spaGo(page, '/admin/offers')
    await page.getByLabel('اسم العرض').fill('خصم اختبار')
    await page.getByLabel('نسبة الخصم %').fill('10')
    await page.getByLabel('على', { exact: true }).selectOption('all')
    await page.getByRole('button', { name: 'نشر العرض' }).click()
    const sw = page.getByRole('switch', { name: 'خصم اختبار: شغّال' })
    await expect(sw).toBeVisible()
    await expect(sw).toHaveAttribute('aria-checked', 'true')
    await sw.click()
    await expect(sw).toHaveAttribute('aria-checked', 'false')
    // paused offers are not active on the storefront
    await spaGo(page, '/offers')
    await expect(page.getByText('خصم اختبار')).toHaveCount(0)
  })

  test('offer form validation and bundle/free-delivery segments', async ({ page }) => {
    await adminLogin(page)
    await spaGo(page, '/admin/offers')
    await page.getByRole('radio', { name: 'باكدج' }).click()
    await expect(page.getByLabel('اسم العرض')).toHaveAttribute('placeholder', 'مثلاً: باكدج رمضان')
    await expect(page.getByLabel('سعر الباكدج (ج.م)')).toBeVisible()
    await page.getByRole('radio', { name: 'توصيل مجاني' }).click()
    await expect(page.getByLabel('أقل قيمة للطلب (ج.م)')).toBeVisible()
    await page.getByLabel('اسم العرض').fill('توصيل مجاني تجريبي')
    await page.getByLabel('أقل قيمة للطلب (ج.م)').fill('300')
    await page.getByRole('button', { name: 'نشر العرض' }).click()
    await expect(page.getByText('توصيل مجاني تجريبي').first()).toBeVisible()
  })

  test('customer search by name and phone', async ({ page }) => {
    await adminLogin(page)
    await spaGo(page, '/admin/customers')
    const search = page.getByLabel('ابحث بالاسم أو رقم الموبايل')
    await expect(page.getByText('محمد أحمد')).toBeVisible()
    await expect(page.getByText('سارة علي')).toBeVisible()
    await search.fill('سارة')
    await expect(page.getByText('سارة علي')).toBeVisible()
    await expect(page.getByText('محمد أحمد')).toHaveCount(0)
    await search.fill('01012345678')
    await expect(page.getByText('محمد أحمد')).toBeVisible()
    await expect(page.getByText('سارة علي')).toHaveCount(0)
    await search.fill('مش موجود خالص')
    await expect(page.getByText('محمد أحمد')).toHaveCount(0)
  })

  test('offer form shows no validation error before the user submits (QA-F01)', async ({
    page,
  }) => {
    await adminLogin(page)
    await spaGo(page, '/admin/offers')
    await expect(page.getByLabel('اسم العرض')).toBeVisible()
    await expect(page.getByText('اختار القسم')).toHaveCount(0)
    await expect(page.getByRole('alert')).toHaveCount(0)
  })
})

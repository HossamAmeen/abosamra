import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { http, HttpResponse } from 'msw'
import type { Component } from 'vue'
import { router as appRouter, routes } from '@/router'
import { db, MOCK_ADMIN } from '@/mocks/db'
import { server } from '@/mocks/server'
import { url } from '@/mocks/handlers/util'
import { useAuthStore } from '@/stores/auth'
import { toProductFormData } from '@/api/admin/products'
import Login from './Login.vue'
import Dashboard from './Dashboard.vue'
import Orders from './Orders.vue'
import Products from './Products.vue'
import ProductForm from './ProductForm.vue'
import Offers from './Offers.vue'
import Customers from './Customers.vue'
import Staff from './Staff.vue'
import Profile from './Profile.vue'

async function mountAt(component: Component, path: string, asAdmin = true) {
  const pinia = createPinia()
  setActivePinia(pinia)
  if (asAdmin) await useAuthStore().adminLogin(MOCK_ADMIN.phone, MOCK_ADMIN.password)
  const router = createRouter({ history: createMemoryHistory(), routes })
  router.push(path)
  await router.isReady()
  const wrapper = mount(component, {
    global: { plugins: [pinia, router] },
    attachTo: document.body,
  })
  await flushPromises()
  return { wrapper, router }
}

/** Lets async validation (vee-validate + zod) and mocked requests settle. */
async function settle() {
  await new Promise((r) => setTimeout(r, 60))
  await flushPromises()
}

const byText = (w: VueWrapper, selector: string, text: string) =>
  w.findAll(selector).find((el) => el.text().includes(text))

beforeEach(() => {
  document.body.innerHTML = ''
})

beforeEach(() => {
  document.body.innerHTML = ''
})

describe('admin guard + login', () => {
  it('redirects a non-staff visitor to /admin/login', async () => {
    setActivePinia(createPinia())
    await appRouter.push('/admin/orders')
    expect(appRouter.currentRoute.value.name).toBe('admin-login')
    expect(appRouter.currentRoute.value.query.next).toBe('/admin/orders')
  })

  it('shows the server error for a wrong password, then signs in', async () => {
    const { wrapper, router } = await mountAt(Login, '/admin/login?next=/admin/orders', false)
    const [phone, password] = wrapper.findAll('input')
    await phone.setValue('01099999999')
    await password.setValue('wrong')
    await wrapper.get('form').trigger('submit')
    await settle()
    expect(wrapper.find('[role=alert]').exists()).toBe(true)
    expect(useAuthStore().isStaff).toBe(false)
    await password.setValue(MOCK_ADMIN.password)
    await wrapper.get('form').trigger('submit')
    await settle()
    expect(useAuthStore().isStaff).toBe(true)
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/admin/orders'))
  })

  it('validates phone and password before calling the API', async () => {
    const { wrapper } = await mountAt(Login, '/admin/login', false)
    await wrapper.get('form').trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('اكتب رقم موبايل صحيح')
    expect(wrapper.text()).toContain('اكتب كلمة السر')
  })

  it('toggles password visibility with the eye button', async () => {
    const { wrapper } = await mountAt(Login, '/admin/login', false)
    const input = wrapper.get('input[autocomplete="current-password"]')
    expect(input.attributes('type')).toBe('password')
    const eye = wrapper.get('button[aria-label="اظهر كلمة السر"]')
    await eye.trigger('click')
    expect(input.attributes('type')).toBe('text')
    expect(eye.attributes('aria-pressed')).toBe('true')
    await wrapper.get('button[aria-label="اخفي كلمة السر"]').trigger('click')
    expect(input.attributes('type')).toBe('password')
  })
})

describe('Staff', () => {
  it('lists admins and adds a new one who can then log in', async () => {
    const { wrapper } = await mountAt(Staff, '/admin/staff')
    expect(wrapper.text()).toContain('أبو سمرة')
    expect(wrapper.text()).toContain('(إنت)')
    await byText(wrapper, 'button', 'إضافة أدمن')!.trigger('click')
    const form = () => wrapper.get('[role=dialog] form')
    await form().trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('كلمة السر لازم تكون 8 حروف على الأقل')
    const inputs = wrapper.findAll('[role=dialog] input')
    await inputs[0]!.setValue('محمود')
    await inputs[1]!.setValue(MOCK_ADMIN.phone)
    await inputs[2]!.setValue('strong-pass-1')
    await form().trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('الرقم ده مسجل قبل كده')
    await inputs[1]!.setValue('01220001111')
    await form().trigger('submit')
    await settle()
    expect(wrapper.find('[role=dialog]').exists()).toBe(false)
    expect(wrapper.text()).toContain('محمود')
    const added = db.users.find((u) => u.phone === '01220001111')!
    expect(added.is_staff).toBe(true)
    setActivePinia(createPinia())
    await useAuthStore().adminLogin('01220001111', 'strong-pass-1')
    expect(useAuthStore().isStaff).toBe(true)
  })
})

describe('Dashboard', () => {
  it('renders stats, low stock, and confirms a new order', async () => {
    const { wrapper } = await mountAt(Dashboard, '/admin')
    const text = wrapper.text()
    for (const t of ['أهلاً يا أبو سمرة', 'طلبات النهاردة', 'مبيعات النهاردة', 'مستنية تأكيد'])
      expect(text).toContain(t)
    expect(text).toContain('قرب يخلص من المخزن')
    const btn = byText(wrapper, 'button', 'تأكيد الطلب')!
    await btn.trigger('click')
    await settle()
    expect(db.orders.find((o) => o.number === 1001)!.status).toBe('preparing')
    expect(wrapper.text()).toContain('اتأكد')
  })
})

describe('Orders', () => {
  it('shows chips with counts and advances an order through the chain', async () => {
    const { wrapper, router } = await mountAt(Orders, '/admin/orders')
    expect(wrapper.text()).toContain('جديد (1)')
    await byText(wrapper, 'button', 'ابدأ التجهيز')!.trigger('click')
    await settle()
    expect(db.orders.find((o) => o.number === 1001)!.status).toBe('preparing')
    expect(wrapper.text()).toContain('مفيش طلبات هنا')
    await router.replace({ query: { status: 'preparing' } })
    await settle()
    expect(wrapper.text()).toContain('خرج للتوصيل')
    await byText(wrapper, 'button', 'خرج للتوصيل')!.trigger('click')
    await settle()
    expect(db.orders.filter((o) => o.status === 'out_for_delivery')).toHaveLength(1)
  })

  it('cancels from the detail sheet only after confirming', async () => {
    const { wrapper } = await mountAt(Orders, '/admin/orders')
    await wrapper.get('[data-testid="order-1001"] button').trigger('click')
    await settle()
    await byText(wrapper, 'button', 'إلغاء الطلب')!.trigger('click')
    expect(db.orders.find((o) => o.number === 1001)!.status).toBe('new')
    await byText(wrapper, 'button', 'أيوه، إلغي')!.trigger('click')
    await settle()
    expect(db.orders.find((o) => o.number === 1001)!.status).toBe('cancelled')
  })
})

describe('Products', () => {
  it('toggles availability optimistically and rolls back on error', async () => {
    const { wrapper } = await mountAt(Products, '/admin/products')
    const sw = wrapper.get('[role=switch]')
    expect(sw.attributes('aria-checked')).toBe('true')
    await sw.trigger('click')
    expect(sw.attributes('aria-checked')).toBe('false') // before the response
    await settle()
    expect(db.products[0].isAvailable).toBe(false)

    server.use(
      http.patch(url('/admin/products/:id/'), () => HttpResponse.json({}, { status: 500 })),
    )
    const sw2 = wrapper.findAll('[role=switch]')[1]
    await sw2.trigger('click')
    await settle()
    expect(sw2.attributes('aria-checked')).toBe('true')
  })

  it('serialises variants as a JSON string field in the multipart body', () => {
    const fd = toProductFormData({
      name: 'x',
      category: 1,
      variants: [{ label: 'ربع', price: 10 }],
      stock_qty: null,
    })
    expect(fd.get('variants')).toBe(JSON.stringify([{ label: 'ربع', price: 10 }]))
    expect(fd.get('stock_qty')).toBe('')
  })
})

describe('ProductForm', () => {
  it('requires name, category and a priced variant', async () => {
    const { wrapper } = await mountAt(ProductForm, '/admin/products/new')
    await wrapper.get('form').trigger('submit')
    await settle()
    const text = wrapper.text()
    expect(text).toContain('اكتب اسم المنتج')
    expect(text).toContain('اختار القسم')
    expect(text).toContain('اكتب الوزن')
    expect(text).toContain('اكتب سعر صحيح')
  })

  it('creates a product with 3 weights; first is default; last row can be removed', async () => {
    const { wrapper, router } = await mountAt(ProductForm, '/admin/products/new')
    await wrapper.get('input[placeholder="مثلاً: كمون مطحون"]').setValue('شطة مطحونة')
    await wrapper.get('select#category').setValue('1')
    const add = byText(wrapper, 'button', 'إضافة وزن')!
    await add.trigger('click') // starts with 3 rows (as in the design) -> 4
    await wrapper.get('button[aria-label="حذف الوزن 4"]').trigger('click') // back to 3
    const labels = wrapper.findAll('input[aria-label="الوزن"]')
    const prices = wrapper.findAll('input[aria-label="السعر"]')
    expect(labels).toHaveLength(3)
    for (const [i, l] of ['ربع كيلو', 'نص كيلو', 'كيلو'].entries()) {
      await labels[i].setValue(l)
      await prices[i].setValue(String((i + 1) * 20))
    }
    await wrapper.get('form').trigger('submit')
    await settle()
    const created = db.products.find((p) => p.name === 'شطة مطحونة')!
    expect(created.variants.map((v) => [v.label, v.price, v.isDefault])).toEqual([
      ['ربع كيلو', 20, true],
      ['نص كيلو', 40, false],
      ['كيلو', 60, false],
    ])
    expect(router.currentRoute.value.path).toBe('/admin/products')
  })

  it('maps server field errors onto the inputs', async () => {
    server.use(
      http.post(url('/admin/products/'), () =>
        HttpResponse.json(
          { name: ['الاسم ده موجود'], variants: [{ price: ['اكتب سعر صحيح من السيرفر'] }] },
          { status: 400 },
        ),
      ),
    )
    const { wrapper } = await mountAt(ProductForm, '/admin/products/new')
    await wrapper.get('input[placeholder="مثلاً: كمون مطحون"]').setValue('كمون')
    await wrapper.get('select#category').setValue('1')
    await wrapper.get('button[aria-label="حذف الوزن 3"]').trigger('click')
    await wrapper.get('button[aria-label="حذف الوزن 2"]').trigger('click')
    await wrapper.get('input[aria-label="الوزن"]').setValue('كيلو')
    await wrapper.get('input[aria-label="السعر"]').setValue('50')
    await wrapper.get('form').trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('الاسم ده موجود')
    expect(wrapper.text()).toContain('اكتب سعر صحيح من السيرفر')
  })

  it('loads an existing product for editing and deletes it after confirming', async () => {
    const id = db.products[3].id
    const { wrapper, router } = await mountAt(ProductForm, `/admin/products/${id}`)
    expect(
      (wrapper.get('input[placeholder="مثلاً: كمون مطحون"]').element as HTMLInputElement).value,
    ).toBe(db.products[3].name)
    await byText(wrapper, 'button', 'حذف المنتج')!.trigger('click')
    await byText(wrapper, 'button', 'أيوه، احذف')!.trigger('click')
    await settle()
    expect(db.products.find((p) => p.id === id && !p.isArchived)).toBeUndefined()
    expect(router.currentRoute.value.path).toBe('/admin/products')
  })
})

describe('Offers', () => {
  it('lists offers and pauses one with the switch', async () => {
    const { wrapper } = await mountAt(Offers, '/admin/offers')
    expect(wrapper.text()).toContain('العروض الحالية')
    const sw = wrapper.get('[role=switch]')
    await sw.trigger('click')
    await settle()
    expect(db.offers[0].is_active).toBe(false)
    expect(sw.attributes('aria-checked')).toBe('false')
  })

  it('validates then publishes a free-delivery offer', async () => {
    const { wrapper } = await mountAt(Offers, '/admin/offers')
    await byText(wrapper, '[role=radio]', 'توصيل مجاني')!.trigger('click')
    await wrapper.get('form').trigger('submit')
    await settle()
    expect(wrapper.text()).toContain('اكتب اسم العرض')
    expect(wrapper.text()).toContain('اكتب أقل قيمة للطلب')
    await wrapper
      .get('input[placeholder="مثلاً: توصيل مجاني للطلبات الكبيرة"]')
      .setValue('توصيل مجاني 500')
    await wrapper.get('input[type=number]').setValue('500')
    await wrapper.get('form').trigger('submit')
    await settle()
    const created = db.offers.find((o) => o.name === 'توصيل مجاني 500')!
    expect(created).toMatchObject({ type: 'free_delivery', min_order: 500, is_active: true })
  })

  it('creates a percentage offer on a category', async () => {
    const { wrapper } = await mountAt(Offers, '/admin/offers')
    await wrapper.get('input[placeholder="مثلاً: خصم البهارات"]').setValue('خصم العسل')
    await wrapper.get('input[type=number]').setValue('15')
    await wrapper.get('select#target').setValue('cat:honey')
    await wrapper.get('form').trigger('submit')
    await settle()
    const created = db.offers.find((o) => o.name === 'خصم العسل')!
    expect(created.value).toBe(15)
    expect(created.target).toMatchObject({ kind: 'category', slug: 'honey' })
  })
})

describe('Customers', () => {
  it('lists customers with stats and filters by search', async () => {
    const { wrapper } = await mountAt(Customers, '/admin/customers')
    expect(wrapper.text()).toContain('محمد أحمد')
    expect(wrapper.text()).toContain('مرتبين حسب آخر طلب')
    expect(wrapper.text()).toContain('طلب ·')
    expect(wrapper.find('a[href="tel:01012345678"]').exists()).toBe(true)
    await wrapper.get('input[type=search]').setValue('سارة')
    await new Promise((r) => setTimeout(r, 400))
    await settle()
    expect(wrapper.text()).not.toContain('محمد أحمد')
    expect(wrapper.text()).toContain('بدون إيميل')
  })
})

describe('Profile', () => {
  it('renames the admin, changes the password and logs out', async () => {
    const { wrapper, router } = await mountAt(Profile, '/admin/profile')
    expect(wrapper.text()).toContain('أبو سمرة')
    expect(wrapper.text()).toContain('إصدار التطبيق 1.2.3')

    await wrapper.get('input[aria-label="الاسم"]').setValue('الحاج أبو سمرة')
    await byText(wrapper, 'button', 'حفظ الاسم')!.trigger('click')
    await settle()
    expect(useAuthStore().user?.name).toBe('الحاج أبو سمرة')

    const [current, next] = wrapper.findAll('input[type="password"]')
    await current!.setValue('wrong-pass')
    await next!.setValue('brand-new-pass')
    await byText(wrapper, 'button', 'تغيير كلمة السر')!.trigger('click')
    await settle()
    expect(wrapper.text()).toContain('كلمة السر الحالية غلط')
    await current!.setValue(MOCK_ADMIN.password)
    await byText(wrapper, 'button', 'تغيير كلمة السر')!.trigger('click')
    await settle()
    expect(db.users.find((u) => u.phone === MOCK_ADMIN.phone)!.password).toBe('brand-new-pass')

    await byText(wrapper, 'button', 'تسجيل خروج')!.trigger('click')
    await settle()
    expect(useAuthStore().isLoggedIn).toBe(false)
    expect(router.currentRoute.value.name).toBe('admin-login')
  })
})

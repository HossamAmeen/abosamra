import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import type { Component } from 'vue'
import { routes } from '@/router'
import Home from './Home.vue'
import Category from './Category.vue'
import Product from './Product.vue'
import Cart from './Cart.vue'
import Account from './Account.vue'
import Offers from './Offers.vue'
import { lineKey, useCartStore } from '@/stores/cart'
import { useAuthStore } from '@/stores/auth'
import { useCatalogStore } from '@/stores/catalog'
import { getProducts } from '@/api/catalog'
import { db } from '@/mocks/db'

async function mountAt(
  component: Component,
  path: string,
  existing?: ReturnType<typeof createPinia>,
) {
  const pinia = existing ?? createPinia()
  setActivePinia(pinia)
  const router = createRouter({ history: createMemoryHistory(), routes })
  router.push(path)
  await router.isReady()
  const wrapper = mount(component, {
    global: { plugins: [pinia, router] },
    attachTo: document.body,
  })
  await flushPromises()
  return { wrapper, router, pinia }
}

beforeEach(() => {
  document.body.innerHTML = ''
})

describe('Home', () => {
  it('renders verbatim copy, category tiles, offer banner and featured products', async () => {
    const { wrapper } = await mountAt(Home, '/')
    const text = wrapper.text()
    expect(text).toContain('أهلاً بيك.. عايز تطلب إيه النهاردة؟')
    expect(text).toContain('عرض الأسبوع')
    expect(text).toContain('الأقسام')
    expect(text).toContain('عروض النهاردة')
    expect(text).toContain('الأكثر طلباً')
    expect(wrapper.findAll('a[href^="/categories/"]').length).toBeGreaterThanOrEqual(6)
    const input = wrapper.get('input[type=search]')
    expect(input.attributes('placeholder')).toBe('دوّر على كمون، عسل، ينسون...')
  })

  it('search is debounced 300 ms then shows a results dropdown', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      const { wrapper } = await mountAt(Home, '/')
      await wrapper.get('input[type=search]').setValue('كمون')
      await vi.advanceTimersByTimeAsync(200)
      expect(wrapper.find('ul[aria-label="نتائج البحث"] a').exists()).toBe(false)
      await vi.advanceTimersByTimeAsync(150)
      await flushPromises()
      const links = wrapper.findAll('ul[aria-label="نتائج البحث"] a')
      expect(links.length).toBeGreaterThan(0)
      expect(links[0].text()).toContain('كمون')
    } finally {
      vi.useRealTimers()
    }
  })

  it('Enter goes to /categories/all?q=', async () => {
    const { wrapper, router } = await mountAt(Home, '/')
    await wrapper.get('input[type=search]').setValue('عسل')
    await wrapper.get('form[role=search]').trigger('submit')
    await flushPromises()
    expect(router.currentRoute.value.fullPath).toBe('/categories/all?q=%D8%B9%D8%B3%D9%84')
  })

  it('cart badge shows the cart count', async () => {
    const { wrapper, pinia } = await mountAt(Home, '/')
    setActivePinia(pinia)
    const { results } = await getProducts()
    useCartStore(pinia).addProduct(results[0], undefined, 3)
    await flushPromises()
    expect(wrapper.get('a[href="/cart"]').text()).toContain('3')
  })
})

describe('Category', () => {
  it('shows count caption, switches chips via URL, stepper replaces add button', async () => {
    const { wrapper, router } = await mountAt(Category, '/categories/spices')
    expect(wrapper.text()).toMatch(/\d+ منتج/)
    expect(wrapper.text()).toContain('أضف للسلة')
    const add = wrapper.findAll('button').find((b) => b.text() === 'أضف للسلة')!
    await add.trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-test=inc]').exists()).toBe(true)
    expect(wrapper.text()).toContain('عرض السلة · 1 منتج')
    await wrapper.find('[data-test=dec]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-test=inc]').exists()).toBe(false) // qty 0 removes
    const herbs = wrapper.findAll('button').find((b) => b.text() === 'أعشاب ومشروبات')!
    await herbs.trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/categories/herbs')
  })

  it('"all" shows كل المنتجات title', async () => {
    const { wrapper } = await mountAt(Category, '/categories/all')
    expect(wrapper.get('h1').text()).toBe('كل المنتجات')
  })
})

describe('Product', () => {
  it('weight picker, qty total, note and added box', async () => {
    const { wrapper, pinia } = await mountAt(Product, '/products/كمون-مطحون')
    expect(wrapper.get('h1').text()).toBe('كمون مطحون')
    const weights = wrapper.findAll('button[aria-pressed]')
    expect(weights).toHaveLength(3)
    expect(weights[0].attributes('aria-pressed')).toBe('true')
    await weights[1].trigger('click')
    expect(weights[1].attributes('aria-pressed')).toBe('true')
    await wrapper.get('[data-test=inc]').trigger('click')
    await wrapper.get('textarea').setValue('مطحون ناعم')
    const addBtn = wrapper.findAll('button').find((b) => b.text() === 'أضف للسلة')!
    await addBtn.trigger('click')
    expect(wrapper.text()).toContain('اتضاف للسلة')
    expect(wrapper.text()).toContain('روح للسلة')
    setActivePinia(pinia)
    const cart = useCartStore(pinia)
    expect(cart.lines[0]).toMatchObject({ qty: 2, note: 'مطحون ناعم' })
    expect(cart.lines[0].unitLabel).toBe('نص كيلو')
  })

  it('unavailable product disables the bar button', async () => {
    db.products[0].isAvailable = false
    const slug = db.products[0].slug
    const { wrapper } = await mountAt(Product, `/products/${slug}`)
    const btn = wrapper.findAll('button').find((b) => b.text() === 'المنتج خلصان حالياً')!
    expect(btn.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('خلصان')
  })
})

describe('Offers', () => {
  it('bundle shows the struck-through old price only when it is above the bundle price (FIX-02)', async () => {
    const bundle = db.offers.find((o) => o.type === 'bundle')!
    const saved = bundle.old_price
    try {
      bundle.old_price = (bundle.bundle_price ?? 0) - 115
      const low = await mountAt(Offers, '/offers')
      const before = low.wrapper.findAll('.line-through').length
      low.wrapper.unmount()
      bundle.old_price = (bundle.bundle_price ?? 0) + 45
      const high = await mountAt(Offers, '/offers')
      expect(high.wrapper.findAll('.line-through').length).toBe(before + 1)
    } finally {
      bundle.old_price = saved
    }
  })

  it('lists offer-only discounted products with an offer caption (FIX-04)', async () => {
    const { wrapper } = await mountAt(Offers, '/offers')
    expect(wrapper.text()).toContain('خصم 15%')
  })

  it('renders the three offer types and discounted grid', async () => {
    const { wrapper } = await mountAt(Offers, '/offers')
    const t = wrapper.text()
    expect(t).toContain('العروض')
    expect(t).toContain('الخصم بيتحسب لوحده في السلة')
    expect(t).toContain('باكدج')
    expect(t).toContain('أضف الباكدج')
    expect(t).toContain('توصيل مجاني')
    expect(t).toContain('على أي طلب فوق 500 ج.م')
    expect(t).toContain('منتجات عليها خصم')
    expect(t).toContain('تسوّق البهارات')
  })

  it('adding the bundle makes one cart line', async () => {
    const { wrapper, pinia } = await mountAt(Offers, '/offers')
    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'أضف الباكدج')!
      .trigger('click')
    setActivePinia(pinia)
    const cart = useCartStore(pinia)
    expect(cart.lines).toHaveLength(1)
    expect(cart.lines[0].bundleOfferId).toBeTruthy()
  })
})

async function fillReferenceCart(pinia: ReturnType<typeof createPinia>) {
  setActivePinia(pinia)
  const cart = useCartStore(pinia)
  const { results } = await getProducts()
  const by = (n: string) => results.find((p) => p.name === n)!
  cart.addProduct(by('كمون مطحون'), by('كمون مطحون').variants[0].id, 2)
  cart.addProduct(by('فلفل أسود حب'))
  cart.addProduct(by('عسل نحل طبيعي'))
  return cart
}

describe('Cart', () => {
  it('empty state', async () => {
    const { wrapper } = await mountAt(Cart, '/cart')
    expect(wrapper.text()).toContain('السلة فاضية')
    expect(wrapper.text()).toContain('ابدأ التسوق')
  })

  it('summary comes from the quote: reference case 435/32/30/433 + free-delivery progress 97', async () => {
    const pinia = createPinia()
    await fillReferenceCart(pinia)
    const { wrapper } = await mountAt(Cart, '/cart', pinia)
    const t = wrapper.text()
    expect(t).toContain('435 ج.م')
    expect(t).toContain('- 32 ج.م')
    expect(t).toContain('30 ج.م')
    expect(t).toContain('433 ج.م')
    expect(t).toContain('فاضلك 97 ج.م وتاخد توصيل مجاني')
    expect(t).toContain('الدفع كاش عند الاستلام')
    expect(wrapper.find('[role=progressbar]').attributes('aria-valuenow')).toBe('81')
  })

  it('guest checkout goes to /account?next=checkout', async () => {
    const { wrapper, pinia, router } = await mountAt(Cart, '/cart')
    await fillReferenceCart(pinia)
    await flushPromises()
    const btn = wrapper.findAll('button').find((b) => b.text() === 'كمّل الطلب')!
    await btn.trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.fullPath).toBe('/account?next=checkout')
  })

  it('logged in: address required, then order is placed and cart cleared', async () => {
    const { wrapper, pinia, router } = await mountAt(Cart, '/cart')
    await fillReferenceCart(pinia)
    const auth = useAuthStore(pinia)
    await auth.login('01012345678')
    await flushPromises()
    await wrapper.get('textarea').setValue('')
    const btn = () => wrapper.findAll('button').find((b) => b.text() === 'كمّل الطلب')!
    await btn().trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('اكتب العنوان بالتفصيل')
    await wrapper.get('textarea').setValue('المعادي، شارع 9، عمارة 12 الدور 3')
    await btn().trigger('click')
    await flushPromises()
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('order-success'))
    expect(useCartStore(pinia).isEmpty).toBe(true)
  })

  it('sends the per-line note on the order item and not in order notes (FIX-05)', async () => {
    const pinia = createPinia()
    const cart = await fillReferenceCart(pinia)
    cart.setNote(lineKey(cart.lines[0]), 'ناعم')
    const body = cart.orderBody()
    expect(body.items[0]).toMatchObject({ variant_id: cart.lines[0].variantId, note: 'ناعم' })
    expect(body.items[1]).not.toHaveProperty('note')
    expect(cart.requestBody().items[0]).not.toHaveProperty('note')
  })

  it('409 cart_changed keeps the cart and shows the review message', async () => {
    const { wrapper, pinia, router } = await mountAt(Cart, '/cart')
    const cart = await fillReferenceCart(pinia)
    await useAuthStore(pinia).login('01012345678')
    await flushPromises()
    await wrapper.get('textarea').setValue('المعادي، شارع 9، عمارة 12 الدور 3')
    cart.lines[0].variantId = 424242 // unknown variant -> server answers cart_changed
    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'كمّل الطلب')!
      .trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.name).not.toBe('order-success')
    expect(cart.isEmpty).toBe(false)
    expect(wrapper.text()).toMatch(/راجع السلة/)
  })
})

describe('Account', () => {
  it('disabled until valid, with hint; Arabic digits accepted', async () => {
    const { wrapper } = await mountAt(Account, '/account')
    const submit = () => wrapper.get('button[type=submit]')
    expect(submit().text()).toBe('إنشاء الحساب')
    expect(submit().attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('اكتب اسمك ورقم موبايل صحيح (11 رقم يبدأ بـ 01)')
    await wrapper.get('input[autocomplete=name]').setValue('محمد')
    await wrapper.get('input[type=tel]').setValue('٠١٠١٢٣٤٥٦٧٨')
    expect(submit().attributes('disabled')).toBeUndefined()
    await wrapper.get('input[type=tel]').setValue('0101234567')
    expect(submit().attributes('disabled')).toBeDefined()
    await wrapper.get('input[type=tel]').setValue('02012345678')
    expect(submit().attributes('disabled')).toBeDefined()
  })

  it('checkout label on the register button', async () => {
    const { wrapper } = await mountAt(Account, '/account?next=checkout')
    expect(wrapper.get('button[type=submit]').text()).toBe('إنشاء الحساب وتأكيد الطلب')
  })

  it('register with an existing phone switches to login with the message', async () => {
    const { wrapper } = await mountAt(Account, '/account')
    await wrapper.get('input[autocomplete=name]').setValue('محمد أحمد')
    await wrapper.get('input[type=tel]').setValue('01012345678')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('الرقم ده عنده حساب، ادخل بيه')
    expect(wrapper.get('button[type=submit]').text()).toBe('دخول')
    expect((wrapper.get('input[type=tel]').element as HTMLInputElement).value).toBe('01012345678')
    expect(wrapper.find('input[autocomplete=name]').exists()).toBe(false)
  })

  it('login with unknown phone switches to register with the message', async () => {
    const { wrapper } = await mountAt(Account, '/account')
    const footer = wrapper.findAll('button').find((b) => b.text().startsWith('عندك حساب؟'))!
    await footer.trigger('click')
    await wrapper.get('input[type=tel]').setValue('01099990000')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('مفيش حساب بالرقم ده')
    expect(wrapper.find('input[autocomplete=name]').exists()).toBe(true)
  })

  it('successful register with next=checkout resumes at the cart', async () => {
    const { wrapper, router } = await mountAt(Account, '/account?next=checkout')
    await wrapper.get('input[autocomplete=name]').setValue('منى سعيد')
    await wrapper.get('input[type=tel]').setValue('01277770000')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/cart')
    expect(router.currentRoute.value.query.resume).toBe('1')
  })

  it('logged-in view shows profile, my orders and logout', async () => {
    const { wrapper, pinia } = await mountAt(Account, '/account')
    setActivePinia(pinia)
    await useAuthStore(pinia).login('01012345678')
    await flushPromises()
    const t = wrapper.text()
    expect(t).toContain('محمد أحمد')
    expect(t).toContain('طلباتي')
    expect(t).toMatch(/طلب #\d+/)
    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'تسجيل خروج')!
      .trigger('click')
    await flushPromises()
    expect(useAuthStore(pinia).isLoggedIn).toBe(false)
    expect(wrapper.text()).toContain('اعمل حسابك في ثانية')
  })
})

describe('catalog store sanity', () => {
  it('loads', async () => {
    setActivePinia(createPinia())
    const c = useCatalogStore()
    await c.loadCategories()
    expect(c.categories).toHaveLength(6)
  })
})

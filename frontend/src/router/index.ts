import { createRouter, createWebHistory, START_LOCATION } from 'vue-router'
import StoreLayout from '@/layouts/StoreLayout.vue'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    hideNav?: boolean
    requiresAuth?: boolean
    requiresStaff?: boolean
    title?: string
  }
}

export const routes = [
  {
    path: '/',
    component: StoreLayout,
    children: [
      { path: '', name: 'home', component: () => import('@/views/store/Home.vue') },
      {
        path: 'categories/:slug?',
        name: 'category',
        component: () => import('@/views/store/Category.vue'),
      },
      {
        path: 'products/:slug',
        name: 'product',
        component: () => import('@/views/store/Product.vue'),
        meta: { hideNav: true },
      },
      { path: 'offers', name: 'offers', component: () => import('@/views/store/Offers.vue') },
      { path: 'cart', name: 'cart', component: () => import('@/views/store/Cart.vue') },
      { path: 'account', name: 'account', component: () => import('@/views/store/Account.vue') },
      {
        path: 'orders/:id/success',
        name: 'order-success',
        component: () => import('@/views/store/OrderSuccess.vue'),
        meta: { requiresAuth: true },
      },
    ],
  },
  {
    path: '/admin/login',
    name: 'admin-login',
    component: () => import('@/views/admin/Login.vue'),
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresStaff: true },
    children: [
      { path: '', name: 'admin-dashboard', component: () => import('@/views/admin/Dashboard.vue') },
      { path: 'orders', name: 'admin-orders', component: () => import('@/views/admin/Orders.vue') },
      {
        path: 'products',
        name: 'admin-products',
        component: () => import('@/views/admin/Products.vue'),
      },
      {
        path: 'products/new',
        name: 'admin-product-new',
        component: () => import('@/views/admin/ProductForm.vue'),
        meta: { hideNav: true },
      },
      {
        path: 'products/:id',
        name: 'admin-product-edit',
        component: () => import('@/views/admin/ProductForm.vue'),
        meta: { hideNav: true },
      },
      { path: 'offers', name: 'admin-offers', component: () => import('@/views/admin/Offers.vue') },
      {
        path: 'customers',
        name: 'admin-customers',
        component: () => import('@/views/admin/Customers.vue'),
      },
      { path: 'staff', name: 'admin-staff', component: () => import('@/views/admin/Staff.vue') },
      {
        path: 'profile',
        name: 'admin-profile',
        component: () => import('@/views/admin/Profile.vue'),
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  // No scroll on the initial load (it forces a synchronous layout); reset on later navigations.
  scrollBehavior: (_to, from) => (from === START_LOCATION ? false : { top: 0 }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.matched.some((r) => r.meta.requiresStaff) && !auth.isStaff) {
    return { name: 'admin-login', query: { next: to.fullPath } }
  }
  if (to.matched.some((r) => r.meta.requiresAuth) && !auth.isLoggedIn) {
    return { name: 'account', query: { next: to.fullPath } }
  }
  return true
})

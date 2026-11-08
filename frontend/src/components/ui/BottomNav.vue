<script setup lang="ts">
import SpiceIcon from './SpiceIcon.vue'
import type { Component } from 'vue'
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  BarChart3,
  Home,
  LayoutGrid,
  Package,
  ShoppingCart,
  Tag,
  User,
  Users,
} from 'lucide-vue-next'

interface NavItem {
  to: string
  label: string
  icon: Component
  match: (path: string) => boolean
  badge?: number
}

const props = withDefaults(
  defineProps<{ variant?: 'store' | 'admin'; cartCount?: number; ordersBadge?: number }>(),
  { variant: 'store', cartCount: 0, ordersBadge: 0 },
)
const route = useRoute()

const items = computed<NavItem[]>(() =>
  props.variant === 'store'
    ? [
        { to: '/', label: 'الرئيسية', icon: Home, match: (p) => p === '/' },
        {
          to: '/categories/spices',
          label: 'الأقسام',
          icon: LayoutGrid,
          match: (p) => p.startsWith('/categories'),
        },
        { to: '/offers', label: 'العروض', icon: Tag, match: (p) => p.startsWith('/offers') },
        {
          to: '/cart',
          label: 'السلة',
          icon: ShoppingCart,
          match: (p) => p.startsWith('/cart'),
          badge: props.cartCount,
        },
        {
          to: '/account',
          label: 'حسابي',
          icon: User,
          match: (p) => p.startsWith('/account') || p.startsWith('/orders'),
        },
      ]
    : [
        { to: '/admin', label: 'الرئيسية', icon: BarChart3, match: (p) => p === '/admin' },
        {
          to: '/admin/orders',
          label: 'الطلبات',
          icon: Package,
          match: (p) => p.startsWith('/admin/orders'),
          badge: props.ordersBadge,
        },
        {
          to: '/admin/products',
          label: 'المنتجات',
          icon: SpiceIcon,
          match: (p) => p.startsWith('/admin/products'),
        },
        {
          to: '/admin/offers',
          label: 'العروض',
          icon: Tag,
          match: (p) => p.startsWith('/admin/offers'),
        },
        {
          to: '/admin/customers',
          label: 'الزبائن',
          icon: Users,
          match: (p) => p.startsWith('/admin/customers'),
        },
      ],
)
</script>

<template>
  <nav
    aria-label="التنقل الرئيسي"
    class="pb-safe fixed inset-x-0 bottom-0 z-40 mx-auto flex max-w-app justify-around border-t border-border bg-surface px-2 pt-1.5"
    :class="variant === 'admin' ? 'sm:max-w-admin' : ''"
  >
    <RouterLink
      v-for="item in items"
      :key="item.to"
      :to="item.to"
      :aria-current="item.match(route.path) ? 'page' : undefined"
      :class="[
        'relative flex min-h-[52px] min-w-[64px] flex-col items-center justify-center gap-0.5 rounded-btn px-3 text-[12px] font-bold',
        item.match(route.path) ? 'bg-primary-soft text-link' : 'text-muted',
      ]"
    >
      <component :is="item.icon" class="h-6 w-6" aria-hidden="true" />
      <span>{{ item.label }}</span>
      <span
        v-if="item.badge"
        class="absolute end-1.5 top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-danger px-1 text-[11px] font-bold text-white"
        :aria-label="`${item.badge} في ${item.label}`"
      >
        {{ item.badge }}
      </span>
    </RouterLink>
  </nav>
</template>

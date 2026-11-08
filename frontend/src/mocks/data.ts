import type { Category, Offer, ShopSettings } from '@/types/api'

export const settings: ShopSettings = {
  shop_name: 'أبو سمرة',
  phone: '01000000000',
  whatsapp: '201000000000',
  delivery_fee: 30,
  free_delivery_threshold: 500,
  currency: 'EGP',
  is_accepting_orders: true,
}

export const categories: Category[] = [
  { id: 1, slug: 'spices', name: 'بهارات', color: '#F6D9B8', icon: 'soup', order: 1 },
  { id: 2, slug: 'herbs', name: 'أعشاب ومشروبات', color: '#DCEBCF', icon: 'leaf', order: 2 },
  { id: 3, slug: 'honey', name: 'عسل وزيوت', color: '#F9E4A8', icon: 'droplet', order: 3 },
  { id: 4, slug: 'nuts', name: 'مكسرات', color: '#EBD7C3', icon: 'nut', order: 4 },
  { id: 5, slug: 'grains', name: 'بقوليات وحبوب', color: '#F2E6C9', icon: 'wheat', order: 5 },
  { id: 6, slug: 'incense', name: 'بخور', color: '#E6DAEE', icon: 'flame', order: 6 },
]

export interface SeedVariant {
  label: string
  price: number
  compare?: number
}
export interface SeedProduct {
  slug: string
  name: string
  category: string
  description: string
  featured?: boolean
  stock?: { qty: number; low: number; unit: string }
  variants: SeedVariant[]
}

const q = 'ربع كيلو'
const h = 'نص كيلو'
const k = 'كيلو'

// 16 products (BSPEC 7). Prices are placeholders; those not in BSPEC 7 are invented for the mock.
export const seedProducts: SeedProduct[] = [
  {
    slug: 'كمون-مطحون',
    name: 'كمون مطحون',
    category: 'spices',
    description: 'كمون مطحون ناعم، ريحته قوية وطعمه أصلي. مناسب للشوربة والفول والطواجن.',
    featured: true,
    stock: { qty: 40, low: 10, unit: 'كيلو' },
    variants: [
      { label: q, price: 60 },
      { label: h, price: 115 },
      { label: k, price: 220 },
    ],
  },
  {
    slug: 'فلفل-أسود-حب',
    name: 'فلفل أسود حب',
    category: 'spices',
    description: 'فلفل أسود حب كامل، يتطحن عند الحاجة عشان يحافظ على ريحته.',
    stock: { qty: 6, low: 8, unit: 'كيلو' },
    variants: [{ label: q, price: 95, compare: 110 }],
  },
  {
    slug: 'كركم',
    name: 'كركم',
    category: 'spices',
    description: 'كركم مطحون لونه ذهبي، للأرز والشوربة والمشروبات.',
    variants: [{ label: q, price: 45 }],
  },
  {
    slug: 'قرفة-عيدان',
    name: 'قرفة عيدان',
    category: 'spices',
    description: 'قرفة عيدان سيلاني للمشروبات والحلويات.',
    variants: [{ label: q, price: 70 }],
  },
  {
    slug: 'بهارات-مشكلة',
    name: 'بهارات مشكلة',
    category: 'spices',
    description: 'خلطة بهارات مشكلة للمحشي واللحوم والفراخ.',
    variants: [{ label: q, price: 55, compare: 65 }],
  },
  {
    slug: 'ينسون',
    name: 'ينسون',
    category: 'herbs',
    description: 'ينسون بلدي، مشروب دافي بعد الأكل وقبل النوم.',
    variants: [{ label: q, price: 50 }],
  },
  {
    slug: 'كركديه',
    name: 'كركديه',
    category: 'herbs',
    description: 'كركديه صعيدي أحمر غامق، ساقع أو سخن.',
    featured: true,
    variants: [{ label: q, price: 65 }],
  },
  {
    slug: 'بابونج',
    name: 'بابونج',
    category: 'herbs',
    description: 'بابونج مجفف للتهدئة والراحة.',
    variants: [{ label: q, price: 40 }],
  },
  {
    slug: 'حبة-البركة',
    name: 'حبة البركة',
    category: 'herbs',
    description: 'حبة البركة كاملة، نضيفة ومنتقاة.',
    variants: [{ label: q, price: 55 }],
  },
  {
    slug: 'عسل-نحل-طبيعي',
    name: 'عسل نحل طبيعي',
    category: 'honey',
    description: 'عسل نحل طبيعي صافي من غير إضافات.',
    featured: true,
    stock: { qty: 12, low: 5, unit: 'كيلو' },
    variants: [{ label: k, price: 220, compare: 250 }],
  },
  {
    slug: 'زيت-زيتون',
    name: 'زيت زيتون',
    category: 'honey',
    description: 'زيت زيتون بكر ممتاز معصور على البارد.',
    variants: [{ label: 'لتر', price: 280 }],
  },
  {
    slug: 'لوز-مقشر',
    name: 'لوز مقشر',
    category: 'nuts',
    description: 'لوز مقشر طازج ومقرمش.',
    featured: true,
    variants: [{ label: q, price: 120 }],
  },
  {
    slug: 'كاجو-محمص',
    name: 'كاجو محمص',
    category: 'nuts',
    description: 'كاجو محمص وجاهز للأكل.',
    variants: [{ label: q, price: 150, compare: 170 }],
  },
  {
    slug: 'عدس-أصفر',
    name: 'عدس أصفر',
    category: 'grains',
    description: 'عدس أصفر مقشر سريع الطبخ.',
    variants: [{ label: k, price: 60 }],
  },
  {
    slug: 'فريك',
    name: 'فريك',
    category: 'grains',
    description: 'فريك بلدي للشوربة والحمام المحشي.',
    variants: [{ label: k, price: 75 }],
  },
  {
    slug: 'بخور-عود',
    name: 'بخور عود',
    category: 'incense',
    description: 'بخور عود فاخر ريحته هادية.',
    stock: { qty: 3, low: 5, unit: 'علبة' },
    variants: [{ label: 'علبة', price: 90 }],
  },
]

function nextThursdayEnd(now = new Date()): string {
  const d = new Date(now)
  const add = (4 - d.getDay() + 7) % 7 || 7
  d.setDate(d.getDate() + add)
  d.setHours(23, 59, 0, 0)
  return d.toISOString()
}

/** Offers with ids 1 (percentage), 2 (bundle), 3 (free delivery). bundle_items are filled by the db. */
export function seedOffers(now = new Date()): Offer[] {
  return [
    {
      id: 1,
      type: 'percentage',
      name: 'خصم 15% على كل البهارات',
      description: '',
      value: 15,
      target: { kind: 'category', slug: 'spices', ids: [] },
      bundle_items: [],
      bundle_price: null,
      old_price: null,
      min_order: null,
      starts_at: now.toISOString(),
      ends_at: nextThursdayEnd(now),
      is_featured: true,
    },
    {
      id: 2,
      type: 'bundle',
      name: 'باكدج الشتا',
      description: '',
      value: 0,
      target: null,
      bundle_items: [], // resolved in db.ts (ينسون + كركديه + عسل نحل)
      bundle_price: 290,
      old_price: null,
      min_order: null,
      starts_at: now.toISOString(),
      ends_at: null,
      is_featured: false,
    },
    {
      id: 3,
      type: 'free_delivery',
      name: 'توصيل مجاني',
      description: '',
      value: 0,
      target: null,
      bundle_items: [],
      bundle_price: null,
      old_price: null,
      min_order: 500,
      starts_at: now.toISOString(),
      ends_at: null,
      is_featured: false,
    },
  ]
}

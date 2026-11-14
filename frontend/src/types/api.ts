// Types for the API contract (FSPEC section 9 + BSPEC section 5). Money values are whole EGP.

export interface ShopSettings {
  shop_name: string
  phone: string
  whatsapp: string
  delivery_fee: number
  free_delivery_threshold: number
  currency: 'EGP'
  is_accepting_orders: boolean
}

export interface Category {
  id: number
  slug: string
  name: string
  color: string
  icon: string
  order: number
}

export type CategoryRef = Pick<Category, 'slug' | 'name' | 'color' | 'icon'>

export interface Variant {
  id: number
  label: string
  price: number
  old_price: number | null
  is_default: boolean
}

export interface ActiveOfferRef {
  id: number
  name: string
  type: OfferType
  value: number
}

export interface Product {
  id: number
  slug: string
  name: string
  description: string
  category: CategoryRef
  image: string | null
  is_available: boolean
  is_featured: boolean
  variants: Variant[]
  active_offer: ActiveOfferRef | null
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ProductsQuery {
  category?: string
  q?: string
  featured?: boolean
  discounted?: boolean
  page?: number
}

export type OfferType = 'percentage' | 'bundle' | 'free_delivery'

export interface OfferTarget {
  kind: 'category' | 'products' | 'all'
  slug: string | null
  ids: number[]
}

export interface BundleItem {
  variant_id: number
  name: string
  qty: number
}

export interface Offer {
  id: number
  type: OfferType
  name: string
  description: string
  value: number
  target: OfferTarget | null
  bundle_items: BundleItem[]
  bundle_price: number | null
  old_price: number | null
  min_order: number | null
  starts_at: string
  ends_at: string | null
  is_featured: boolean
}

// ---- Quote ----
export interface QuoteRequest {
  items: { variant_id: number; qty: number; note?: string }[]
  bundles: { offer_id: number; qty: number }[]
}

export interface QuoteLine {
  variant_id: number | null
  offer_id: number | null
  name: string
  unit_label: string
  qty: number
  unit_price: number
  line_total: number
}

export interface QuoteDiscount {
  offer_id: number
  label: string
  amount: number
}

export type WarningCode = 'unavailable' | 'not_found' | 'insufficient_stock' | 'offer_expired'

export interface QuoteWarning {
  variant_id: number | null
  offer_id?: number | null
  code: WarningCode
  detail: string
}

export interface Quote {
  lines: QuoteLine[]
  subtotal: number
  discounts: QuoteDiscount[]
  discount_total: number
  delivery_fee: number
  free_delivery_threshold: number
  free_delivery_remaining: number
  total: number
  warnings: QuoteWarning[]
}

// ---- Auth ----
export interface User {
  id: number
  name: string
  phone: string
  email: string
  default_address: string
  area: string
  is_staff: boolean
}

export interface AuthResponse {
  access: string
  refresh: string
  user: User
}

export interface RegisterPayload {
  name: string
  phone: string
  email?: string
}

export type ApiErrorCode = 'phone_exists' | 'not_found' | 'cart_changed' | (string & {})

export interface ApiErrorBody {
  detail?: string
  code?: ApiErrorCode
  quote?: Quote
  [field: string]: unknown
}

// ---- Orders ----
export type OrderStatus = 'new' | 'preparing' | 'out_for_delivery' | 'delivered' | 'cancelled'

export interface OrderLine {
  name: string
  unit_label: string
  qty: number
  unit_price: number
  line_total: number
  note: string
}

export interface Order {
  id: number
  number: number
  status: OrderStatus
  created_at: string
  customer: { name: string; phone: string }
  address: string
  area: string
  notes: string
  lines: OrderLine[]
  subtotal: number
  discounts: QuoteDiscount[]
  discount_total: number
  delivery_fee: number
  total: number
  payment_method: 'cod'
}

export interface CreateOrderPayload extends QuoteRequest {
  address: string
  area?: string
  notes?: string
}

// ---- Admin ----
export interface AdminOrder extends Order {
  items_summary: string
}

export type OrderCounts = Record<OrderStatus, number>

export interface LowStockItem {
  id: number
  name: string
  stock_qty: number
  stock_unit: string
}

export interface Dashboard {
  orders_today: number
  sales_today: number
  pending_count: number
  new_customers_week: number
  low_stock: LowStockItem[]
}

export interface AdminVariantInput {
  id?: number
  label: string
  price: number
  old_price?: number | null
  stock_factor?: number
  is_default?: boolean
  order?: number
}

export interface AdminVariant {
  id: number
  label: string
  price: number
  old_price: number | null
  stock_factor: number
  is_default: boolean
  order: number
}

/** Decimal DRF fields may arrive as strings ("5.000"); parse with Number(). */
export type DecimalLike = number | string | null

export interface AdminProduct {
  id: number
  slug: string
  name: string
  description: string
  image: string | null
  category: Pick<Category, 'id' | 'slug' | 'name' | 'color' | 'icon'>
  is_available: boolean
  is_featured: boolean
  stock_qty: DecimalLike
  low_stock_threshold: DecimalLike
  stock_unit: string
  variants: AdminVariant[]
  created_at: string
  updated_at: string
}

export interface AdminProductInput {
  name: string
  description?: string
  /** Category id (slug is also accepted by the API). */
  category: number | string
  is_available?: boolean
  is_featured?: boolean
  stock_qty?: number | null
  low_stock_threshold?: number | null
  stock_unit?: string
  variants: AdminVariantInput[]
  image?: File | null
}

export interface AdminOffer extends Omit<Offer, 'value'> {
  value: number | null
  is_active: boolean
  created_at: string
}

export interface AdminOfferInput {
  type: OfferType
  name: string
  description?: string
  value?: number | null
  target?: { kind: OfferTarget['kind']; slug?: string | null; ids?: number[] }
  bundle_items?: { variant_id: number; qty: number }[]
  bundle_price?: number | null
  min_order?: number | null
  starts_at?: string
  ends_at?: string | null
  is_featured?: boolean
  is_active?: boolean
}

export interface AdminStaff {
  id: number
  name: string
  phone: string
  date_joined: string
}

export interface AdminStaffInput {
  name: string
  phone: string
  password: string
}

export interface AdminCustomer {
  id: number
  name: string
  phone: string
  email: string
  default_address: string
  area: string
  date_joined: string
  orders_count: number
  total_spent: number
  last_order_at: string | null
}

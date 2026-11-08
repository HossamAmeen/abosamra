import { api } from './client'
import type { Category, Offer, Paginated, Product, ProductsQuery, ShopSettings } from '@/types/api'

export const getSettings = () => api.get<ShopSettings>('/settings/').then((r) => r.data)
export const getCategories = () => api.get<Category[]>('/categories/').then((r) => r.data)
export const getOffers = () => api.get<Offer[]>('/offers/active/').then((r) => r.data)

// Requests started at boot for the landing route (before its lazy chunk has loaded). The view's own
// first identical call takes the in-flight promise instead of issuing a second request.
const early = new Map<string, Promise<unknown>>()
const queryKey = (params: ProductsQuery) =>
  'products:' +
  JSON.stringify(
    Object.entries(params)
      .filter(([, v]) => v !== undefined && v !== '')
      .sort(),
  )
const takeEarly = <T>(key: string): Promise<T> | undefined => {
  const hit = early.get(key) as Promise<T> | undefined
  early.delete(key)
  return hit
}

const fetchProducts = (params: ProductsQuery) =>
  api.get<Paginated<Product>>('/products/', { params }).then((r) => r.data)
const fetchProduct = (slug: string) =>
  api.get<Product>(`/products/${encodeURIComponent(slug)}/`).then((r) => r.data)

export const getProducts = (params: ProductsQuery = {}) =>
  takeEarly<Paginated<Product>>(queryKey(params)) ?? fetchProducts(params)
export const getProduct = (slug: string) =>
  takeEarly<Product>('product:' + slug) ?? fetchProduct(slug)

/** Start the product requests the landing route is going to make. Unknown routes do nothing. */
export function prefetchLanding(pathname: string, search: string) {
  const start = (key: string, run: () => Promise<unknown>) => {
    const p = run()
    p.catch(() => early.delete(key)) // a failed early request is simply retried by the view
    early.set(key, p)
    setTimeout(() => early.delete(key), 15_000)
  }
  const home = pathname === '/'
  const category = /^\/categories(?:\/([^/]+))?\/?$/.exec(pathname)
  const product = /^\/products\/([^/]+)\/?$/.exec(pathname)
  if (home) {
    for (const q of [{ discounted: true }, { featured: true }] as ProductsQuery[]) {
      start(queryKey(q), () => fetchProducts(q))
    }
  } else if (category) {
    const slug = category[1] ? decodeURIComponent(category[1]) : 'all'
    const term = new URLSearchParams(search).get('q') || undefined
    const q: ProductsQuery = { category: slug === 'all' ? undefined : slug, q: term, page: 1 }
    start(queryKey(q), () => fetchProducts(q))
  } else if (product) {
    const slug = decodeURIComponent(product[1])
    start('product:' + slug, () => fetchProduct(slug))
  }
}

import { api } from './client'
import type { Quote, QuoteRequest } from '@/types/api'

export const quoteCart = (body: QuoteRequest) =>
  api.post<Quote>('/cart/quote/', body).then((r) => r.data)

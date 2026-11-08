import type { OrderStatus } from '@/types/api'

export const STATUS_LABELS: Record<OrderStatus, string> = {
  new: 'جديد',
  preparing: 'بيتجهز',
  out_for_delivery: 'في الطريق',
  delivered: 'اتسلم',
  cancelled: 'اتلغى',
}

/** Next step in the chain and the admin button label for it. */
export const NEXT_ACTION: Partial<Record<OrderStatus, { status: OrderStatus; label: string }>> = {
  new: { status: 'preparing', label: 'ابدأ التجهيز' },
  preparing: { status: 'out_for_delivery', label: 'خرج للتوصيل' },
  out_for_delivery: { status: 'delivered', label: 'اتسلم' },
}

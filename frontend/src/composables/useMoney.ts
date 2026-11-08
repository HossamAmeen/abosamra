import { formatDiscount, formatMoney } from '@/utils/money'

export function useMoney() {
  return { money: formatMoney, discount: formatDiscount }
}

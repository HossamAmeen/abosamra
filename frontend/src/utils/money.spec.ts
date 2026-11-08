import { describe, expect, it } from 'vitest'
import { formatDiscount, formatMoney, roundPounds } from './money'

describe('money', () => {
  it('formats with Western digits and ج.م', () => {
    expect(formatMoney(3450)).toBe('3,450 ج.م')
    expect(formatMoney(60)).toBe('60 ج.م')
    expect(formatMoney(0)).toBe('0 ج.م')
    expect(formatMoney('1200')).toBe('1,200 ج.م')
  })
  it('formats discounts as "- 32 ج.م"', () => {
    expect(formatDiscount(32)).toBe('- 32 ج.م')
    expect(formatDiscount(-32)).toBe('- 32 ج.م')
  })
  it('rounds half up to whole pounds', () => {
    expect(roundPounds(32.25)).toBe(32)
    expect(roundPounds(32.5)).toBe(33)
  })
})

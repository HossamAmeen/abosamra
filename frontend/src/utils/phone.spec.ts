import { describe, expect, it } from 'vitest'
import { isValidPhone, normalizePhone } from './phone'

describe('normalizePhone', () => {
  it.each([
    ['٠١٠١٢٣٤٥٦٧٨', '01012345678'],
    ['۰۱۰۱۲۳۴۵۶۷۸', '01012345678'],
    ['+201012345678', '01012345678'],
    ['00201012345678', '01012345678'],
    ['201012345678', '01012345678'],
    ['010 1234-5678', '01012345678'],
    ['(010) 12345678', '01012345678'],
  ])('%s -> %s', (raw, expected) => {
    expect(normalizePhone(raw)).toBe(expected)
  })
})

describe('isValidPhone (FSPEC 12)', () => {
  it('accepts 01012345678 and all prefixes 010/011/012/015', () => {
    for (const p of ['01012345678', '01112345678', '01212345678', '01512345678']) {
      expect(isValidPhone(p)).toBe(true)
    }
  })
  it('accepts Arabic-Indic and +20 forms', () => {
    expect(isValidPhone('٠١٠١٢٣٤٥٦٧٨')).toBe(true) // BSPEC 8 sample
    expect(isValidPhone('٠١٠١٢٣٤٥٦٧٨')).toBe(true)
    expect(isValidPhone('٠١٠١٢٣٤٥٦٧')).toBe(false)
    expect(isValidPhone('+201012345678')).toBe(true)
  })
  it('rejects 0101234567 (10 digits)', () => {
    expect(isValidPhone('0101234567')).toBe(false)
  })
  it('rejects 02xxxxxxxxx and other bad input', () => {
    expect(isValidPhone('02123456789')).toBe(false)
    expect(isValidPhone('01312345678')).toBe(false)
    expect(isValidPhone('')).toBe(false)
    expect(isValidPhone('abc')).toBe(false)
  })
})

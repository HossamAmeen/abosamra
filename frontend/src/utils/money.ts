/** `3450` -> `3,450 ج.م` (Western digits). */
const nf = new Intl.NumberFormat('en-US') // built once: `toLocaleString` re-creates the formatter per call

export function formatMoney(n: number | string): string {
  return nf.format(Number(n)) + ' ج.م'
}

/** Discount rows render as `- 32 ج.م`. */
export function formatDiscount(n: number | string): string {
  return '- ' + formatMoney(Math.abs(Number(n)))
}

/** Whole pounds, round half up. */
export function roundPounds(n: number): number {
  return Math.floor(n + 0.5)
}

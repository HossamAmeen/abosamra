export const PHONE_REGEX = /^01[0125][0-9]{8}$/
export const PHONE_HINT = 'اكتب اسمك ورقم موبايل صحيح (11 رقم يبدأ بـ 01)'
export const PHONE_ERROR = 'اكتب رقم موبايل مصري صحيح (11 رقم يبدأ بـ 01)'

const ARABIC_INDIC = '٠١٢٣٤٥٦٧٨٩'
const PERSIAN = '۰۱۲۳۴۵۶۷۸۹'

/** BSPEC 4.1: digits -> Western, strip separators, +20 / 0020 / 20 prefix -> 0. */
export function normalizePhone(raw: string): string {
  let s = (raw ?? '')
    .replace(/[٠-٩]/g, (d) => String(ARABIC_INDIC.indexOf(d)))
    .replace(/[۰-۹]/g, (d) => String(PERSIAN.indexOf(d)))
  s = s.replace(/[\s\-()]/g, '')
  if (s.startsWith('+20')) s = '0' + s.slice(3)
  else if (s.startsWith('0020')) s = '0' + s.slice(4)
  else if (s.startsWith('20') && s.length === 12) s = '0' + s.slice(2)
  return s
}

export function isValidPhone(raw: string): boolean {
  return PHONE_REGEX.test(normalizePhone(raw))
}

/** `01001234567` -> `0100 123 4567` (display only). */
export function formatPhoneDisplay(phone: string): string {
  const m = /^(\d{4})(\d{3})(\d{4})$/.exec(phone)
  return m ? `${m[1]} ${m[2]} ${m[3]}` : phone
}

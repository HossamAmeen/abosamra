import { PHONE_ERROR, PHONE_HINT, isValidPhone, normalizePhone } from '@/utils/phone'

export function usePhone() {
  return { normalize: normalizePhone, isValid: isValidPhone, hint: PHONE_HINT, error: PHONE_ERROR }
}

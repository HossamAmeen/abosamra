import { ref } from 'vue'

/** Delivery address typed on the cart; survives navigating to /account and back (SPA lifetime). */
const address = ref('')

export function useCheckoutDraft() {
  return { address }
}

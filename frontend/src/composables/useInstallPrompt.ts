import { computed, ref } from 'vue'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const VISITS_KEY = 'abosamra.visits'
const DISMISSED_KEY = 'abosamra.install-dismissed'

const deferred = ref<BeforeInstallPromptEvent | null>(null)
const visits = ref(0)
const dismissed = ref(false)
let initialised = false

function safeGet(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}
function safeSet(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    /* storage blocked */
  }
}

export const isStandalone = () =>
  typeof window !== 'undefined' &&
  (window.matchMedia?.('(display-mode: standalone)').matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true)

export const isIos = () =>
  typeof navigator !== 'undefined' && /iphone|ipad|ipod/i.test(navigator.userAgent)

/** Count one visit per browser session; capture the install event. Call once at app start. */
export function initInstallPrompt() {
  if (initialised || typeof window === 'undefined') return
  initialised = true
  let n = Number(safeGet(VISITS_KEY) ?? 0)
  try {
    if (!sessionStorage.getItem('abosamra.visit-counted')) {
      n += 1
      safeSet(VISITS_KEY, String(n))
      sessionStorage.setItem('abosamra.visit-counted', '1')
    }
  } catch {
    /* ignore */
  }
  visits.value = n
  dismissed.value = safeGet(DISMISSED_KEY) === '1'
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()
    deferred.value = e as BeforeInstallPromptEvent
  })
  window.addEventListener('appinstalled', () => {
    deferred.value = null
  })
}

export function useInstallPrompt() {
  const ios = isIos()
  /** Shown from the 2nd visit, when the browser can install (or on iOS Safari), not yet dismissed. */
  const canShow = computed(
    () =>
      visits.value >= 2 && !dismissed.value && !isStandalone() && (deferred.value !== null || ios),
  )

  async function install() {
    if (!deferred.value) return
    await deferred.value.prompt()
    await deferred.value.userChoice
    deferred.value = null
  }
  function dismiss() {
    dismissed.value = true
    safeSet(DISMISSED_KEY, '1')
  }
  return { canShow, ios, install, dismiss }
}

/** Test helper. */
export function __setInstallState(state: {
  visits?: number
  dismissed?: boolean
  event?: unknown
}) {
  if (state.visits !== undefined) visits.value = state.visits
  if (state.dismissed !== undefined) dismissed.value = state.dismissed
  if (state.event !== undefined) deferred.value = state.event as BeforeInstallPromptEvent
}

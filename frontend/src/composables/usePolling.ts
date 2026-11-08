import { onMounted, onUnmounted } from 'vue'

/** Runs `fn` now and every `ms` while the page is visible; refreshes when it becomes visible. */
export function usePolling(fn: () => unknown, ms = 30000) {
  let timer: ReturnType<typeof setInterval> | undefined

  const stop = () => {
    if (timer) clearInterval(timer)
    timer = undefined
  }
  const start = () => {
    stop()
    timer = setInterval(() => void fn(), ms)
  }
  const onVisibility = () => {
    if (document.visibilityState === 'visible') {
      void fn()
      start()
    } else {
      stop()
    }
  }

  onMounted(() => {
    void fn()
    if (document.visibilityState === 'visible') start()
    document.addEventListener('visibilitychange', onVisibility)
  })
  onUnmounted(() => {
    stop()
    document.removeEventListener('visibilitychange', onVisibility)
  })
}

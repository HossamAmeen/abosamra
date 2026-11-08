import { computed, onBeforeUnmount, ref, watch, type Ref } from 'vue'

/**
 * Renders a long list in small batches (one per macrotask) instead of one big commit, so a screen full of
 * product cards never produces a single long main-thread task. The first batch is painted immediately.
 */
export function useProgressive<T>(source: Ref<T[]>, first = 4, step = 4) {
  const shown = ref(first)
  let timer: ReturnType<typeof setTimeout> | undefined

  function tick() {
    if (shown.value >= source.value.length) return
    timer = setTimeout(() => {
      shown.value += step
      tick()
    }, 16)
  }
  watch(
    () => source.value.length,
    () => {
      clearTimeout(timer)
      tick()
    },
    { immediate: true },
  )
  onBeforeUnmount(() => clearTimeout(timer))
  return computed(() => source.value.slice(0, shown.value))
}
